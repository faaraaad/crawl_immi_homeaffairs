import asyncio
import logging
import threading
from typing import Generator, Optional, Any, Coroutine, TypeVar
import redis
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

from immi_crawler.config import settings
from immi_crawler.exceptions import WebDriverException, TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

# Global singletons for background thread playwright instances
_loop: Optional[asyncio.AbstractEventLoop] = None
_thread: Optional[threading.Thread] = None
_playwright: Optional[Playwright] = None
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_lock = threading.Lock()


def get_redis_client() -> "redis.Redis[str]":
    """Create and return a configured Redis client."""
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def start_background_loop() -> None:
    """Start a persistent background asyncio event loop running in a daemon thread."""
    global _loop, _thread
    with _lock:
        if _loop is not None:
            return
        
        _loop = asyncio.new_event_loop()
        _thread = threading.Thread(target=_loop.run_forever, name="PlaywrightThread", daemon=True)
        _thread.start()
        logger.info("Persistent background event loop started.")


async def _init_playwright() -> None:
    """Initialize Playwright and launch a single persistent browser context in the async loop."""
    global _playwright, _browser, _context
    logger.info("Initializing Playwright and Chromium...")
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=True)
    _context = await _browser.new_context()
    logger.info("Playwright persistent browser context established.")


def get_browser_context() -> BrowserContext:
    """Get or initialize the shared persistent Playwright BrowserContext."""
    global _context
    if _context is None:
        start_background_loop()
        assert _loop is not None
        # Dispatch the init coroutine to the background thread and block until ready
        future = asyncio.run_coroutine_threadsafe(_init_playwright(), _loop)
        future.result()  # Wait for completion
    assert _context is not None
    return _context


def legal_pages() -> Generator[int, None, None]:
    """Generate pagination element click indices based on the original formula."""
    ct = 0
    while True:
        yield 4 + ct * 2
        ct += 1


async def scrape_page_async(base_url: str, ct: int, timeout_ms: int) -> str:
    """Perform async browser crawling for page index `ct` using the shared context.
    
    Args:
        base_url: Target base URL.
        ct: Page index to crawl (0-indexed).
        timeout_ms: Locator timeout in milliseconds.
        
    Returns:
        The page's HTML source after table rows are loaded.
    """
    context = get_browser_context()
    page = await context.new_page()
    page.set_default_timeout(timeout_ms)

    try:
        logger.info(f"Navigating to {base_url} for page {ct}")
        await page.goto(base_url, wait_until="domcontentloaded")
        
        # Select all pagination items
        pagination_items = page.locator(".pagination li")
        
        # Perform sequential pagination to reach target page `ct` if ct > 0
        if ct > 0:
            for page_idx in legal_pages():
                await pagination_items.first.wait_for(state="attached", timeout=timeout_ms)
                if ct > page_idx:
                    logger.debug(f"Clicking shift-pagination button index {page_idx}")
                    await pagination_items.nth(page_idx).locator("a").click()
                    # Wait for page update using presence of elements in table
                    await page.locator('tr[tabindex="-1"][aria-expanded="false"]').first.wait_for(
                        state="attached", timeout=timeout_ms
                    )
                else:
                    logger.debug(f"Clicking final target page button index {ct}")
                    await pagination_items.nth(ct).locator("a").click()
                    await page.locator('tr[tabindex="-1"][aria-expanded="false"]').first.wait_for(
                        state="attached", timeout=timeout_ms
                    )
                    break
        else:
            # Page 0 (initial view): Wait for table rows to be present
            await page.locator('tr[tabindex="-1"][aria-expanded="false"]').first.wait_for(
                state="attached", timeout=timeout_ms
            )

        logger.info(f"Successfully loaded and reached page {ct}")
        html = await page.content()
        return html

    except PlaywrightTimeoutError as e:
        logger.error(f"Playwright timeout error while loading page {ct}: {e}")
        raise TimeoutException(f"Playwright timed out on page {ct}: {e}") from e
    except PlaywrightError as e:
        logger.error(f"Playwright generic error on page {ct}: {e}")
        if "Target closed" in str(e) or "Navigation failed" in str(e):
            raise WebDriverException(f"Playwright browser failure: {e}") from e
        else:
            raise NoSuchElementException(f"Playwright locator/element missing: {e}") from e
    finally:
        await page.close()


async def get_total_pages_async(base_url: str, timeout_ms: int) -> int:
    """Fetch base page and retrieve the count of pagination items."""
    context = get_browser_context()
    page = await context.new_page()
    page.set_default_timeout(timeout_ms)
    
    try:
        await page.goto(base_url, wait_until="domcontentloaded")
        pagination_items = page.locator(".pagination li")
        await pagination_items.first.wait_for(state="attached", timeout=timeout_ms)
        count = await pagination_items.count()
        return count
    except PlaywrightTimeoutError as e:
        raise TimeoutException(f"Timeout checking pagination on base page: {e}") from e
    except PlaywrightError as e:
        raise WebDriverException(f"Error checking pagination: {e}") from e
    finally:
        await page.close()


T = TypeVar('T')


def run_async_in_background(coro: Coroutine[Any, Any, T]) -> T:
    """Utility to run a coroutine in our persistent background thread and return result."""
    start_background_loop()
    assert _loop is not None
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()
