"""
This module defines the `main()` coroutine for the Apify Actor, executed from the `__main__.py` file.

Feel free to modify this file to suit your specific needs.

To build Apify Actors, utilize the Apify SDK toolkit, read more at the official documentation:
https://docs.apify.com/sdk/python
"""

from urllib.parse import urljoin
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
import re
import json
import tls_client
from time import sleep
import threading
import urllib.parse
import requests
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
        # Get geo, category and number of maximum items
        actor_input = await Actor.get_input() or {}
        geo = actor_input.get("country")
        sort = actor_input.get("sort")
        status = actor_input.get("status")
        logger = actor_input.get("logger")
        max_items = actor_input.get("max_items")

        main_url = f'https://trends.google.com/trending?geo={geo}&hl=en-GB&sort={sort}&status={status}'
        print(f'TRENDING url: ', main_url)

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={user_agent}')

        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        
                
        
        driver.get(main_url)
        try:
            page_limit_b = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[@jsname='DRv89']//span[@jscontroller='QjUiqc']")))
            driver.execute_script("arguments[0].click();", page_limit_b)
            sleep(1)
            limit_b_p = driver.find_element(By.XPATH, "//ul[@aria-label='Rows per page']")
            limit_b = limit_b_p.find_elements(By.TAG_NAME, "li")
            limit_b_click = limit_b[2].find_element(By.XPATH, "//span[contains(text(), '50')]")
            driver.execute_script("arguments[0].click();", limit_b_click)
            sleep(2)
        except:
            pass
        
        count = 0
        exit_while = False
        while not exit_while:
            #Get all trend data per page
            try:
                trend_div = driver.find_element(By.XPATH, "//table[@role='grid']//tbody[@jsname='cC57zf']")
                trend_trs = trend_div.find_elements(By.TAG_NAME, "tr")
            except:
                trend_trs =[]
                pass

            for trend_tr in trend_trs:
                title = ""
                search_volume = ""
                started = ""
                trend_status = ""
                articles = []
                explore_topics_rising = []
                explore_topics_top = []
                queries = []
                
                #Extract search Volume
                try:
                    search_volume_1 = trend_tr.find_elements(By.TAG_NAME, "td")[2].text
                    search_v_a = search_volume_1.split("\n")
                    search_volume = search_v_a[0] + " | (" + search_v_a[2] + ")"
                except:
                    pass

                #Extract started
                try:
                    started_1 = trend_tr.find_elements(By.TAG_NAME, "td")[3].text
                    started_1_a = started_1.split("\n")
                    started = started_1_a[0]
                    trend_status = started_1_a[2]
                except:
                    pass
                driver.execute_script("arguments[0].click();", trend_tr)
                sleep(1)

                try:
                    #Get Title of trending
                    modal_body = driver.find_element(By.XPATH, "//div[@jsname='dUjKgb']")
                    title = modal_body.find_element(By.XPATH, ".//div[1]//span[@role='heading']").text
                    print(f'TREND: ', title , search_volume, started)
                    #Get Explore url of trending
                    detail_urls = modal_body.find_elements(By.XPATH, ".//a[@aria-label='Explore']")
                    detail_url = detail_urls[len(detail_urls) - 1].get_attribute("href")
                    print(f'Explore detail URL: ', detail_url)

                    article_as = driver.find_elements(By.XPATH, "//div[@jsaction='click:vx9mmb;contextmenu:rbJKIe']//a")
                except:
                    pass
                # Get all queries of trending
                try:
                    query_more_b = driver.find_element(By.XPATH, "//span[@jsaction='click:KoToPc']")
                    driver.execute_script("arguments[0].click();", query_more_b)
                    sleep(0.5)
                except:
                    pass
                    
                query_div_all = driver.find_elements(By.XPATH, "//div[@jscontroller='LkRRw']//div[1]//div[2]//div[1]//span[2]//button//span[4]")
                
                for query_div in query_div_all:
                    queries.append(query_div.text)
            
                #Get all articles of trend
                article_as = driver.find_elements(By.XPATH, "//div[@jsaction='click:vx9mmb;contextmenu:rbJKIe']//a")
                for article_a in article_as:
                    try:
                        url = article_a.get_attribute("href")
                    except:
                        url = ""
                        pass
                    try:
                        imageUrl = article_a.find_element(By.TAG_NAME, "img").get_attribute("src")
                    except: 
                        imageUrl = ""
                        pass
                    try:
                        article_title  = article_a.find_element(By.XPATH, ".//div[2]//div[1]").text
                    except:
                        article_title = ""
                        pass
                    try:
                        source_time = article_a.find_element(By.XPATH, ".//div[2]//div[2]").text
                        source = source_time.split(" ● ")[0]
                        article_time = source_time.split(" ● ")[1]
                    except:
                        source = ""
                        article_time = ""
                        pass
                    articles.append({"imageUrl": imageUrl, "title": article_title, "url": url, "source": source, "time": article_time}) 
                
                #Close detail modal
                modal_close = modal_body.find_element(By.XPATH, ".//div[1]//div[1]//span[1]//button[1]")
                driver.execute_script("arguments[0].click();", modal_close)
                sleep(0.5)  
                
                #Open trends explore page on new tab
                # Inject JavaScript to open the URL in a new tab when the button is clicked
                driver.execute_script(f"window.open('{detail_url}', '_blank');")
                window_handles = driver.window_handles
                driver.switch_to.window(window_handles[1])
                
                try:
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Related topics')]")))
                except:
                    pass
                
                #Get Topics content body on explore page
                try:
                    md_content = driver.find_element(By.XPATH, "//md-content[@ng-if='ctrl.widgets.length && !ctrl.isQuerying']")
                    entity_content_p = md_content.find_elements(By.XPATH, ".//div[@flex='50']")[0]
                except:
                    pass
                
                #Get All Topics Rising data
                while True:
                    try:
                        all_topics_rising = entity_content_p.find_elements(By.XPATH, ".//trends-widget[1]//ng-include[1]//widget[1]//div[1]//div[1]//ng-include[1]//ng-include[@ng-if='item.value.link']//a[1]")
                    except:
                        all_topics_rising = []
                        break
                    
                    for topics_rising in all_topics_rising:
                        rising_title_type = topics_rising.find_element(By.XPATH, ".//span[@ng-bind='bidiText']").text.split(" - ", 1)
                        if len(rising_title_type) == 2:
                            rising_title, rising_type = rising_title_type
                        else:
                            rising_title = rising_title_type[0]
                            rising_type = ""
                        
                        rising_link = topics_rising.get_attribute("href")
                        pattern = r"/(m|g)/\w+"
                        match = re.search(pattern, rising_link)
                        if match:
                            rising_mid = match.group()
                        else:
                            print("No match found.")
                        explore_topics_rising.append({"mid": rising_mid, "link": rising_link, "title": rising_title, "type": rising_type})
                    
                    try:
                        next_entity_button = entity_content_p.find_element(By.XPATH, ".//div[@ng-if='ctrl.bullets.length && ctrl.shouldShowItemsListView()']//button[@ng-click='ctrl.updateToNextPage()']")
                    except:
                        break
                    
                    try:
                        next_entity_button_state = next_entity_button.get_attribute("disabled")
                        if next_entity_button_state != None:
                            break
                        driver.execute_script("arguments[0].click();", next_entity_button)
                        sleep(1)
                        continue
                    except:
                        pass
                
                print(f'Explore topics RISING count: ' , len(explore_topics_rising))    
                
                #Switch Topics Top Mode
                try:
                    topics_rising_head = entity_content_p.find_element(By.XPATH, ".//trends-widget[1]//ng-include[1]//widget[1]//div[1]//div[1]//div[1]//ng-include[1]//div[contains(text(), 'Rising')]")
                    driver.execute_script("arguments[0].scrollIntoView();", topics_rising_head)
                    sleep(0.5)
                    topics_top_options = driver.find_elements(By.XPATH, ".//md-option[@jslog='41826; track:generic_click']")
                    for topics_top_option in topics_top_options:
                        driver.execute_script("arguments[0].click();", topics_top_option)
                        sleep(0.5)
                except:
                    pass

                #Get all explore topics top data
                while True:
                    try:
                        all_topics_top = entity_content_p.find_elements(By.XPATH, ".//trends-widget[1]//ng-include[1]//widget[1]//div[1]//div[1]//ng-include[1]//ng-include[@ng-if='item.value.link']//a[1]")
                    except:
                        all_topics_top = []
                        break

                    for topics_top in all_topics_top:
                        top_title_type = topics_top.find_element(By.XPATH, ".//span[@ng-bind='bidiText']").text.split(" - ", 1)
                        if len(top_title_type) == 2:
                            top_title, top_type = top_title_type
                        else:
                            top_title = top_title_type[0]
                            top_type = ""
                        top_link = topics_top.get_attribute("href")
                        pattern = r"/(m|g)/\w+"
                        match = re.search(pattern, top_link)
                        if match:
                            top_mid = match.group()
                        else:
                            print("No match found.")
                        explore_topics_top.append({"mid": top_mid, "link": top_link, "title": top_title, "type": top_type})
                            
                    try:
                        next_entity_button = entity_content_p.find_element(By.XPATH, ".//div[@ng-if='ctrl.bullets.length && ctrl.shouldShowItemsListView()']//button[@ng-click='ctrl.updateToNextPage()']")
                    except:
                        break
                    
                    try:
                        next_entity_button_state = next_entity_button.get_attribute("disabled")
                        if next_entity_button_state != None:
                            break
                        driver.execute_script("arguments[0].click();", next_entity_button)
                        sleep(1)
                        continue
                    except:
                        pass
                    
                print(f'Explore topics TOP count: ' , len(explore_topics_top))  
               
                driver.close()
                driver.switch_to.window(window_handles[0])
                
                data = {
                "title": title,
                "search_volume": search_volume,
                "started": started,
                "status": trend_status,
                "queries": queries,
                "articles": articles,
                "explore_topics_rising" :explore_topics_rising,
                "explore_topics_top": explore_topics_top
                }
                #Save trend data
                await Actor.push_data(data)

                count += 1
                print(f'End of item {count} of {max_items}')
                print(f'==========')
            
                if(max_items == count):
                    exit_while = True
                    break
            
            if exit_while:
                break

            next_b =  driver.find_element(By.XPATH, "//button[@jsname='ViaHrd' and @aria-label='Go to next page']")
            try:
                b_state = next_b.get_attribute("disabled")
                print(f'next button state is ', b_state)
                if b_state != None:
                    exit_while = True
                    break
            except:
                pass
            
            driver.execute_script("arguments[0].click();", next_b)
      
        driver.quit()
                
            
            
               
            
           
        

        
