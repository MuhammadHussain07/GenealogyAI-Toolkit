# import csv
# import time
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.common.keys import Keys
# import undetected_chromedriver as uc
# from bs4 import BeautifulSoup
# from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

# # Configuration
# EMAIL = "anthonymdavenport@gmail.com"
# PASSWORD = "Jackson2008!"
# TREE_URL = "https://www.ancestry.com/family-tree/tree/191247410/family?cfpid=382485586551"
# CSV_FILENAME = "ancestry_family_tree.csv"

# def initialize_driver():
#     options = uc.ChromeOptions()
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_argument("--start-maximized")
#     driver = uc.Chrome(options=options)
#     return driver

# def safe_click(driver, element, max_attempts=3):
#     """Attempt to click an element safely using different methods."""
#     attempts = 0
#     while attempts < max_attempts:
#         try:
#             # Wait for any overlays to disappear
#             time.sleep(1)
            
#             # Scroll element into center of viewport
#             driver.execute_script(
#                 "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", 
#                 element
#             )
#             time.sleep(1)
            
#             # Try multiple click methods
#             try:
#                 element.click()
#             except ElementClickInterceptedException:
#                 # Try JavaScript click
#                 driver.execute_script("arguments[0].click();", element)
#             except:
#                 # Try Actions chain
#                 ActionChains(driver).move_to_element(element).click().perform()
                
#             return True
            
#         except Exception as e:
#             print(f"Click attempt {attempts + 1} failed: {str(e)}")
#             attempts += 1
#             time.sleep(1)
    
#     return False

# def save_to_csv(data, filename):
#     """Save extracted data to CSV file."""
#     try:
#         with open(filename, mode="w", newline="", encoding="utf-8") as file:
#             writer = csv.writer(file)
#             writer.writerow(["Name", "DOB", "Place of Birth", "Death Status", "Timeline", "Sources"])
#             writer.writerows(data)
#         print(f"[SUCCESS] Data successfully saved to {filename}")
#     except Exception as e:
#         print(f"[ERROR] Failed to save data to CSV: {str(e)}")

# def parse_dob_and_death(dob_text):
#     """Parse date of birth, place of birth, and death status from text."""
#     try:
#         dob = place_of_birth = "Unknown"
#         death_status = "Living"
        
#         # Split text into parts for better parsing
#         parts = dob_text.split()
        
#         # Parse birth information
#         if "B:" in dob_text:
#             birth_index = dob_text.index("B:") + 2
#             birth_info = dob_text[birth_index:].split("D:")[0].strip()
            
#             # Try to separate date and place
#             try:
#                 date_parts = []
#                 place_parts = []
#                 started_place = False
                
#                 for part in birth_info.split():
#                     if started_place or not (part[0].isdigit() or part in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
#                         started_place = True
#                         place_parts.append(part)
#                     else:
#                         date_parts.append(part)
                
#                 dob = " ".join(date_parts)
#                 place_of_birth = " ".join(place_parts)
#             except:
#                 dob = birth_info
        
#         # Parse death information
#         if "D:" in dob_text:
#             death_index = dob_text.index("D:") + 2
#             death_info = dob_text[death_index:].strip()
#             death_status = death_info if death_info else "Deceased"
        
#         return dob.strip(), place_of_birth.strip(), death_status.strip()
#     except Exception as e:
#         print(f"[WARNING] Error parsing birth/death info: {str(e)}")
#         return "Unknown", "Unknown", "Unknown"

# def extract_family_data(driver):
#     """Extract family member data from the family tree."""
#     family_data = []
#     try:
#         # Wait for family tree to load and get initial set of members
#         print("[INFO] Waiting for family tree members...")
#         WebDriverWait(driver, 30).until(
#             EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.nodeTitle.notranslate"))
#         )
        
#         # Give the page extra time to fully render
#         time.sleep(5)
        
#         members = driver.find_elements(By.CSS_SELECTOR, "span.nodeTitle.notranslate")
#         print(f"[INFO] Found {len(members)} family members.")

#         for i, member in enumerate(members):
#             try:
#                 print(f"[INFO] Processing member {i + 1}...")
                
#                 # Try to click the member with our safe click function
#                 if not safe_click(driver, member):
#                     print(f"[WARNING] Could not click member {i + 1} after multiple attempts")
#                     continue

#                 # Wait for modal to appear
#                 try:
#                     modal = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR, "div.treeProfileInfoWrapper"))
#                     )
#                 except TimeoutException:
#                     print(f"[WARNING] Modal did not appear for member {i + 1}")
#                     continue

#                 # Extract modal content with retry
#                 max_retries = 3
#                 for retry in range(max_retries):
#                     try:
#                         html = driver.page_source
#                         soup = BeautifulSoup(html, "html.parser")
                        
#                         name = soup.select_one("span.treeProfileInfoName")
#                         if not name:
#                             raise ValueError("Name element not found")
#                         name = name.get_text(strip=True)
                        
#                         dob_info = soup.select_one("div.treeProfileInfoDatePlace")
#                         if not dob_info:
#                             raise ValueError("Date/place info not found")
#                         dob_info = dob_info.get_text(strip=True)
                        
#                         dob, place_of_birth, death_status = parse_dob_and_death(dob_info)
#                         break
#                     except Exception as e:
#                         if retry == max_retries - 1:
#                             raise
#                         time.sleep(1)

#                 print(f"[SUCCESS] Extracted: {name}")
#                 family_data.append([name, dob, place_of_birth, death_status, "", ""])

#                 # Close modal with retry
#                 try:
#                     close_button = WebDriverWait(driver, 5).until(
#                         EC.element_to_be_clickable((By.CSS_SELECTOR, "button.close"))
#                     )
#                     safe_click(driver, close_button)
#                 except:
#                     # If can't find close button, try pressing ESC
#                     ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                
#                 time.sleep(2)  # Wait for modal to fully close

#             except Exception as e:
#                 print(f"[WARNING] Failed to process member {i + 1}: {str(e)}")
#                 # Try to close any open modals before continuing
#                 try:
#                     ActionChains(driver).send_keys(Keys.ESCAPE).perform()
#                 except:
#                     pass
#                 time.sleep(2)
#                 continue

#     except Exception as e:
#         print(f"[ERROR] Unable to extract family data: {str(e)}")

#     return family_data

# def login_and_navigate(driver):
#     """Login to Ancestry and navigate to the family tree page."""
#     try:
#         print("[INFO] Logging in to Ancestry...")
#         driver.get("https://www.ancestry.com/signin")
        
#         # Wait for login form and enter credentials
#         WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username")))
        
#         username_field = driver.find_element(By.ID, "username")
#         password_field = driver.find_element(By.ID, "password")
        
#         # Clear fields and enter credentials
#         username_field.clear()
#         password_field.clear()
#         username_field.send_keys(EMAIL)
#         password_field.send_keys(PASSWORD)
        
#         # Submit login form
#         submit_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
#         safe_click(driver, submit_button)

#         # Wait for successful login
#         WebDriverWait(driver, 30).until(lambda d: "signin" not in d.current_url.lower())
#         print("[SUCCESS] Logged in successfully!")

#         # Navigate to family tree page
#         print("[INFO] Navigating to the family tree page...")
#         driver.get(TREE_URL)
#         time.sleep(5)  # Wait for page to load completely

#         # Extract and save family data
#         family_data = extract_family_data(driver)
#         save_to_csv(family_data, CSV_FILENAME)

#     except Exception as e:
#         print(f"[ERROR] Failed during login or navigation: {str(e)}")
#         raise

# def main():
#     """Main function to run the scraper."""
#     driver = None
#     try:
#         driver = initialize_driver()
#         login_and_navigate(driver)
#     except Exception as e:
#         print(f"[ERROR] Script failed: {str(e)}")
#     finally:
#         if driver:
#             driver.quit()

# if __name__ == "__main__":
#     main()


import csv
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException
)

# Configuration
EMAIL = "anthonymdavenport@gmail.com"
PASSWORD = "Jackson2008!"
TREE_URL = "https://www.ancestry.com/family-tree/tree/191247410/family?cfpid=382485586551"
CSV_FILENAME = "ancestry_timeline_facts.csv"

def initialize_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    return uc.Chrome(options=options)

def wait_for_element(driver, by, selector, timeout=10, condition="presence"):
    """Generic wait function with different conditions."""
    try:
        if condition == "clickable":
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
        else:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        return element
    except TimeoutException:
        print(f"Timeout waiting for element: {selector}")
        return None

def safe_click(driver, element, max_attempts=3):
    """Enhanced safe click function with multiple fallback methods."""
    for attempt in range(max_attempts):
        try:
            # Scroll element into view
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(1)
            
            # Try different click methods
            try:
                element.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", element)
            except:
                ActionChains(driver).move_to_element(element).click().perform()
            
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"Click attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_attempts - 1:
                return False
            time.sleep(1)

def extract_timeline_events(driver):
    """Extract timeline events from the Facts tab."""
    events = []
    try:
        # Wait for timeline events to load
        time.sleep(3)
        timeline_container = wait_for_element(driver, By.CLASS_NAME, "timeline")
        
        if timeline_container:
            # Find all event elements
            event_elements = driver.find_elements(By.CSS_SELECTOR, ".event")
            
            for event in event_elements:
                try:
                    event_data = {}
                    
                    # Extract event type
                    event_type = event.find_element(By.CSS_SELECTOR, ".eventType").text.strip()
                    
                    # Extract date
                    try:
                        date = event.find_element(By.CSS_SELECTOR, ".eventDate").text.strip()
                    except:
                        date = "Unknown"
                    
                    # Extract location
                    try:
                        location = event.find_element(By.CSS_SELECTOR, ".eventLocation").text.strip()
                    except:
                        location = "Unknown"
                    
                    event_data = {
                        "type": event_type,
                        "date": date,
                        "location": location
                    }
                    
                    events.append(event_data)
                    
                except Exception as e:
                    print(f"Error extracting event details: {str(e)}")
                    continue
                    
    except Exception as e:
        print(f"Error extracting timeline events: {str(e)}")
    
    return events

def extract_profile_data(driver):
    """Extract timeline-based facts from the profile page with improved element detection."""
    try:
        print("[DEBUG] Starting profile data extraction...")
        
        # Wait for initial page load
        time.sleep(5)
        
        # Initialize profile data
        profile_data = {
            "name": "Unknown",
            "birth_info": {},
            "death_info": {},
            "events": [],
            "residences": [],
            "marriage_info": []
        }
        
        # Extract name - updated selector based on your screenshot
        try:
            name_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".personTitle"))
            )
            if name_element:
                profile_data["name"] = name_element.text.strip()
                print(f"[DEBUG] Found name: {profile_data['name']}")
        except Exception as e:
            print(f"[WARNING] Could not extract name: {str(e)}")

        # Make sure we're on the Facts tab
        try:
            tabs = driver.find_elements(By.CSS_SELECTOR, ".nav-tabs li a")
            facts_tab = None
            for tab in tabs:
                if "Facts" in tab.text:
                    facts_tab = tab
                    break
            
            if facts_tab:
                driver.execute_script("arguments[0].click();", facts_tab)
                time.sleep(3)
        except Exception as e:
            print(f"[WARNING] Could not switch to Facts tab: {str(e)}")

        # Extract Timeline events
        try:
            timeline = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "timeline"))
            )
            
            events = timeline.find_elements(By.CSS_SELECTOR, "[class*='fact-row']")
            print(f"[DEBUG] Found {len(events)} events")
            
            for event in events:
                try:
                    event_data = {}
                    
                    # Extract event type
                    event_type_elem = event.find_element(By.CSS_SELECTOR, "[class*='fact-type']")
                    event_data["type"] = event_type_elem.text.strip()
                    
                    # Extract date
                    try:
                        date_elem = event.find_element(By.CSS_SELECTOR, "[class*='fact-date']")
                        event_data["date"] = date_elem.text.strip()
                    except:
                        event_data["date"] = "Unknown"
                    
                    # Extract location
                    try:
                        location_elem = event.find_element(By.CSS_SELECTOR, "[class*='fact-location']")
                        event_data["location"] = location_elem.text.strip()
                    except:
                        event_data["location"] = "Unknown"
                    
                    # Process specific event types
                    if "Birth" in event_data["type"]:
                        profile_data["birth_info"] = {
                            "date": event_data["date"],
                            "location": event_data["location"]
                        }
                    elif "Death" in event_data["type"]:
                        profile_data["death_info"] = {
                            "date": event_data["date"],
                            "location": event_data["location"]
                        }
                    elif "Residence" in event_data["type"]:
                        profile_data["residences"].append(f"{event_data['date']} - {event_data['location']}")
                    elif "Marriage" in event_data["type"]:
                        profile_data["marriage_info"].append(f"{event_data['date']} - {event_data['location']}")
                    
                    profile_data["events"].append(event_data)
                    print(f"[DEBUG] Processed event: {event_data['type']}")
                    
                except Exception as e:
                    print(f"[WARNING] Error processing event: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"[WARNING] Error extracting timeline events: {str(e)}")
        
        print("[DEBUG] Profile data extraction completed")
        return profile_data

    except Exception as e:
        print(f"[ERROR] Failed to extract profile data: {str(e)}")
        print(f"[DEBUG] Current URL: {driver.current_url}")
        return None
def process_family_member(driver, member):
    """Process a single family member."""
    try:
        # Store current window handle
        main_window = driver.current_window_handle
        
        # Click member name with retry logic
        if not safe_click(driver, member):
            return None
        
        # Wait for and click Profile link
        profile_link = wait_for_element(
            driver,
            By.XPATH,
            "//a[contains(text(), 'Profile') or contains(@class, 'profileLink')]",
            condition="clickable"
        )
        
        if not profile_link or not safe_click(driver, profile_link):
            return None
        
        # Switch to new window/tab if opened
        time.sleep(3)
        windows = driver.window_handles
        if len(windows) > 1:
            driver.switch_to.window(windows[-1])
        
        # Extract profile data
        profile_data = extract_profile_data(driver)
        
        # Clean up and return to main window
        if len(windows) > 1:
            driver.close()
            driver.switch_to.window(main_window)
        else:
            driver.back()
            time.sleep(3)
        
        return profile_data
        
    except Exception as e:
        print(f"Error processing family member: {str(e)}")
        # Recovery attempt
        try:
            if len(driver.window_handles) > 1:
                driver.switch_to.window(main_window)
        except:
            pass
        return None

def extract_family_data(driver):
    """Extract data for all family members."""
    all_profile_data = []
    
    try:
        print("Waiting for family tree to load...")
        member_elements = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.nodeTitle.notranslate"))
        )
        time.sleep(5)
        
        print(f"Found {len(member_elements)} family members")
        
        for i, member in enumerate(member_elements, 1):
            print(f"\nProcessing member {i}/{len(member_elements)}")
            
            try:
                profile_data = process_family_member(driver, member)
                if profile_data:
                    all_profile_data.append(profile_data)
                    print(f"Successfully extracted data for {profile_data['name']}")
            except StaleElementReferenceException:
                print("Member element became stale, refreshing elements...")
                # Refresh the list of members
                member_elements = driver.find_elements(By.CSS_SELECTOR, "span.nodeTitle.notranslate")
                continue
            
    except Exception as e:
        print(f"Error extracting family data: {str(e)}")
    
    return all_profile_data

def save_to_csv(data, filename):
    """Save extracted data to CSV with improved structure."""
    headers = [
        "Name",
        "Birth Date",
        "Birth Location",
        "Death Date",
        "Death Location",
        "Events",
        "Sources"
    ]
    
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            
            for profile in data:
                events_str = "; ".join([
                    f"{event['type']}: {event['date']} - {event['location']}"
                    for event in profile['events']
                ])
                
                writer.writerow({
                    "Name": profile["name"],
                    "Birth Date": profile["birth_info"].get("date", "Unknown"),
                    "Birth Location": profile["birth_info"].get("location", "Unknown"),
                    "Death Date": profile["death_info"].get("date", "Unknown"),
                    "Death Location": profile["death_info"].get("location", "Unknown"),
                    "Events": events_str,
                    "Sources": "; ".join(profile["sources"])
                })
                
        print(f"Data successfully saved to {filename}")
        
    except Exception as e:
        print(f"Error saving to CSV: {str(e)}")

def main():
    driver = None
    try:
        driver = initialize_driver()
        
        # Login
        print("Logging in...")
        driver.get("https://www.ancestry.com/signin")
        
        username_field = wait_for_element(driver, By.ID, "username")
        password_field = wait_for_element(driver, By.ID, "password")
        
        if username_field and password_field:
            username_field.send_keys(EMAIL)
            password_field.send_keys(PASSWORD)
            
            submit_button = wait_for_element(
                driver,
                By.XPATH,
                '//button[@type="submit"]',
                condition="clickable"
            )
            if submit_button:
                safe_click(driver, submit_button)
        
        # Wait for login completion
        WebDriverWait(driver, 30).until(lambda d: "signin" not in d.current_url.lower())
        print("Login successful")
        
        # Navigate to family tree
        print("Navigating to family tree...")
        driver.get(TREE_URL)
        time.sleep(5)
        
        # Extract and save data
        profile_data = extract_family_data(driver)
        save_to_csv(profile_data, CSV_FILENAME)
        
    except Exception as e:
        print(f"Script failed: {str(e)}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()