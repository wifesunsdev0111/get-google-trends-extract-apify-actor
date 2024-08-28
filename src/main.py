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
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
from typing import Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        language = actor_input.get("language")
        use_proxies = actor_input.get("use_proxies")
        
        proxies = None
        if use_proxies in "yes":
            #Get Proxies from Apify
            proxy_configuration = await Actor.create_proxy_configuration()
            proxy_url = await proxy_configuration.new_url()
            proxies = {
                'http': proxy_url,
                'https': proxy_url,
            }

        #Create tls_client session using User-Agent and Cookie parameter
        def _create_tls_client(cookie: str, user_agent: str):
            #Init tls_client            
            session = tls_client.Session(
                client_identifier="chrome112",
                random_tls_extension_order=True
            )
            #init tls_client headers
            session.headers.update(
                {
                    "authority": "trends.google.com",
                    "scheme": "https",
                    "cookie": json.dumps(cookie),
                    "user-agent": user_agent,
                }
            )
            return session
        
        #Create Selenium Webdriver using proxy
        def _create_driver():
            """
                Create a WebDriver instance for web scraping.
            
                This method sets up a WebDriver instance with the specified options, including handling headless mode,
                proxy configurations, browser window size, and wait conditions.
            
                Returns:
                - tuple: A tuple containing the WebDriver instance and WebDriverWait object.
                """
            
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'user-agent={user_agent}')
            chrome_options.add_argument("--enable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure")

           
            driver = None
            wait = None

            try:
                driver = webdriver.Chrome(options=chrome_options)  # Create WebDriver without proxy settings
                driver.set_window_size(1920, 1600)  # Set browser window size
                wait = WebDriverWait(driver, 20, ignored_exceptions=[NoSuchElementException, StaleElementReferenceException])  # Set WebDriverWait object
                return (driver, wait)  # Return the WebDriver instance and WebDriverWait object
            except Exception as e:
                print(f"Booting Driver Error: {e}")  # Log any errors that occur during WebDriver setup
                return (None, None)  # Return None values if WebDriver setup fails
            
        #Get Response from https requests based on request url and request method(GET, POST)
        def _get_response_until_success(url: str, method: str):
            # Define user-agent headers
            headers = {
                "authority": "trends.google.com",
                "method": "POST",
                # "path": "/trends/api/explore?hl=en-US&tz=240&req=%7B%22comparisonItem%22:%5B%7B%22keyword%22:%22gus+walz%22,%22geo%22:%22US%22,%22time%22:%22now+1-d%22%7D%5D,%22category%22:0,%22property%22:%22%22%7D&tz=240",
                "scheme": "https",
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                # "Content-Length": "",
                "Content-Type": "application/json;charset=UTF-8",
                "Cookie": "__utmc=10102256; __utmz=10102256.1724318783.2.2.utmcsr=trends.google.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmt=1; __utma=10102256.755398533.1724314470.1724318783.1724319203.3; __utmb=10102256.6.9.1724323314805; AEC=AVYB7crw4-uqNzyvgIgFG2ITCfJYJo135J0JS04jEs_6sfAzfhzPwa5TLA; _gid=GA1.3.179090894.1724314471; OTZ=7700175_72_76_104100_72_446760; NID=516=MWYOHX7k9uhsjF9WleQwglcrBXXxfnPOQ7y3sqFCpYudnMCXTVHMD3EwJLvfOxln9oenfV5oCQGnc7dECPbFEpgr5MiKky3pCG2omacVz1t8f98pt-NjnUhF0PNdxc6Ps4nIVOnr6zQyUneZC7QHEk38t7wwgz2WTOqrZQ48H0yWW3hh2xI2F4liGo10kP1yaxkLgUjTTTtzG_OKb_oScXrn6zNNbM04CnCzz5QKamTxhKra5cL-Eo96Ngw6QEz6lZqveRtsySY2gKqI; _gat_gtag_UA_4401283=1; _ga=GA1.3.755398533.1724314470; _ga_VWZPXDNJJB=GS1.1.1724323269.3.1.1724323352.0.0.0",
                "Origin": "https://trends.google.com",
                "Priority": "u=1, i",
                # "Referer": "https://trends.google.com/trends/explore?q=gus%20walz&date=now%201-d&geo=US&hl=en-US",
                "Sec-Ch-Ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
                "Sec-Ch-Ua-Arch": '"x86"',
                "Sec-Ch-Ua-Bitness": '"64"',
                "Sec-Ch-Ua-Form-Factors": '"Desktop"',
                "Sec-Ch-Ua-Full-Version": '"127.0.6533.99"',
                "Sec-Ch-Ua-Full-Version-List": '"Not)A;Brand";v="99.0.0.0", "Google Chrome";v="127.0.6533.99", "Chromium";v="127.0.6533.99"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Model": '""',
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Ch-Ua-Platform-Version": '"10.0.0"',
                "Sec-Ch-Ua-Wow64": "?0",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                "X-Client-Data": 'CIW2yQEIpbbJAQipncoBCMPbygEIk6HLAQjvmM0BCIWgzQEI2/zNAQixns4BCP2szgEI5K/OAQiLss4BCKSyzgEIwbbOAQjat84BGKGdzgEYvK7OARidsc4B'
            }

            cookies = "__utmc=10102256; __utmz=10102256.1724318783.2.2.utmcsr=trends.google.com|utmccn=(referral)|utmcmd=referral|utmcct=/; __utmt=1; __utma=10102256.755398533.1724314470.1724318783.1724319203.3; __utmb=10102256.6.9.1724323314805; AEC=AVYB7crw4-uqNzyvgIgFG2ITCfJYJo135J0JS04jEs_6sfAzfhzPwa5TLA; _gid=GA1.3.179090894.1724314471; OTZ=7700175_72_76_104100_72_446760; NID=516=MWYOHX7k9uhsjF9WleQwglcrBXXxfnPOQ7y3sqFCpYudnMCXTVHMD3EwJLvfOxln9oenfV5oCQGnc7dECPbFEpgr5MiKky3pCG2omacVz1t8f98pt-NjnUhF0PNdxc6Ps4nIVOnr6zQyUneZC7QHEk38t7wwgz2WTOqrZQ48H0yWW3hh2xI2F4liGo10kP1yaxkLgUjTTTtzG_OKb_oScXrn6zNNbM04CnCzz5QKamTxhKra5cL-Eo96Ngw6QEz6lZqveRtsySY2gKqI; _gat_gtag_UA_4401283=1; _ga=GA1.3.755398533.1724314470; _ga_VWZPXDNJJB=GS1.1.1724323269.3.1.1724323352.0.0.0"
            
            while True:
                try:
                    response = None
                    if proxies != None:
                        if method == "get": response = requests.get(url, headers=headers, timeout=40)
                        else: response = requests.post(url, headers=headers, timeout=40)
                    else:
                        if method == "get": response = requests.get(url, headers=headers, timeout=40)
                        else: response = requests.post(url, headers=headers, timeout=40)
                    print(f'HTTPS response code: ', response.status_code)
                    if response.status_code == 404 or response.status_code == 301:   
                        return ("", response.status_code)  # Return empty content and status code for specific response codes
                    elif response.status_code < 300:
                        return (response.content, response.status_code)  # Return response content and status code for successful requests

                    # print(f'Waiting: {method, response.status_code}')  # Print a message indicating waiting
                    sleep(5)  # Adjust sleep time as needed (in seconds)
                except Exception as e:
                    print(e)  # Log any exceptions that occur during the request
                    sleep(20)  # Wait before retrying in case of exceptions

        def _decode_data(response):
            # Step 1: Decode the byte string
            decoded_data = response.decode('utf-8')
            # Step 2: Remove the initial extraneous characters
            cleaned_data = decoded_data.lstrip(")]}'\n")
            # Step 3: Parse the JSON data
            json_data = json.loads(cleaned_data)
            return json_data

        def _convert_url(payload):
            # Convert the JSON object to a string
            req_str = json.dumps(payload)
            req_str.replace(" ", "")
            # URL-encode the JSON string
            encoded_req = urllib.parse.quote(req_str)
            return encoded_req.replace("%3A", ":")

        #Google Trends Now URL        
        main_url = f'https://trends.google.com/trending?geo={geo}&hl={language}&sort={sort}&status={status}'
        print(f'Trending url: ', main_url)
        
        #Get trends data(title, search volume, started, trend status, articles, queries) from Trending Now page
        def _get_all_trending_data():
            user_agent = ""
            cookies = []
            result = []
            driver, wait = _create_driver()
            driver.get(main_url)

            #Get main browser cookie
            cookie_list = driver.get_cookies()
            cookie =  {cookie['name']: cookie['value'] for cookie in cookie_list}
            print(f'main browser COOKIE: ', cookie)

            #Get main browser user_agent
            user_agent = driver.execute_script("return navigator.userAgent;")
            print(f'main browser USER_AGENT: ', user_agent)

            #Set pagination value from 25 to 50
            page_limit_b = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@jsname='DRv89']//span[@jscontroller='QjUiqc']")))
            driver.execute_script("arguments[0].click();", page_limit_b)
            sleep(1)
            limit_b_p = driver.find_element(By.XPATH, "//ul[@aria-label='Rows per page']")
            limit_b = limit_b_p.find_elements(By.TAG_NAME, "li")
            limit_b_click = limit_b[2].find_element(By.XPATH, ".//span[contains(text(), '50')]")
            driver.execute_script("arguments[0].click();", limit_b_click)
            sleep(2)

            count = 0 #current number of trend count
            result = [] #all result
            exit_while = False
            while not exit_while:
                #Get all trends per one page
                trend_div = driver.find_element(By.XPATH, "//table[@role='grid']//tbody[@jsname='cC57zf']")
                trend_trs = trend_div.find_elements(By.TAG_NAME, "tr")
                for index, trend_tr in enumerate(trend_trs):
                    title = ""
                    search_volume = ""
                    search_volume_delta = ""
                    started = ""
                    trend_status = ""
                    articles = []
                    queries = []

                    #Extract search volume                    
                    try:
                        search_volume_1 = trend_tr.find_elements(By.TAG_NAME, "td")[2].text
                        search_v_a = search_volume_1.split("\n")
                        search_volume = search_v_a[0]
                        search_volume_delta = search_v_a[2]
                    except:
                        pass
                    
                    #Extract started and trend status
                    try:
                        started_1 = trend_tr.find_elements(By.TAG_NAME, "td")[3].text
                        started_1_a = started_1.split("\n")
                        started = started_1_a[0]
                        trend_status = started_1_a[2]
                    except:
                        pass

                    #Click selected trend to extranct articles and queries
                    driver.execute_script("arguments[0].click();", trend_tr)
                    sleep(1)

                    #Get modal body when click trend tr of table
                    modal_body = driver.find_element(By.XPATH, "//div[@jsname='dUjKgb']")
                    
                    #Extact title of trending
                    title = modal_body.find_element(By.XPATH, ".//div[1]//span[@role='heading']").text
                    print(f'==== {title} ====')

                    #Extract Explore page URL
                    detail_urls = modal_body.find_elements(By.XPATH, ".//a[@aria-label='Explore']")
                    detail_url_element = detail_urls[len(detail_urls) - 1]
                    detail_url = detail_url_element.get_attribute("href")


                    # Extract all queries of trend
                    try:
                        query_more_b = driver.find_element(By.XPATH, "//span[@jsaction='click:KoToPc']")
                        driver.execute_script("arguments[0].click();", query_more_b)
                        sleep(0.5)
                    except:
                        pass
                        
                    query_div_all = driver.find_elements(By.XPATH, "//div[@jscontroller='LkRRw']//div[1]//div[2]//div[1]//span[2]//button//span[4]")
                    
                    for query_div in query_div_all:
                        queries.append(query_div.text)
                        
                    #Extract all articles of trend
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
                            source = source_time.split(" ● ")[1]
                            article_time = source_time.split(" ● ")[0]
                        except:
                            source = ""
                            article_time = ""
                            pass
                        articles.append({"imageUrl": imageUrl, "title": article_title, "url": url, "source": source, "time": article_time})

                    #Close detail modal   
                    modal_close = modal_body.find_element(By.XPATH, ".//div[1]//div[1]//span[1]//button[1]")
                    driver.execute_script("arguments[0].click();", modal_close)
                    sleep(0.5)
                    
                    # if index == 0:
                    #     # Inject JavaScript to open the URL in a new tab when the button is clicked
                    #     driver.execute_script(f"window.open('{detail_url}', '_blank');")
                    #     window_handles = driver.window_handles
                    #     driver.switch_to.window(window_handles[1])
                        
                    #     try:
                    #         wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Related topics')]")))
                    #     except:
                    #         pass
                    #     cookie_list = driver.get_cookies()
                    #     cookie =  {cookie['name']: cookie['value'] for cookie in cookie_list}
                    #     print(f'Explore Daynamic COOKIE: ', cookie)
                    #     user_agent = driver.execute_script("return navigator.userAgent;")
                    #     print(f'Explore Dynamic USER AGENT: ', user_agent)
                    #     driver.close()
                    #     driver.switch_to.window(window_handles[0])  
                    
                    data = {
                        "title": title,
                        "search_volume": search_volume,
                        "search_volume_delta": search_volume_delta,
                        "started": started,
                        "status": trend_status,
                        "queries": queries,
                        "articles": articles,
                        "cookie": cookie,
                        "user_agent": user_agent
                    }
                    
                    result.append(data)
                    count += 1
                    print(f'End of trend {count} of {max_items}')
                    
                    #Break from current for loop when count equals max items
                    if(max_items == count):
                        exit_while = True
                        break
                #Break from current while loop when count equals max items
                if exit_while:
                    break
                
                #Get next page button and click it to proceed to the next page
                bs = driver.find_element(By.XPATH, "//button[@jsname='ViaHrd' and @aria-label='Go to next page']")
                next_b = bs
                try:
                    b_state = next_b.get_attribute("disabled")
                    print(b_state)
                    if b_state != None:
                        break
                except:
                    pass
                #Click next page button
                driver.execute_script("arguments[0].click();", next_b)
                sleep(3)        
            driver.quit()
            return result    

        #Extract all topics rising and topics top data per trend
        def _get_explore_rising_top(trend_info: dict[Any, Any]):
            cookie = trend_info['cookie']
            user_agent = trend_info['user_agent']
            explore_topics_rising = []
            explore_topics_top = []        
            
            #Make payload for https request to get topics rising and top data
            payload = {
                "comparisonItem": [
                    {
                        "keyword": trend_info['title'],
                        "geo": geo,
                        "time": "now 1-d"
                    }
                ],
                "category": 0,
                "property": ""
            }
            
            #Get entity and query info of trend from Post request
            try:
                main_req = _convert_url(payload)
                url = f'https://trends.google.com/trends/api/explore?hl={language}&tz=-60&req={main_req}&tz=-120'
                print(f'Explore data url: ', url)
                # session = _create_tls_client(cookie, user_agent)
                # while True:
                #     try:
                #         if proxies != None:
                #             response= session.post(url, proxy=proxies['http'])
                #         else:
                #             response= session.post(url)
                #         print(f'Explore data url HTTPS POST response code:', response.status_code)
                #         if response.status_code == 200:
                #             break
                #         else:
                #             sleep(10)
                #     except:
                #         pass
                response, _ = _get_response_until_success(url, "post")
                trend_data = _decode_data(response)
                entity_req = trend_data['widgets'][2]['request']
                user_type = entity_req['userConfig']['userType']
                if logger == "verbose":
                    print(f'user type is ', user_type)
                #get token for fetching topics data
                entity_token = trend_data['widgets'][2]['token']
            except:
                pass
            
            sleep(1)
            #Get entity GET URL and response data
            try:  
                entity_url_req_p = _convert_url(entity_req)
                entity_url_req = entity_url_req_p.replace("%2C", ",")
                entity_url = f'https://trends.google.com/trends/api/widgetdata/relatedsearches?hl={language}&tz=-60&req={entity_url_req_p}&token={entity_token}'
                print(f'Explore Topics:', entity_url)
                entity_res, _ = _get_response_until_success(entity_url, "get")
            except:
                pass

            #Convert entity response to JSON
            try:        
                decoded_entity_res = entity_res.decode('utf-8')
                cleaned_entity_res = decoded_entity_res.lstrip(")]}\',\n")
                entity_data= json.loads(cleaned_entity_res)
                if logger == "verbose":
                    print(f'Explore Topics Data:')
                    long_string = json.dumps(entity_data)
                    for i in range(0, len(long_string), 150):
                        print(long_string[i:i+150])
            except:
                pass
            
            #Get all topics rising id and link
            try:       
                topics_rising_all = entity_data['default']['rankedList'][1]['rankedKeyword']
                for rising in topics_rising_all:
                    rising_url_link = rising['link']
                    rising_value = rising['value']
                    rising_mid = rising['topic']['mid']
                    rising_title = rising['topic']['title']
                    rising_type = rising['topic']['type']
                    explore_topics_rising.append({"mid": rising_mid, "link": rising_url_link, "title": rising_title, "type": rising_type, "value": rising_value})
            except:
                pass
                
            #Get all topics top id and link
            try:       
                topics_top_all = entity_data['default']['rankedList'][0]['rankedKeyword']
                for top in topics_top_all:
                    top_url_link = top['link']
                    top_value = top['value']
                    top_mid = top['topic']['mid']
                    top_title = top['topic']['title']
                    top_type = top['topic']['type']
                    explore_topics_top.append({"mid": top_mid, "link": top_url_link, "title": top_title, "type": top_type, "value": top_value})
            except:
                pass

            data = {
                "title": trend_info['title'],
                "search_volume": trend_info['search_volume'],
                "search_volume_delta": trend_info['search_volume_delta'],
                "started": trend_info['started'],
                "status": trend_info['status'],
                "queries": trend_info['queries'],
                "articles": trend_info['articles'],
                "explore_topics_rising" :explore_topics_rising,
                "explore_topics_top": explore_topics_top
            }
            return data
        
        @staticmethod
        def _apply_multi_threading(inputs: list[dict[Any, Any]], callback: Callable, max_threads: int = 2):
            results = []
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                # Map each collection to the future object executing it
                future_to_post = {executor.submit(callback, input): input for input in inputs}
                
                # Iterate over the futures as they complete (in the order they complete)
                for future in as_completed(future_to_post):
                    try:
                        input = future_to_post[future]
                        # Get the result from the future
                        result = future.result()
                        results.append(result)
                    except Exception as exc:
                        results.append(None)
                        # Handle any exceptions that were raised during processing
                        print(f'Input {input} generated an exception while multi threading: {exc}')
            return results

        async def _save_actor(trends: dict[Any, Any]):
            for trend in trends:
                await Actor.push_data(trend)

        all_trending_data = _get_all_trending_data()
        if use_proxies in "yes":
            print("========== A proxy >>>>>>>>>>", proxies)
        else:
            print("========== A proxy >>>>>>>>>>", "Don't Use Proxies")
        chunk_size = 50
        subLists = [all_trending_data[i:i + chunk_size] for i in range(0, len(all_trending_data), chunk_size)]
        
        print(f'Fetching EXPLORE data from API')
        count = 0
        for trends in subLists:
            trends_data = _apply_multi_threading(trends, _get_explore_rising_top)
            print("number of trends : ", len(trends))
            await _save_actor(trends_data)
            print(f"{len(trends)} trends saved")
    