"""
This module defines the `main()` coroutine for the Apify Actor, executed from the `__main__.py` file.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
import re
from time import sleep
import threading
from apify import Actor


# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.


async def main() -> None:
    """
    The main coroutine is being executed using `asyncio.run()`, so do not attempt to make a normal function
    out of it, it will not work. Asynchronous execution is required for communication with Apify platform,
    and it also enhances performance in the field of web scraping significantly.
    """
    async with Actor:
        # Read the Actor input
        actor_input = await Actor.get_input() or {}
        start_urls = actor_input.get('start_urls', [{'url': 'https://apify.com'}])
        max_depth = actor_input.get('max_depth', 1)

        
        
        if not start_urls:
            Actor.log.info('No start URLs specified in actor input, exiting...')
            await Actor.exit()

        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')


        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        driver.get("https://trends.google.com/trends/trendingsearches/realtime?geo=US&hl=en-GB&category=all")



        # Get the initial page height
        try:
            while True:
                # Scroll to the bottom of the page
                trend_lists = driver.find_elements(By.XPATH, "//div[@class='generic-container-wrapper']//md-list")
                sleep(5)

                try:
                    load_more_button = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.feed-load-more-button")))
                    driver.execute_script("arguments[0].click();", load_more_button)
                except:
                    break
        except:
            trend_lists = driver.find_elements(By.XPATH, "//div[@class='generic-container-wrapper']//md-list")
            pass
                
        print(f'all trends count is ', len(trend_lists))

        result = []

        for trend in trend_lists:
            
            id=""
            title = ""
            link = ""
            queries = ""
            entity_link = []
            articles = []
            image = {}
            
            driver.execute_script("arguments[0].scrollIntoView(false); window.scrollBy(0, 0);", trend)
            
            feed_item = trend.find_element(By.TAG_NAME, "feed-item")
            id = feed_item.get_attribute("story-id")
            link = feed_item.get_attribute("share-url")
            title_o = trend.find_element(By.CSS_SELECTOR, "div[class=\"title\"]").text
            title = title_o.replace("• ", ", ")
            queries = title_o.replace(" • ", ", ").split(", ")
            entity_link.append({"id": "realtime-all", "link": "https://trends.google.com/trends/trendingsearches/realtime?geo=US&hl=en-GB&category=all"})
            
            image_link_div = trend.find_element(By.CSS_SELECTOR, "div[class=\"image-link-wrapper\"]")
            link = image_link_div.find_element(By.TAG_NAME, "a").get_attribute("href")
            thumbnail = image_link_div.find_element(By.TAG_NAME, "img").get_attribute("src")
            source = image_link_div.find_element(By.CSS_SELECTOR, "div[class=\"image-text\"]").text
            image = {"link": link, "source": source, "thumbnail": thumbnail}
            # print(image)
            
            arrow_button = trend.find_element(By.CSS_SELECTOR, "div[class=\"arrow-icon-wrapper rotate-down\"]")
            # arrow_button.click()
            driver.execute_script("arguments[0].click();", arrow_button)
            
            sleep(2)
                
            articles_list_div = trend.find_element(By.CSS_SELECTOR, "div[class=\"carousel-wrapper\"]")
            articles_list = articles_list_div.find_elements(By.TAG_NAME, "a")
            
            for article in articles_list:
                # sleep(1)
                article_link = article.get_attribute("href")
                
                parent = article.find_element(By.XPATH, "//div[@class='feed-item-carousel-item']")
                article_div = parent.find_element(By.XPATH, "//div[@class='carousel-text-wrapper with-image']")
                
                
                article_title = article_div.find_element(By.XPATH, "//div[@class='item-title']").text
                article_source_date = article_div.find_element(By.XPATH, "//div[@class='item-subtitles']").text
                article_source = article_source_date.replace(" • ", ", ").split(", ")[0]
                try:
                    article_date = article_source_date.replace(" • ", ", ").split(", ")[1]
                except:
                    article_date = ""
                    pass
                
                article_img = article.find_element(By.XPATH, "//div[@class='carousel-image-wrapper']//img").get_attribute("src")
                articles.append({"title": article_title, "link": article_link, "image": article_img, "date": article_date, "source": article_source})
                
                
            data = {
                "id": id,
                "title": title,
                "link": link,
                "queries": queries,
                "entity_link" :entity_link,
                "articles": articles,
                "image": image
                
            }
            await Actor.push_data(data)
      
        driver.quit()
                
            
            
               
            
           
        

        
