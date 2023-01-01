import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from tasks import app, write_to_file


def legal_pages():
    ct = 0
    while True:
        yield 4 + ct*2
        ct += 1


def get_driver(url, driver_addr):
    driver = webdriver.Chrome(service=ChromeService(executable_path=driver_addr))
    driver.get(url)
    return driver


@app.task
def get_page(driver_addr, base_url, ct):
    driver = get_driver(base_url, driver_addr)
    for page in legal_pages():
        if ct > page:
            driver.find_element(By.CLASS_NAME, "pagination").find_elements(By.TAG_NAME, "li")[
                page].find_element(
                By.TAG_NAME, "a").click()
            driver.implicitly_wait(3)
            time.sleep(2)
        else:
            driver.find_element(By.CLASS_NAME, "pagination").find_elements(By.TAG_NAME, "li")[
                ct].find_element(
                By.TAG_NAME, "a").click()
            driver.implicitly_wait(3)
            time.sleep(2)
            break
    print(f"Crawling Page {ct}")
    html = driver.page_source
    driver.quit()
    get_occupation_and_visa(html)


def get_occupation_and_visa(html):
    soup = BeautifulSoup(html, 'html.parser')

    trs = soup.find_all(
        "tr", attrs={
            'tabindex': '-1',
            'aria-expanded': 'false'
        })

    trs = soup.find_all("tr", attrs={'tabindex': '-1', 'aria-expanded': 'false'})
    for tr in trs:
        occupation = tr.find_all("td")[0].get_text()
        for li in tr.find_all("td")[2].find_all("li"):
            try:
                file_name = li.get_text()[:3]
                int(file_name)
                if file_name == "482":
                    if "Medium Term Stream" in li.get_text():
                        write_to_file.apply_async(args=(file_name + " - " + "Medium Term Stream", occupation))
                    else:
                        write_to_file.apply_async(args=(file_name + " - " + "Short Term Stream", occupation))
                else:
                    write_to_file.apply_async(args=(file_name + " - " + "State or Territory nominated", occupation))
            except ValueError:
                pass


def crawl_website(base_url, driver_addr):
    ct = 0
    try:
        driver = get_driver(base_url, driver_addr)
        number_of_page = len(
            driver.find_element(
                By.CLASS_NAME, "pagination").find_elements(By.TAG_NAME, "li"))
        while True and ct < number_of_page:
            get_page.apply_async(args=(driver_addr, base_url, ct))
            ct += 1
    except Exception as e:
        print(f"Crawling Finish on Page {ct}")
        raise e
