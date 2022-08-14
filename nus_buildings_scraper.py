import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class Scraper:
    def __init__(self,url):
        self.url = url
        self.page_links = []
        self.names = []
        self.details = []
        self.map_info = pd.DataFrame(columns=["name","address","lat","lon"])
  
    # Get url links for navigation to each sub-section
    def scrape_page_links(self):
        page = requests.get(self.url, verify=False)
        soup = BeautifulSoup(page.content, 'html.parser')
        data = soup.find_all('a', class_='list-group-item child')
        self.page_links = list(map(lambda x: f"https://map.nus.edu.sg/{x['href']}", data))
        
    # Iterate through url links for each sub-section (across all pages) to scrape data
    def scrape_map_info(self): 
        # Get number of pages for each sub-section
        def extract_num_pages(driver, link, className):
            driver.get(link)
            last_page = 1
            for page in driver.find_elements(By.CLASS_NAME, className):
                if page.text.isnumeric():
                    if float(page.text) > last_page:
                        last_page = float(page.text)
            return int(last_page)
    
        lst_names = []
        lst_details = []
        links = self.page_links
        try:
            # Iterate through all sub-section links
            for link in links:
                driver = webdriver.Chrome(ChromeDriverManager().install())
                last_page = extract_num_pages(driver, link, "next_link")
                # Iterate through all pages for the sub-section
                for i in range(last_page):
                    url = link[0:len(link)-1] + str(i+1)
                    driver.get(url)
                    time.sleep(2)
                    xpath = "//*[@style='font-size:16px; font-weight:bold; text-decoration:none;']"
                    for e in driver.find_elements(By.XPATH, xpath):
                        print(e.text)
                        print(e.get_attribute("onclick").split("location.href = ")[1])
                        lst_names += [e.text]
                        lst_details += [e.get_attribute("onclick").split("location.href = ")[1]]

            self.names = lst_names
            self.details = lst_details
            
        except Exception as e:
            print(e)
        
    # Reformat html scrapped to extract address, lat and lon data
    def prepare_file(self):
        try:
            lat = list(map(lambda x:re.search(r"&lat=(.*?)';", x)[1], self.details))
            lon = list(map(lambda x:re.search(r"#page=map&long=(.*?)&", x)[1], self.details))
            addr = list(map(lambda x:re.search(r"set_lp(.*?)https", x)[1][1:].replace("'","")[:-2], self.details))
            addr_cleaned = [x.replace("\\", "'").replace("  "," ") for x in addr]
            self.map_info["name"] = self.names
            self.map_info["address"] = addr_cleaned
            self.map_info["lat"] = lat
            self.map_info["lon"] = lon
        except Exception as e:
            print(e)

    # Start the scraper
    def run_scraper(self):
        self.scrape_page_links()
        self.scrape_map_info()
        return self.map_info

s = Scraper("https://map.nus.edu.sg/#page=search&type=bus_stop&qword=All&p=1") 
s.run_scraper()
s.prepare_file()
s.map_info.to_csv('nus_buildings.csv')
