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
            if '1132_' in element.text:
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
        return deadlines
        
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
def to_calendar(deadlines):
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    import os.path
    from datetime import datetime, timedelta

    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Create Google Calendar API service
    service = build('calendar', 'v3', credentials=creds)

    # Create events for each deadline
    for course_name, homework_dict in deadlines.items():
        for homework_title, deadline in homework_dict.items():
            # Create event start time (1 hour before deadline)
            start_time = deadline.replace(hour=deadline.hour - 1)
            
            # Set time range to search for existing events (1 day before and after the deadline)
            time_min = (deadline - timedelta(days=1)).isoformat() + 'Z'
            time_max = (deadline + timedelta(days=1)).isoformat() + 'Z'
            
            # Check if event already exists
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True
            ).execute()
            
            # Check each event in the time range for a match
            event_exists = False
            for existing_event in events_result.get('items', []):
                if existing_event.get('summary') == f'[Homework Due] {course_name}: {homework_title}':
                    print(f'Event for {homework_title} in {course_name} already exists')
                    event_exists = True
                    break
            
            if event_exists:
                continue
                
            event = {
                'summary': f'[Homework Due] {course_name}: {homework_title}',
                'description': f'Deadline for {homework_title} in {course_name}',
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Taipei',
                },
                'end': {
                    'dateTime': deadline.isoformat(),
                    'timeZone': 'Asia/Taipei',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60},       # 1 hour before
                    ],
                },
            }

            try:
                event = service.events().insert(calendarId='primary', body=event).execute()
                print(f'Created calendar event for {homework_title} in {course_name}')
            except Exception as e:
                print(f'Error creating event for {homework_title}: {e}')


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run the scraping function
    deadline = login_and_scrape()
    # Run the calendar event creation function
    to_calendar(deadline)
