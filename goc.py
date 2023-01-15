from crawl import crawl_website
import os


base_url = "https://immi.homeaffairs.gov.au/visas/working-in-australia/skill-occupation-list"
driver = os.environ.get("chromedriver_addr", "/usr/lib/chromium-browser/chromedriver")

crawl_website(base_url, driver)
