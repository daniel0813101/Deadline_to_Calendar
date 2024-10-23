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

        # Find 113_1 classes
        driver.switch_to.default_content()
        driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "s_main"))))
        l = driver.find_elements(By.CLASS_NAME, 'text-left')
        for i in l:
            print(i.text)
            if '1131_' in i.text:
                print(i.text.split('_')[1])
                i.find_element(By.XPATH, "./ancestor::tr").find_element(By.XPATH, ".//button[@class='btn btn-gray']").click()
                time.sleep(2)



                # Back to origin homework page
                driver.switch_to.default_content()
                driver.switch_to.frame(driver.find_element(By.ID, "moocSysbar"))
                dropdown = Select(driver.find_element(By.ID, 'selcourse'))
                dropdown.select_by_value('10000000')

                time.sleep(2)

                driver.switch_to.default_content()
                driver.switch_to.frame(WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "moocSysbar"))))
                driver.find_element(By.ID, 'SYS_06_01_004').click()
    
                time.sleep(2)

                driver.switch_to.default_content()
                driver.switch_to.frame(driver.find_element(By.ID, "s_main"))
                

                

    except Exception as e:
        print(f"An error occurred: {e}")
        driver.save_screenshot("error_screenshot.png")

    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run the scraping function
    login_and_scrape()
