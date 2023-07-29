""" This is a Python Scraper which gathers room prices
from www.airbnb.com and www.hotels.com.
The purpose of this program is to automatically gather room prices
while running on GitHub Action System.
This is a refactored version of Sion99/PythonCrawler.
The original code is available at https://github.com/Sion99/PythonCrawler
For more information about scraping www.airbnb.com, visit https://www.airbnb.com/robots.txt
"""

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import datetime
import time
import platform
from scipy import stats
import re

locations = [
    ["제주도", "6049718"],
    ["다낭", "6297250"],
    ["도쿄", "3593"],
    ["오사카", "2697"],
    ["후쿠오카", "6336957"],
    ["삿포로", "3250"],
    ["오키나와", "10805"],
    ["하노이", "6054458"],
    ["호치민", "3140"],
    ["방콕", "604"],
    ["비엔티안", "553248635937188604"],
    ["타이베이", "3518"],
    ["홍콩", "184245"],
    ["마카오", "6054541"],
    ["괌", "70"],
    ["세부", "800"],
]


def getChromeOptions():
    """Necessary for GitHub Actions"""
    chrome_driver = os.path.join("chromedriver")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    service = Service(executable_path=chrome_driver)
    return service, chrome_options


def getChromeDriver():
    if platform.platform().startswith("macOS"):
        chrome_options = webdriver.ChromeOptions()
        #chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
    else:
        service, chrome_options = getChromeOptions()
        driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def getUrls(driver, checkin, checkout, location):
    initial = f"https://www.airbnb.co.kr/s/{location[0]}/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2023-07-01&monthly_length=3&price_filter_input_type=0&price_filter_num_nights=5&channel=EXPLORE&price_min=13000&price_max=500000&search_type=search_query&date_picker_type=calendar&checkin={checkin}&checkout={checkout}&adults=2&source=structured_search_input_header&search_type=filter_change"
    driver.get(initial)
    time.sleep(5)
    urls = []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    href = soup.find_all("a", class_="l1ovpqvx c1ackr0h dir dir-ltr")
    for h in href:
        endpoint = h.get("href")
        url = "https://www.airbnb.co.kr" + endpoint
        urls.append(url)
    return urls

def getDirectInfo(driver, checkin, checkout):
    for location in locations:
        url = f"https://www.airbnb.co.kr/s/{location[0]}/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2023-08-01&monthly_length=3&price_filter_input_type=0&price_filter_num_nights=5&channel=EXPLORE&price_min=13000&price_max=500000&search_type=search_query&date_picker_type=calendar&checkin={checkin}&checkout={checkout}&adults=2&source=structured_search_input_header&search_type=filter_change"
        driver.get(url)
        time.sleep(3)
        driver.find_element(By.XPATH, "/html/body/div[5]/div/div/div[1]/div/div[2]/div/div/div/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div/div/button").click()
        time.sleep(3)
        info = driver.find_element(By.XPATH, '//*[@id="tab--tabs--0"]/span[2]').text
        if info is None:
            info = driver.find_element(By.XPATH, '//*[@id="site-content"]/div[1]/div/div/div/div/div/section/div[2]/div/div/div/div[1]').text
            info = info[11:].replace(",", "")
            avg = int(re.findall(r'\d+', info))
        else:
            info = info[4:].replace(",", "")
            avg = int(info)
        print(location[0], avg)
    print("end of service")

def getAirbnb(driver, checkin, checkout):
    i = 0
    df = pd.DataFrame(columns=["지역", "숙소개수", "10% 절사평균", "중앙값", "표준편차"])
    for location in locations:
        urls = getUrls(driver, checkin, checkout, location)
        lists = []
        
        print(f"--------- location : {location[0]} ----------")
        print(f"--------- check-in date : {checkin} ----------")

        for url in urls:
            driver.get(url)
            time.sleep(5)
#            driver.execute_script("window.scrollTo(0, 2000)")
            soup = BeautifulSoup(driver.page_source, "html.parser")
            airbnbs = soup.find_all("div", class_="c4mnd7m dir dir-ltr")

            for airbnb in airbnbs:
                prices = airbnb.find_all("span", class_="a8jt5op dir dir-ltr")
                for price in prices:
                    if price.string.startswith("총 요금"):
                        print(f"{price.string}")
                        value = int(price.string[7:].replace(",", ""))
                        lists.append(value)
        
        avg10 = int(stats.trim_mean(lists, 0.1))
        med = np.median(lists)
        std = int(np.std(lists))
        num = len(lists)
        
        df.loc[i] = [location[0], num, avg10, med, std]
        i += 1
    df.to_csv(
                f"./data/{checkin}.csv", encoding="utf-8-sig"
            )
    print("end of service")


def getHotels(driver, checkin, checkout):
    driver.implicitly_wait(10)

    for location in locations:
        count = 0
        url = f"https://kr.hotels.com/Hotel-Search?adults=2&d1=2023-06-27&d2=2023-06-28&destination={location[0]}&endDate={checkout}&regionId={location[1]}&rooms=1&semdtl=&sort=RECOMMENDED&startDate={checkin}&theme=&useRewards=false&userIntent="

        while True:
            count += 1
            driver.get(url)
            time.sleep(10)
            driver.execute_script("window.scrollTo(0, 2000)")
            soup = BeautifulSoup(driver.page_source, "html.parser")
            hotels = soup.find_all(
                "div",
                class_="uitk-text uitk-type-300 uitk-text-default-theme is-visually-hidden",
            )
            if len(hotels) > 20 or count > 2:
                break
        i = 0
        df = pd.DataFrame(columns=["checkin", "checkout", "location", "price"])
        print(f"--------- trial : {count} ----------")
        print(f"--------- location : {location[0]} ----------")
        print(f"--------- check-in date : {checkin} ----------")

        for hotel in hotels:
            if hotel.string.startswith("현재 요금"):
                print(hotel.string)
                value1 = checkin
                value2 = checkout
                value3 = location[0]
                value4 = int(hotel.string[7:].replace(",", ""))
                df.loc[i] = [value1, value2, value3, value4]
                i += 1
        df.to_csv(
            f"./data/hotels{checkin}{location[0]}price.csv", encoding="utf-8-sig"
        )
    print("end of service")


if __name__ == "__main__":
    chromedriver = getChromeDriver()
    now = datetime.datetime.now()
    checkin = (now + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    checkout = (now + datetime.timedelta(days=8)).strftime("%Y-%m-%d")
    #getAirbnb(chromedriver, checkin, checkout)
    #getHotels(chromedriver, checkin, checkout)
    getDirectInfo(chromedriver, checkin, checkout)
    chromedriver.close()
    chromedriver.quit()
