from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import graph_chrome_correctly
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup
import pickle
from lxml import html
from selenium.common.exceptions import TimeoutException
import re
from config import USERNAME, PASSWORD

def driverGet():
    service = Service(executable_path=r'/files/chromedriver.exe')
    options = webdriver.ChromeOptions()

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-gpu')
    #options.add_argument('--headless')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument("--password-store=basic")
    options.add_argument("--start-maximized")
    options.add_extension('./files/ublock.crx')
    options.add_argument('--ignore-certificate-errors')
    options.add_experimental_option("detach", True)  # this prevent closing when it is complete!
    options.add_experimental_option('prefs', {
        'credentials_enable_service': True,
        'profile': {
            'password_manager_enabled': True
        }
    })

    try:
        driver = webdriver.Chrome(options=options)

    except Exception as e:
        print(e)
        graph_chrome_correctly.download_chromedriver().download()
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            print(e)
            print('Error in chromedriver.')
            exit(1)
    return driver

def login(browser):
    try:
        # Load and set cookies
        with open("./files/cookies.pkl", "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                browser.add_cookie(cookie)
        browser.get('https://www.linkedin.com/feed/')
        if 'deneme-hesap' in browser.page_source:
            print('Login successful by cookies.')
            return True
        else:
            raise Exception('Login failed by cookies.')
    except:
        browser.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')
        # linkedin
        time.sleep(1)
        link_user = browser.find_element(By.ID, 'username')
        link_user.send_keys(USERNAME)  # username

        # link_pass = browser.find_element_by_id('password')
        link_pass = browser.find_element(By.ID, 'password')
        link_pass.send_keys(PASSWORD)  # password

        browser.find_element(By.XPATH, '//*[@id="organic-div"]/form/div[3]/button').submit()

        browser.get('https://www.linkedin.com/feed/')
        WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div[3]')))
        if 'deneme-hesap' in browser.page_source:
            print('Login successful.')
            # Save cookies after login
            cookies = browser.get_cookies()
            with open("./files/cookies.pkl", "wb") as file:
                pickle.dump(cookies, file)
            return True
        else:
            print('Login unsuccessful.')
            return False

def loginFirst(keywords, joblink, browser):
    while(True):
        if login(browser):
            break
        else:
            time.sleep(1)
    pattern = re.compile(r"/jobs/view/[^/]+-(\d+)\??")

    # if login(browser):
    browser.get(joblink)
    numberofJob = int(browser.find_element(By.XPATH, '//*[@id="main-content"]/div/h1/span[1]').text)
    print(f"Total number of jobs: {numberofJob}")

    num = 1
    # Initialize current_scroll_position outside the while loop
    current_scroll_position = 0
    previous_numberofLinksGet = 0
    same_count_repeats = 0

    while True:
        # Get the total height of the page
        total_height = browser.execute_script("return document.body.scrollHeight")

        # Set the distance to scroll each time
        scroll_distance = 200

        # Scroll down the page in steps
        while current_scroll_position < total_height:
            browser.execute_script(f"window.scrollTo(0, {current_scroll_position});")
            time.sleep(0.2)  # Adjust sleep time as per your requirement
            current_scroll_position += scroll_distance

        element_html1 = browser.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/ul').get_attribute(
            'outerHTML')
        numberofLinksGet = len(
            BeautifulSoup(element_html1, 'html.parser').find_all('a', href=lambda href: (href and 'jobs/view' in href)))
        print(f"{num}. Total job collected: {numberofLinksGet}")

        if int(numberofJob) <= int(numberofLinksGet):
            break
        elif previous_numberofLinksGet == numberofLinksGet:
            same_count_repeats += 1
            if same_count_repeats >= 2:  # for example, break if the same count repeats 3 times
                print("Repeated count, breaking the loop.")
                break
        else:  # if the count is not the same as the previous, reset same_count_repeats
            same_count_repeats = 0

        previous_numberofLinksGet = numberofLinksGet  # Store the current count for the next iteration
        time.sleep(1)
        num += 1

    # Find the element using XPath
    element = browser.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/ul')

    # Extract HTML and find links using BeautifulSoup
    element_html = element.get_attribute('outerHTML')
    element_soup = BeautifulSoup(element_html, 'html.parser')
    links = element_soup.find_all('a')

    print(f"Total job collected: {len(element_soup.find_all('a', href=lambda href: (href and 'jobs/view' in href)))}")

    # Use a set to store unique links
    unique_links = set()

    # Add links to the set only if 'jobs/view' is in their 'href' attribute
    for link in links:
        href = link.get('href', '')
        if 'jobs/view' in href:
            # unique_links.add(href)
            match = pattern.search(href)
            if match:
                job_id = match.group(1)
                unique_links.add(job_id)

    # Print the count of unique links
    print("Unique links: ", len(unique_links))

    # Load existing links from link.txt into a set
    existing_links = set()
    try:
        with open("./files/links.txt", "r") as file:
            existing_links = set(line.strip() for line in file.readlines())
    except FileNotFoundError:
        # If file not found, we just continue since existing_links is already an empty set
        pass

    # Find the links that are in unique_links but not in existing_links
    new_links = unique_links - existing_links

    process_links = False

    # Process only new links that are not in link.txt
    with open("./files/links.txt", "a") as file:
        for job_id in new_links:

            finalLink = f"https://www.linkedin.com/jobs/view/{job_id}"
            print(finalLink)
            browser.get(finalLink)

            if 'authwall' in browser.current_url:
                print('authwall')
                login(browser)
                browser.get(finalLink)
            try:
                element_present = EC.presence_of_element_located((By.CLASS_NAME, 'show-more-less-html__markup'))
                WebDriverWait(browser, 10).until(element_present)  # Wait up to 10 seconds
            except TimeoutException:
                print("Timed out waiting for page to load")

            response = browser.page_source
            soup = BeautifulSoup(response, 'html.parser')

            i = 0
            while (True):
                # Extracting description
                description_div = soup.find('div', {'class': 'show-more-less-html__markup'})
                description = description_div.get_text(strip=True) if description_div else None
                if description != None:
                    break
                else:
                    time.sleep(0.2)
                    if i == 5:
                        description = 'None'
                        break

            # Convert the BeautifulSoup object to an lxml object
            lxml_soup = html.fromstring(str(soup))

            # Extracting applicant number
            # XPath for the applicant number
            xpath_selector_applicant = '//*[@id="main-content"]/section[1]/div/section[2]/div/div[1]/div/h4/div[2]/figure/figcaption'

            # Extracting applicant number
            applicant_number_element = lxml_soup.xpath(xpath_selector_applicant)
            applicant_number = applicant_number_element[0].text.strip() if applicant_number_element else None
            if applicant_number == None:
                applicant_number_element = soup.find('span', {'class': 'tvm__text tvm__text--positive'})
                applicant_number_strong = applicant_number_element.find('strong') if applicant_number_element else None
                applicant_number = applicant_number_strong.get_text(strip=True) if applicant_number_strong else None

            # Extracting date
            date_span = soup.find('span', {'class': 'posted-time-ago__text'})
            date = date_span.get_text(strip=True) if date_span else None

            i = 1
            while (True):
                # Extracting description
                # XPath for the title
                xpath_selector = f'//*[@id="main-content"]/section[1]/div/section[2]/div/div[{i}]/div/h1'
                # //*[@id="main-content"]/section[1]/div/section[2]/div/div[2]/div/h1
                # Extracting title
                title_element = lxml_soup.xpath(xpath_selector)
                title = title_element[0].text if title_element else None

                if title != None:
                    break
                else:
                    i += 1
                    time.sleep(0.2)

                if i == 5:
                    title = 'None'
                    break

            # Extracting company name
            company_name_a = soup.find('a', {'class': 'sub-nav-cta__optional-url'})
            company_name = company_name_a['title'] if company_name_a else None
            if company_name == None:
                company_location_div = soup.select_one('.job-details-jobs-unified-top-card__primary-description > div')
                company_name = company_location_div.get_text(strip=True).split('      ')[
                    0] if company_location_div else None

            matching_keywords_description = [word for word in keywords if word.lower() in description.lower()]
            matching_keywords_title = [word for word in keywords if word.lower() in title.lower()]

            # If any keywords match, print the information
            if matching_keywords_description or matching_keywords_title:
                print(f"Link: {finalLink}")
                print(f"Title: {title}")
                print(f"Applicant Number: {applicant_number}")
                print(f"Date: {date}")
                print(f"Company name: {company_name}")

                if matching_keywords_description:
                    print(f"Keywords matched in description: {', '.join(matching_keywords_description)}")

                if matching_keywords_title:
                    print(f"Keywords matched in title: {', '.join(matching_keywords_title)}")
                print('#############################################################################################')
            time.sleep(12325)
            file.write(job_id + "\n")

def withoutLogin(keywords, joblink, browser):
    pattern = re.compile(r"/jobs/view/[^/]+-(\d+)\??")

    # if login(browser):
    browser.get(joblink)
    numberofJob = int(browser.find_element(By.XPATH, '//*[@id="main-content"]/div/h1/span[1]').text)
    print(f"Total number of jobs: {numberofJob}")

    num = 1
    # Initialize current_scroll_position outside the while loop
    current_scroll_position = 0
    previous_numberofLinksGet = 0
    same_count_repeats = 0

    while True:
        # Get the total height of the page
        total_height = browser.execute_script("return document.body.scrollHeight")

        # Set the distance to scroll each time
        scroll_distance = 200

        # Scroll down the page in steps
        while current_scroll_position < total_height:
            browser.execute_script(f"window.scrollTo(0, {current_scroll_position});")
            time.sleep(0.2)  # Adjust sleep time as per your requirement
            current_scroll_position += scroll_distance

        element_html1 = browser.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/ul').get_attribute(
            'outerHTML')
        numberofLinksGet = len(
            BeautifulSoup(element_html1, 'html.parser').find_all('a', href=lambda href: (href and 'jobs/view' in href)))
        print(f"{num}. Total job collected: {numberofLinksGet}")

        if int(numberofJob) <= int(numberofLinksGet):
            break
        elif previous_numberofLinksGet == numberofLinksGet:
            same_count_repeats += 1
            if same_count_repeats >= 2:  # for example, break if the same count repeats 3 times
                print("Repeated count, breaking the loop.")
                break
        else:  # if the count is not the same as the previous, reset same_count_repeats
            same_count_repeats = 0

        previous_numberofLinksGet = numberofLinksGet  # Store the current count for the next iteration
        time.sleep(1)
        num += 1

    # Find the element using XPath
    element = browser.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/ul')

    # Extract HTML and find links using BeautifulSoup
    element_html = element.get_attribute('outerHTML')
    element_soup = BeautifulSoup(element_html, 'html.parser')
    links = element_soup.find_all('a')

    print(f"Total job collected: {len(element_soup.find_all('a', href=lambda href: (href and 'jobs/view' in href)))}")

    # Use a set to store unique links
    unique_links = set()

    # Add links to the set only if 'jobs/view' is in their 'href' attribute
    for link in links:
        href = link.get('href', '')
        if 'jobs/view' in href:
            # unique_links.add(href)
            match = pattern.search(href)
            if match:
                job_id = match.group(1)
                unique_links.add(job_id)

    # Print the count of unique links
    print("Unique links: ", len(unique_links))

    # Load existing links from link.txt into a set
    existing_links = set()
    try:
        with open("./files/links.txt", "r") as file:
            existing_links = set(line.strip() for line in file.readlines())
    except FileNotFoundError:
        # If file not found, we just continue since existing_links is already an empty set
        pass

    # Find the links that are in unique_links but not in existing_links
    new_links = unique_links - existing_links

    process_links = False

    # Process only new links that are not in link.txt
    with open("./files/links.txt", "a") as file:
        for job_id in new_links:

            # if '3733037715' in finalLink:
            #     process_links = True
            #
            # if not process_links:
            #     continue

            # if 'jobs/view' not in finalLink:
            #     continue
            finalLink = f"https://www.linkedin.com/jobs/view/{job_id}"
            print(finalLink)
            browser.get(finalLink)

            if 'authwall' in browser.current_url:
                print('authwall')
                login(browser)
                browser.get(finalLink)
            try:
                element_present = EC.presence_of_element_located((By.CLASS_NAME, 'show-more-less-html__markup'))
                WebDriverWait(browser, 10).until(element_present)  # Wait up to 10 seconds
            except TimeoutException:
                print("Timed out waiting for page to load")

            response = browser.page_source
            soup = BeautifulSoup(response, 'html.parser')

            i = 0
            while (True):
                # Extracting description
                description_div = soup.find('div', {'class': 'show-more-less-html__markup'})
                description = description_div.get_text(strip=True) if description_div else None
                if description != None:
                    break
                else:
                    time.sleep(0.2)
                    if i == 5:
                        description = 'None'
                        break

            # Convert the BeautifulSoup object to an lxml object
            lxml_soup = html.fromstring(str(soup))

            # Extracting applicant number
            # XPath for the applicant number
            xpath_selector_applicant = '//*[@id="main-content"]/section[1]/div/section[2]/div/div[1]/div/h4/div[2]/figure/figcaption'

            # Extracting applicant number
            applicant_number_element = lxml_soup.xpath(xpath_selector_applicant)
            applicant_number = applicant_number_element[0].text.strip() if applicant_number_element else None
            if applicant_number == None:
                applicant_number_element = soup.find('span', {'class': 'tvm__text tvm__text--positive'})
                applicant_number_strong = applicant_number_element.find('strong') if applicant_number_element else None
                applicant_number = applicant_number_strong.get_text(strip=True) if applicant_number_strong else None

            # Extracting date
            date_span = soup.find('span', {'class': 'posted-time-ago__text'})
            date = date_span.get_text(strip=True) if date_span else None

            i = 1
            while (True):
                # Extracting description
                # XPath for the title
                xpath_selector = f'//*[@id="main-content"]/section[1]/div/section[2]/div/div[{i}]/div/h1'
                # //*[@id="main-content"]/section[1]/div/section[2]/div/div[2]/div/h1
                # Extracting title
                title_element = lxml_soup.xpath(xpath_selector)
                title = title_element[0].text if title_element else None

                if title != None:
                    break
                else:
                    i += 1
                    time.sleep(0.2)

                if i == 5:
                    title = 'None'
                    break

            # Extracting company name
            company_name_a = soup.find('a', {'class': 'sub-nav-cta__optional-url'})
            company_name = company_name_a['title'] if company_name_a else None
            if company_name == None:
                company_location_div = soup.select_one('.job-details-jobs-unified-top-card__primary-description > div')
                company_name = company_location_div.get_text(strip=True).split('      ')[
                    0] if company_location_div else None

            matching_keywords_description = [word for word in keywords if word.lower() in description.lower()]
            matching_keywords_title = [word for word in keywords if word.lower() in title.lower()]

            # If any keywords match, print the information
            if matching_keywords_description or matching_keywords_title:
                print(f"Link: {finalLink}")
                print(f"Title: {title}")
                print(f"Applicant Number: {applicant_number}")
                print(f"Date: {date}")
                print(f"Company name: {company_name}")

                if matching_keywords_description:
                    print(f"Keywords matched in description: {', '.join(matching_keywords_description)}")

                if matching_keywords_title:
                    print(f"Keywords matched in title: {', '.join(matching_keywords_title)}")
                print('#############################################################################################')
            time.sleep(1)
            file.write(job_id + "\n")

def main(keywords, joblink, browser, loginProcess=True):
    if loginProcess == True:
        loginFirst(keywords, joblink, browser)
    else:
        withoutLogin(keywords, joblink, browser)


# Your keywords
keywords = [
    # English Keywords
    'biology', 'bioinformatics', 'proteomics', 'drug', 'pharma', 'bayer', 'sanofi',
    'mass spectrometry',
    'biotechnology', 'genomics',  'clinical', 'biomedical',
    'life sciences', 'computational biology', 'molecular biology', 'biochemistry','Python',

    # German Keywords
    'biologie', 'bioinformatik', 'proteomik', 'arzneimittel',
    'massenspektrometrie',
    'biotechnologie', 'genomik', 'klinisch', 'biomedizinisch',
    'lebenswissenschaften', 'computational biology', 'molekularbiologie'
]

# frankfurt job search link
# 'https://www.linkedin.com/jobs/search/?keywords=Data%20Scientist&location=Germany&locationId=&geoId=101282230&f_TPR=r86400&f_PP=106772406&position=1&pageNum=0'

#link = input('Enter the link: ')
# joblink = 'https://www.linkedin.com/jobs/search/?currentJobId=&geoId=101282230&keywords=data%20scientist&location=Germany&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true'

# 24h jobs in frankfurt
url = 'https://www.linkedin.com/jobs/search/?keywords=Data%20Scientist&location=Germany&locationId=&geoId=101282230&f_TPR=r86400&f_PP=106772406&position=1&pageNum=0'

url = 'https://www.linkedin.com/jobs/search/?currentJobId=3727693937&distance=25&geoId=101282230&keywords=python%20proteomics&origin=JOBS_HOME_KEYWORD_HISTORY&refresh=true'

browser = driverGet()
try:
    main(keywords, url, browser, loginProcess=True)
    browser.quit()
    print('Browser closed')
except Exception as e:
    print('Exception occured: ', e)
    #browser.quit()
    #print('Browser closed')