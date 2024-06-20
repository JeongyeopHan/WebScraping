import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from datetime import datetime

class WebspiderSpider(scrapy.Spider):
    name = "webspider"
    volunteer_id = "2153"
    location = "korea"

    def start_requests(self):
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.driver.get('https://statutes.capitol.texas.gov/Index.aspx')

        self.parse()

    def parse(self):
        driver = self.driver

        # Select Finance Code from the first dropdown
        code_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_QSearch_cboQuickCode'))
        )
        code_dropdown.send_keys('Finance Code')

        # Get all chapter options from the second dropdown
        chapter_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_QSearch_cboQuickChapter'))
        )
        chapters = chapter_dropdown.find_elements(By.TAG_NAME, 'option')

        for chapter in chapters:
            chapter_value = chapter.get_attribute('value')
            chapter_text = chapter.text
            if chapter_value and chapter_value != "00":  # Ignore the default/empty option
                chapter_dropdown.send_keys(chapter_text)

                # Click the Go button
                go_button = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_QSearch_btnQSGo')
                go_button.click()

                # Wait for the new page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.legText'))
                )

                # Scrape the new page
                response = HtmlResponse(url=driver.current_url, body=driver.page_source, encoding='utf-8')
                soup = Selector(response)
                sections = soup.css('p.left')

                for section in sections:
                    section_text = section.css('::text').get()
                    section_number = section_text.split(' ')[1].strip('.')

                    yield {
                        "text": section_text,
                        "metadata": {
                            "date downloaded": datetime.now().strftime("%Y-%m-%d"),
                            "site url": driver.current_url,
                            "extra data": {
                                "chapter": chapter_text,
                                "section": section_number
                            }
                        },
                        "volunteer id": self.volunteer_id,
                        "location": self.location
                    }

                driver.back()  # Go back to the main page
                code_dropdown = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_QSearch_cboQuickCode'))
                )
                code_dropdown.send_keys('Finance Code')
                chapter_dropdown = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_QSearch_cboQuickChapter'))
                )
                chapter_dropdown.send_keys(chapter_text)

    def closed(self, reason):
        self.driver.quit()
