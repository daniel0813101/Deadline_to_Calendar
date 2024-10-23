from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
import os
import csv
import time 
from datetime import datetime


def login_and_scrape():
    # Setup Chrome WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    try:
        # Open CU login page
        driver.get('https://cu.nsysu.edu.tw/mooc/login.php')
        print("Opened CU login page")

        # Locate the username, password fields, and login button
        username = driver.find_element(By.ID, 's_username')
        password = driver.find_element(By.ID, 'password')
        login_button = driver.find_element(By.ID, 'btnSignIn')

        # Enter login credentials
        username.send_keys(os.getenv('USERNAME'))
        password.send_keys(os.getenv('PASSWORD'))

        # Click the login button
        login_button.click()

        # Wait for page to load and check current URL to verify login
        WebDriverWait(driver, 10).until(EC.url_changes('https://cu.nsysu.edu.tw/mooc/login.php'))
        current_url = driver.current_url
        if 'login' in current_url:
            print("Login failed: still on login page")
            return
        else:
            print("Login successful")

        time.sleep(2)

        # Navigate to the user's homework page
        driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "moocSysbar"))))
        driver.find_element(By.ID, 'SYS_06_01_004').click()
        print("Navigated to user homework page")

        time.sleep(2)

        
        # Find and store 113_1 classes
        driver.switch_to.default_content()
        driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "s_main"))))

        courses_to_process = []
        elements = driver.find_elements(By.CLASS_NAME, 'text-left')
        for element in elements:
            if '1131_' in element.text:
                courses_to_process.append(element.text)

        deadlines = {}
        print(deadlines)
        for course in courses_to_process:
            print(course)
            # Find the element again in the current page
            driver.switch_to.default_content()
            driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "s_main"))))   
                    
            # Find the specific course element and its button
            course_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, 
                    f"//div[@class='text-left'][contains(text(), '{course}')]")))
            course_name = course_element.text.split('_')[1]
            course_element.find_element(By.XPATH, "./ancestor::tr").find_element(By.XPATH, ".//button[@class='btn btn-gray']").click()
            time.sleep(3)

            # Get homeworks deadline 
            driver.switch_to.default_content()
            driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "s_main"))))   
            deadlines[course_name] = get_deadline(driver)
            print(f"{course_name } done")


            # Back to origin homework page
            driver.switch_to.default_content()
            driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "moocSysbar"))))
            dropdown = Select(driver.find_element(By.ID, 'selcourse'))
            dropdown.select_by_value('10000000')

            time.sleep(3)

            driver.switch_to.default_content()
            driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "moocSysbar"))))
            driver.find_element(By.ID, 'SYS_06_01_004').click()

            time.sleep(3)

            driver.switch_to.default_content()
            driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "s_main"))))

        print(deadlines)
        
        # Interact with Google Calendar
                

                

    except Exception as e:
        print(f"An error occurred: {e}")
        driver.save_screenshot("error_screenshot.png")

    finally:
        # Close the browser
        driver.quit()

# Get homework deadlines
def get_deadline(driver):
    
    hw_deadline = {}
    # Get deadline hw name and time
    try:
        homework_boxes = driver.find_elements(By.CLASS_NAME, "box2")
        for box in homework_boxes:
            title = box.find_element(By.XPATH, ".//span[@style='width: 230px;']").get_attribute("title")
            deadline = box.find_element(By.CLASS_NAME, "sub-text").text
            if '到' in deadline:
                end_date_str = deadline.split('到')[1].strip()

            deadline = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M')
            current_time = datetime.now()

            if deadline > current_time:
                hw_deadline[title] = deadline
            
            
    except Exception as e:
        print(f"Error getting deadlines: {e}")
        
    return hw_deadline


# Import deadlines to Google Calendar
def to_calendar():

    # Connect to Google Calendar API
    2

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run the scraping function
    login_and_scrape()
