import logging
import click
from immi_crawler.config import settings

logger = logging.getLogger("immi_crawler")


@click.group()
def main() -> None:
    """Immigration Home Affairs Skill Occupation List Crawler CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


@main.command()
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(["json", "csv", "sqlite", "postgres"]),
    default=settings.OUTPUT_FORMAT,
    help="Target persistence format."
)
@click.option(
    "--concurrency",
    "-c",
    type=int,
    default=settings.CONCURRENCY,
    help="Max concurrent tasks."
)
@click.option(
    "--output-dir",
    "-d",
    type=click.Path(),
    default=settings.OUTPUT_DIR,
    help="Target directory for output files."
)
@click.option(
    "--sync",
    is_flag=True,
    help="Block and wait for the crawl tasks to complete."
)
def crawl(output_format: str, concurrency: int, output_dir: str, sync: bool) -> None:
    """Trigger a full crawler pipeline run across all list pages."""
    # Update settings from CLI parameters
    settings.OUTPUT_FORMAT = output_format
    settings.CONCURRENCY = concurrency
    settings.OUTPUT_DIR = output_dir

    logger.info("Initializing crawl workflow...")
    
    # Import crawler and task modules inside to avoid circular dependency
    from immi_crawler.crawler import get_total_pages_async, run_async_in_background
    from immi_crawler.tasks import get_page, complete_crawl
    from celery import chord

    try:
        # 1. Fetch total pages count
        logger.info(f"Contacting base URL: {settings.BASE_URL}")
        total_pages = run_async_in_background(
            get_total_pages_async(settings.BASE_URL, settings.PAGE_LOAD_TIMEOUT)
        )
        logger.info(f"Discovered pagination range: 0 to {total_pages - 1} ({total_pages} pages total).")
        
        # 2. Build Celery workflow
        tasks_to_run = [get_page.s(settings.BASE_URL, page_num) for page_num in range(total_pages)]
        workflow = chord(tasks_to_run)(complete_crawl.s())
        
        # 3. Dispatch workflow
        logger.info("Dispatching Celery crawl tasks (chord workflow)...")
        result = workflow.apply_async()
        logger.info(f"Workflow dispatched successfully. Parent task ID: {result.id}")
        
        if sync:
            logger.info("Blocking CLI execution. Waiting for celery workers to finish...")
            result.get(timeout=600)  # Wait up to 10 minutes
            logger.info("Crawl execution workflow finished successfully.")
        else:
            logger.info("Run 'celery -A immi_crawler.tasks.app worker' to see the tasks executed by the workers.")
            
    except Exception as e:
        logger.error(f"Crawl dispatch failed: {e}", exc_info=True)
        raise click.ClickException(str(e))


@main.command()
def test_notification() -> None:
    """Utility command to dispatch a dry-run email/Telegram notification diff."""
    import asyncio
    from immi_crawler.notifier import notify_diff
    
    logger.info("Sending dry-run notification...")
    added = [{"occupation": "Test Software Engineer", "visa_subclass": "189", "stream": "Points-tested"}]
    removed = [{"occupation": "Test Marketing Manager", "visa_subclass": "190", "stream": "State Nominated"}]
    
    try:
        asyncio.run(notify_diff(added, removed))
        logger.info("Dry-run notification dispatched.")
    except Exception as e:
        logger.error(f"Failed to dispatch dry-run notification: {e}", exc_info=True)
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()
