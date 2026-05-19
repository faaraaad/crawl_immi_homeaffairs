import asyncio
import csv
import json
import logging
import os
from datetime import datetime
from celery import Celery, Task
import aiosqlite

from immi_crawler.config import settings
from immi_crawler.db import AsyncSessionLocal
from immi_crawler.models import OccupationVisa
from immi_crawler.parser import get_occupation_and_visa
from immi_crawler.crawler import scrape_page_async, get_redis_client, run_async_in_background
from immi_crawler.exceptions import WebDriverException, TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

# Initialize Celery App
app = Celery(
    "immi_crawler",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["immi_crawler.tasks"]
)

# Standard celery configuration settings
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@app.task(  # type: ignore[untyped-decorator]
    bind=True,
    autoretry_for=(WebDriverException, TimeoutException, NoSuchElementException),
    max_retries=3,
    retry_backoff=True,
    retry_jitter=False
)
def get_page(self: Task, base_url: str, ct: int) -> list[dict[str, str]]:
    """Celery task to crawl and parse a single page of the occupations list.
    
    Args:
        base_url: The URL to load.
        ct: Page index to scrape.
        
    Returns:
        List of parsed occupation-visa dictionaries.
    """
    logger.info(f"Task get_page started for page {ct}")
    
    # Check if page was already crawled during resume logic
    r = get_redis_client()
    if r.sismember("crawled_pages", str(ct)):
        logger.info(f"Page {ct} already crawled (found in Redis resume set). Skipping fetch.")
        # Retrieve already scraped page contents from Redis cache or just return empty list
        # since we want to avoid re-scraping but also avoid double saving
        return []
        
    # Execute Playwright async crawl in the background loop
    try:
        html = run_async_in_background(
            scrape_page_async(base_url, ct, settings.PAGE_LOAD_TIMEOUT)
        )
        
        # Parse items from HTML
        items: list[dict[str, str]] = get_occupation_and_visa(html)
        logger.info(f"Page {ct} crawled. Extracted {len(items)} items.")
        
        # Record success in Redis crawled pages set to support resume
        r.sadd("crawled_pages", str(ct))
        return items
        
    except Exception as e:
        logger.error(f"Error crawling page {ct}: {e}", exc_info=True)
        raise e


@app.task  # type: ignore[untyped-decorator]
def save_occupation_visa(occupation: str, visa_subclass: str, stream: str) -> None:
    """Drop-in Celery task replacing write_to_file to save a single item to PostgreSQL."""
    async def _save() -> None:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                item = OccupationVisa(
                    occupation=occupation,
                    visa_subclass=visa_subclass,
                    stream=stream
                )
                session.add(item)
                
    logger.debug(f"Saving single record: {occupation} - {visa_subclass}")
    try:
        asyncio.run(_save())
    except Exception as e:
        logger.error(f"Failed to save single occupation-visa: {e}", exc_info=True)
        raise e


@app.task  # type: ignore[untyped-decorator]
def complete_crawl(results: list[list[dict[str, str]]]) -> None:
    """Chord callback task executing post-crawl processing, saving to selected storage format,
    performing change detection, and launching SMTP/Telegram alerts.
    """
    # Flatten parallel page results
    flat_results = []
    for page_items in results:
        if page_items:
            flat_results.extend(page_items)
            
    logger.info(f"Crawl completed. Collected a total of {len(flat_results)} records.")
    if not flat_results:
        logger.warning("No records found in this crawl. Skipping persistence and diff.")
        return
        
    now = datetime.utcnow()
    now_str = now.isoformat()
    output_format = settings.OUTPUT_FORMAT.lower()
    
    # --- 1. Persist data according to selected output format ---
    
    if output_format == "postgres":
        async def _save_postgres() -> None:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    db_items = [
                        OccupationVisa(
                            occupation=item["occupation"],
                            visa_subclass=item["visa_subclass"],
                            stream=item["stream"],
                            scraped_at=now
                        )
                        for item in flat_results
                    ]
                    session.add_all(db_items)
            logger.info("Saved data to PostgreSQL database via SQLAlchemy async ORM.")
            
        asyncio.run(_save_postgres())
        
    elif output_format == "sqlite":
        async def _save_sqlite() -> None:
            db_path = os.path.join(settings.OUTPUT_DIR, "immi_crawler.db")
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS occupation_visas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        occupation TEXT,
                        visa_subclass TEXT,
                        stream TEXT,
                        scraped_at TEXT
                    )
                """)
                rows = [
                    (item["occupation"], item["visa_subclass"], item["stream"], now_str)
                    for item in flat_results
                ]
                await conn.executemany(
                    "INSERT INTO occupation_visas (occupation, visa_subclass, stream, scraped_at) VALUES (?, ?, ?, ?)",
                    rows
                )
                await conn.commit()
            logger.info(f"Saved data to SQLite database via aiosqlite at {db_path}")
            
        asyncio.run(_save_sqlite())
        
    elif output_format == "csv":
        csv_path = os.path.join(settings.OUTPUT_DIR, "occupations.csv")
        try:
            with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["occupation", "visa_subclass", "stream", "scraped_at"])
                writer.writeheader()
                for item in flat_results:
                    writer.writerow({
                        "occupation": item["occupation"],
                        "visa_subclass": item["visa_subclass"],
                        "stream": item["stream"],
                        "scraped_at": now_str
                    })
            logger.info(f"Saved data to CSV at {csv_path}")
        except Exception as e:
            logger.error(f"Failed to write CSV: {e}", exc_info=True)
            
    elif output_format == "json":
        json_filename = f"crawl_run_{now.strftime('%Y%m%d_%H%M%S')}.json"
        json_path = os.path.join(settings.OUTPUT_DIR, json_filename)
        try:
            metadata = {
                "scraped_at": now_str,
                "total_records": len(flat_results),
                "output_format": output_format
            }
            payload = {
                "metadata": metadata,
                "data": flat_results
            }
            with open(json_path, mode="w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
            logger.info(f"Saved data to JSON at {json_path}")
        except Exception as e:
            logger.error(f"Failed to write JSON: {e}", exc_info=True)
            
    # --- 2. Change Detection & Alerting ---
    
    r = get_redis_client()
    prev_snapshot_str = r.get("previous_crawl_snapshot")
    prev_snapshot = []
    
    if prev_snapshot_str:
        try:
            prev_snapshot = json.loads(prev_snapshot_str)
        except json.JSONDecodeError:
            logger.error("Failed to decode previous Redis crawl snapshot. Re-initializing.")
            
    # Compare datasets using tuples of (occupation, subclass, stream)
    current_set = {(item["occupation"], item["visa_subclass"], item["stream"]) for item in flat_results}
    prev_set = {(item["occupation"], item["visa_subclass"], item["stream"]) for item in prev_snapshot}
    
    added_tuples = current_set - prev_set
    removed_tuples = prev_set - current_set
    
    added_list = [{"occupation": o, "visa_subclass": v, "stream": s} for o, v, s in added_tuples]
    removed_list = [{"occupation": o, "visa_subclass": v, "stream": s} for o, v, s in removed_tuples]
    
    if added_list or removed_list:
        logger.warning(f"🚨 List Change Detected! Added: {len(added_list)}, Removed: {len(removed_list)}")
        print(f"DIFFERENCE DETECTED: Added {len(added_list)}, Removed {len(removed_list)}")
        
        # Dispatch notifications asynchronously
        from immi_crawler.notifier import notify_diff
        async def _notify() -> None:
            await notify_diff(added_list, removed_list)
        asyncio.run(_notify())
    else:
        logger.info("No modifications detected in the occupation list comparison.")
        
    # Overwrite the Redis snapshot for the next comparison
    r.set("previous_crawl_snapshot", json.dumps(flat_results))
    
    # Successful run: reset the resume tracking set so next run does not skip anything
    r.delete("crawled_pages")
    logger.info("Crawl state cleared in Redis. Ready for next full run.")
