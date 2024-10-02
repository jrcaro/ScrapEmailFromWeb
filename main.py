from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import re
from concurrent.futures import ProcessPoolExecutor, wait, TimeoutError, as_completed
from multiprocessing import freeze_support
import os
from tqdm import tqdm
from datetime import datetime
import logging
import sys
import requests

# Constants
with open('cred.txt', 'r') as f:
    API_KEY = f.readline()
DEBUG = False
SEARCH_ENGINE_ID = '95f8e9404c82049dc'
SLEEP_TIME = 3
SEPARATOR = ";"
MAX_SEARCH = 90
NAME_FILE = './/resultado.csv'
# Regex pattern
PATTERN = re.compile(r"[\w]+[.]?[-]?[\w]+@[\w]+[.]?[-]?[\w]+\.[\w]{2,6}")
# Words to filter URLs
with open('filter.txt', 'r') as f:
    FILTER_WORDS_ = f.readlines()

FILTER_WORDS = list(map(lambda x: x.replace('\n', ''), FILTER_WORDS_))

def get_driver(debug):
    # The log disable with the option headless=new is not working
    logging.getLogger('selenium').setLevel(logging.ERROR)

    service = Service(
        service_log_path=os.devnull
    )

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=1")

    if not debug:
        chrome_options.add_argument("--headless=new")

    return webdriver.Chrome(service=service, options=chrome_options)

def build_payload(query, start=1, num=10, **params):
    payload = {
        'key': API_KEY,
        'q': query,
        'cx': SEARCH_ENGINE_ID,
        'start': start,
        'num': num,
        'excludeTerms': ' '.join(FILTER_WORDS)
    }

    payload.update(params)
    return payload

def make_request(payload):
    res = requests.get('https://www.googleapis.com/customsearch/v1/', params=payload)

    if res.status_code != 200:
        raise Exception('Request failed')
    
    return [url['link'] for url in res.json()['items']]

def write_file(data, filename):
    with open(filename, 'a') as f:
        try:
            f.write(data)
        except Exception as e:
            return e

def scrape_web(url, debug = False, query = 'debug'):
    # Get driver and sleep for full page load
    driver = get_driver(debug)
    driver.get(url)
    time.sleep(SLEEP_TIME)
    email = ''
    date = datetime.now()

    # Seach for contact page and navigate to it
    try:
        conctact_link = driver.find_element(By.PARTIAL_LINK_TEXT, "ontact")
        driver.get(conctact_link.get_attribute("href"))
    except NoSuchElementException:
        try:
            conctact_link = driver.find_element(By.PARTIAL_LINK_TEXT, "ONTACT")
            driver.get(conctact_link.get_attribute("href"))
        except NoSuchElementException:
            try:
                conctact_link = driver.find_element(By.XPATH,
                                                    ".//div[contains(@class, 'navbar')]//a[contains(@href,'ontact')]")
                driver.get(conctact_link.get_attribute("href"))
            except:
                email = 'Comprobar'
    
    if not email:
        time.sleep(SLEEP_TIME)
        # Search email in the page with mailto ready email or plain text with regex
        try:        
            elem = driver.find_element(By.XPATH, ".//a[contains(@href,'mailto:')]")
            email = elem.get_attribute("href").strip().lower()[7:].split('?')[0].replace('%20', '')
        except NoSuchElementException as e:
            source = driver.page_source
            email_reg = PATTERN.finditer(source)
            try:
                email = email_reg.__next__().group().replace('%20', '')
            except Exception:
                email= 'Comprobar'
        finally:
            driver.close()
        
        if DEBUG:
            print('{} -> {}'.format(url, email))
        write_file('{}{}{}{}{}{}{}\n'.format(query, SEPARATOR, 
                                     date, SEPARATOR, 
                                     url, SEPARATOR, 
                                     email.lower()), NAME_FILE)

def load_url(query, result_total=MAX_SEARCH):
    items =[]
    reminder = result_total % 10

    if reminder > 0:
        pages = (result_total // 10) + 1
    else:
        pages = result_total // 10

    for i in tqdm(range(pages)):
        if pages == i + 1 and reminder > 0:
            payload = build_payload(query, start=(i+1)*10, num=reminder)
        else:
            payload = build_payload(query, start=(i+1)*10)

        try:
            res = make_request(payload)
            items.extend(res)
        except Exception as e:
            print('No existen más páginas. Tiramos con las que hay.')
            continue

    return items

if __name__ == "__main__":

    # Enable multiprocessing in exe for Windows
    freeze_support()

    # Create the outpur file and the header if not exist. If exist, read the URLs
    # and sum the list to the filter words list to not duplicates
    if os.path.exists(NAME_FILE):
        with open(NAME_FILE, 'r+') as f:
            res_urls = [x.split(SEPARATOR)[2] for x in f.readlines()]

        filter_list = FILTER_WORDS + res_urls
    else:
        write_file('Busqueda{}Fecha{}Pagina{}Email\n'.format(SEPARATOR, 
                                                             SEPARATOR, SEPARATOR), NAME_FILE)
        filter_list = FILTER_WORDS

    # Query to search in Google
    query = input('Que quieres buscar, payaso? ')
    #query = 'estudios arquitectura cordoba'

    try:
        # Google search and apply filters
        print('Buscando en Google...')
        search_raw = load_url(query)
        search_filter = [i for i in search_raw if not any(i for j in filter_list if str(j) in i)]
        urls_list = set(search_filter)
    except Exception as e:
        print(e)
        input('Ha habido un error. Pulsa alguna tecla para salir.')
        sys.exit()

    # Progress bar
    LENGTH = len(urls_list)
    pbar = tqdm(total=LENGTH,
                desc='Lo que te queda por esperar. Cada email 5$',
                colour='GREEN')

    # If debug flag is active, process the information one by one
    if DEBUG:
        for url in urls_list:
            try:
                scrape_web(url, DEBUG)
                pbar.update(n=1)
            except Exception as e:
                print(e)
                continue
    else:    
        # list to store the processes
        processList = []

        # initialize the mutiprocess interface
        with ProcessPoolExecutor() as executor:
            for url in urls_list:
                try:
                    processList.append(executor.submit(scrape_web, url, query=query))
                except TimeoutError as e:
                    print(e)
                    for pid, process in executor._processes.items():
                        process.terminate()
                    executor.shutdown()
                except Exception as e:
                    print(e)
                    continue

            for _ in as_completed(processList):
                pbar.update(n=1)

        # wait for all the threads to complete
        wait(processList)
    
