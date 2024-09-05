from bs4 import BeautifulSoup
import re
import random
import csv
# If you get an error message when importing BeautifulSoup, pip install it.

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

### Selenium ###
# Some websites track the delay time between certain actions such as clicking, loading, etc.

# To cut down on the amount of unnecessary code, just choose your options (location, types of homes, etc) on Trulia,
# and then copy the link below to URL:
URL = "https://www.trulia.com/for_sale/Baltimore,MD/39.21264,39.41584,-76.73825,-76.48247_xy/12_zm/"

### To "humanise" my webscraper: ###
# This code returns random floating point numbers between 3 and 5.
time_delay = random.uniform(3,5)

# Get your http header here: https://myhttpheader.com/
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 "
                  "Safari/537.36",
    "Accept-Language": "hu,en-US;q=0.9,en;q=0.8",
    "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
               "application/signed-exchange;v=b3;q=0.7"),
    "Accept-Encoding": "gzip, deflate, br"
}

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
accept_language = "hu,en-US;q=0.9,en;q=0.8"
accept = ("text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
               "application/signed-exchange;v=b3;q=0.7")
accept_encoding = "gzip, deflate, br"

chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument(f"user-agent={user_agent}")
chrome_options.add_argument(f"accept-language={accept_language}")
chrome_options.add_argument(f"accept={accept}")
chrome_options.add_argument(f"accept-encoding={accept_encoding}")

driver = webdriver.Chrome(options=chrome_options)
driver.get(URL)
time.sleep(time_delay)

# Maximize current window (personal preference):
driver.maximize_window()
time.sleep(time_delay)

# Empty lists for the parsed data:
prices_list_usd = []
addresses_list = []
postcodes_list = []
links_list = []

# Empty lists for the extracted room numbers and area:
bedrooms_list = []
bathrooms_list = []
area_in_sqft_list = []

def parser():
    # Instead of lxml, I use html.parser which is more suitable for content that is dynamically loaded by the browser:
    website = driver.page_source
    soup = BeautifulSoup(website, "html.parser")

    ### Scraping Trulia ###
    # Getting the web elements which contain the most important information:
    listing_addresses = soup.find_all(name="div", attrs={"data-testid": "property-address"})
    listing_prices = soup.find_all(name="div", attrs={"data-testid": "property-price"})
    listing_links = soup.find_all(name="a", attrs={"data-testid": "property-card-link"})

    # This below element suddenly changed on the website so had to replace it. It might change again in the future:
    # listing_details = soup.find_all(name="div", class_="Padding-sc-1tki7vp-0 eTEQyY")
    listing_details = soup.find_all(name="div", class_="pt_xxxs")

    try:
        for i in range(len(listing_addresses)):
             address = listing_addresses[i].getText().strip()
             if address not in addresses_list:
                 addresses_list.append(address)
                 # Here, I split the price element on the "/" and remove the "$" sign to make subsequent work easier.
                 # I also remove the decimals in one go:
                 price = listing_prices[i].getText().strip().split("/")[0].strip("$").replace(",", "")
                 if price:
                    prices_list_usd.append(price)
                 else:
                    prices_list_usd.append("NaN")

                 # I separate the postcode to make later analysis possible based on it:
                 postcode = addresses_list[i].split(",")[2].split()[1]
                 postcodes_list.append(postcode)

                 # Parsing only acquired partial links, so in order to make them clickable, this is what I used:
                 trulia_url = "https://www.trulia.com"
                 link = listing_links[i].get("href")
                 full_link = f"{trulia_url}{link}"
                 links_list.append(full_link)

                 # Getting hold of the room and area info:
                 content = listing_details[i].getText()

                 # Defining regex patterns to extract the numbers preceding "bd", "ba", "sqft" (if present):
                 bd_pattern = re.compile(r'(\d+)(?=bd)')
                 ba_pattern = re.compile(r'(\d+)(?=ba)')
                 sqft_pattern = re.compile(r'(\d+(?:,\d{3})*)(?=\s+sqft)')

                 # Loop through each element in the content list to check for missing "bd", "ba", or "sqft" values and
                 # replace them with "NaN":
                 # Extract numbers preceding "bd"
                 bd_match = bd_pattern.search(content)
                 if bd_match:
                     # The code below captures the first group of the pattern, which is (\d+), standing for one or more
                     # numbers before "bd" (if present):
                     bedrooms_list.append(bd_match.group(1))
                 else:
                     # If "bd" is not present, it will be substituted by "NaN":
                     bedrooms_list.append("NaN")

                 # Extract numbers preceding "ba"
                 ba_match = ba_pattern.search(content)
                 if ba_match:
                     bathrooms_list.append(ba_match.group(1))
                 else:
                     bathrooms_list.append("NaN")

                 # Extract numbers preceding "sqft" (including numbers with commas)
                 sqft_match = sqft_pattern.search(content)
                 if sqft_match:
                     # Clean the area_in_sqft by removing the decimals in one go:
                     area_in_sqft_list.append(sqft_match.group(1).replace(",", ""))
                 else:
                     area_in_sqft_list.append("NaN")
             else:
                 continue
    except Exception:
        pass

def write_to_csv():
    with open("housing.csv", "w", newline="", encoding="utf-8") as csvfile:
        columns = ["address", "postcode", "price", "bedrooms", "bathrooms",
                   "area_in_sqft", "link"]
        # Using DictWriter to avoid errors in data entry:
        writer = csv.DictWriter(csvfile, fieldnames=columns)

        writer.writeheader()
        for i in range(len(addresses_list)):
            writer.writerow({
                "address": addresses_list[i],
                "postcode": postcodes_list[i],
                "price": prices_list_usd[i],
                "bedrooms": bedrooms_list[i],
                "bathrooms": bathrooms_list[i],
                "area_in_sqft": area_in_sqft_list[i],
                "link": links_list[i]
            })

while True:
# Instead of while True, use this if you want to test the code on a few pages:
# for pages in range(2):
    for _ in range(12):  # This is the range it took the code to scroll to the end of the listings on a page
        parser()
        time.sleep(time_delay)
        driver.execute_script("window.scrollBy(0, window.innerHeight);")  # To scroll down one page
        print("Scrolling...")
        time.sleep(time_delay)
    try:
        write_to_csv()
        time.sleep(time_delay)

        next_button = driver.find_element(By.XPATH, "//span[@rel='next' and @aria-label='Next Page']")
        actions = ActionChains(driver)
        actions.move_to_element(next_button).click().perform()

        print("Clicked Next Page")
        time.sleep(time_delay)

    except Exception:
        print("No Next Page Button found.")
        driver.quit()
        break

### To check if you were successful: ###
# print(f"Adresses: {addresses_list}")
# print(f"Prices: {prices_list_usd}")
# print(f"Postcodes: {postcodes_list}")
# print(f"Links: {links_list}")
# print(f"Bedrooms: {bedrooms_list}")
# print(f"Bathrooms: {bathrooms_list}")
# print(f"Area: {area_in_sqft_list}")

# print(len(links_list))
# print(len(area_in_sqft_list))


### Code alternatives I've tried for scrolling down: ###
# Scroll down a specific amount of pixels:
# driver.execute_script("window.scrollBy(0, 200);")
# Scroll down by pressing the Page Down key (proved to be too short):
# driver.find_elements_by_name("body").send_keys(Keys.PAGE_DOWN)

### Code alternatives I've tried for pagination. ###
### Most of them were caught by the website so I had to add extra measures to "humanise" my parsing: ###
# next_button = driver.find_element(By.CSS_SELECTOR, value="span[rel='next'][aria-label='Next Page'][role='button']")
# next_button = driver.find_element(By.XPATH, value="//span[@rel='next' and @aria-label='Next Page']")
# next_button = driver.find_element(By.XPATH, value="//*[@id="resultsColumn"]/nav/ul/li[8]")
# next_button = driver.find_element(By.XPATH, value="//svg[@role='img' and @viewBox='0 0 32 32']")
# next_button = driver.find_element(By.CSS_SELECTOR, value="li[data-testid='pagination-next-page'] a")
# next_button.click()