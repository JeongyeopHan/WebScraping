import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from scrapy.utils.project import get_project_settings
from datetime import datetime
from selenium.common.exceptions import TimeoutException

class WebspiderSpider(scrapy.Spider):
    name = "webspider"
    volunteer_id = "2153"
    location = "Korea"
    start_urls = ['https://statutes.capitol.texas.gov/Index.aspx']

    def __init__(self, *args, **kwargs):
        super(WebspiderSpider, self).__init__(*args, **kwargs)
        service = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.driver.implicitly_wait(10)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        self.driver.get(response.url)

        # Use Select class to interact with the dropdowns
        select_code = Select(WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_QSearch_cboQuickCode'))
        ))
        select_code.select_by_visible_text('Finance Code')

        select_chapter = Select(WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_QSearch_cboQuickChapter'))
        ))

        if len(select_chapter.options) > 2:
            second_chapter_text = select_chapter.options[2].text
            select_chapter.select_by_visible_text(second_chapter_text)

            go_button = self.driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_QSearch_btnQSGo')
            ActionChains(self.driver).click(go_button).perform()

            WebDriverWait(self.driver, 20).until(EC.new_window_is_opened(self.driver.window_handles))
            new_tab_handle = self.driver.window_handles[-1]
            self.driver.switch_to.window(new_tab_handle)

            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, 'pre'))
            )

            self.process_page_content(second_chapter_text)

    def process_page_content(self, chapter_text):
        response = HtmlResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8')
        soup = Selector(response)
        sections = soup.css('p.left')

        for section in sections:
            section_text = section.css('::text').get()
            if section_text:
                section_number = section_text.split(' ')[1].strip('.') if ' ' in section_text else ''
                item = {
                    "text": section_text,
                    "metadata": {
                        "date downloaded": datetime.now().strftime("%Y-%m-%d"),
                        "site url": self.driver.current_url,
                        "extra data": {
                            "chapter": chapter_text,
                            "section": section_number
                        }
                    },
                    "volunteer id": self.volunteer_id,
                    "location": self.location
                }
                yield item

    def closed(self, reason):
        self.driver.quit()
