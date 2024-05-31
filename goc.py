from crawl import crawl_website



base_url = "https://immi.homeaffairs.gov.au/visas/working-in-australia/skill-occupation-list"
driver = "/usr/lib/chromium-browser/chromedriver"

crawl_website(base_url, driver)
