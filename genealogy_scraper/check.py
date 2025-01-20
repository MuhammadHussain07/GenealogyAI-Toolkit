import csv
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import *
import undetected_chromedriver as uc

# Configuration
TREE_URL = "https://www.ancestry.com/family-tree/tree/191247410/family?cfpid=382485586551"
CSV_FILENAME = "ancestry_timeline_facts.csv"

def initialize_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    return uc.Chrome(options=options)

def wait_for_element(driver, by, selector, timeout=10, condition="presence"):
    try:
        if condition == "clickable":
            return WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
        else:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
    except TimeoutException:
        print(f"Timeout waiting for element: {selector}")
        return None

def safe_click(driver, element, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            # Scroll element into view
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            time.sleep(1)
            
            try:
                element.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", element)
            except:
                ActionChains(driver).move_to_element(element).click().perform()
            
            return True
            
        except Exception as e:
            print(f"Click attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_attempts - 1:
                return False
            time.sleep(1)

def extract_timeline_facts(driver):
    """Extract facts from the timeline section."""
    facts = []
    try:
        # Wait for Facts tab to be active
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='tabpanel']"))
        )
        
        # Wait for timeline items to load
        timeline_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".timeline-item"))
        )
        
        for item in timeline_items:
            try:
                fact = {}
                
                # Extract fact type
                fact_type = item.find_element(By.CSS_SELECTOR, ".fact-type").text.strip()
                fact["type"] = fact_type
                
                # Extract date
                try:
                    date_elem = item.find_element(By.CSS_SELECTOR, ".fact-date")
                    fact["date"] = date_elem.text.strip()
                except:
                    fact["date"] = "Unknown"
                
                # Extract location
                try:
                    location_elem = item.find_element(By.CSS_SELECTOR, ".fact-location")
                    fact["location"] = location_elem.text.strip()
                except:
                    fact["location"] = "Unknown"
                
                facts.append(fact)
                
            except Exception as e:
                print(f"Error extracting fact details: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error extracting timeline facts: {str(e)}")
    
    return facts

def extract_profile_data(driver):
    """Extract profile data with improved handling of dynamic content."""
    profile_data = {
        "name": "Unknown",
        "birth_info": {},
        "death_info": {},
        "facts": [],
        "sources": []
    }
    
    try:
        # Wait for profile content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "personTitle"))
        )
        
        # Extract name
        try:
            name_elem = driver.find_element(By.CLASS_NAME, "personTitle")
            profile_data["name"] = name_elem.text.strip()
        except:
            print("Could not extract name")
        
        # Make sure we're on the Facts tab
        try:
            facts_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[role='tab']:nth-child(1)"))
            )
            facts_tab.click()
            time.sleep(2)
        except:
            print("Could not switch to Facts tab")
        
        # Extract facts
        facts = extract_timeline_facts(driver)
        
        # Process facts into appropriate categories
        for fact in facts:
            if "Birth" in fact["type"]:
                profile_data["birth_info"] = {
                    "date": fact["date"],
                    "location": fact["location"]
                }
            elif "Death" in fact["type"]:
                profile_data["death_info"] = {
                    "date": fact["date"],
                    "location": fact["location"]
                }
            
            profile_data["facts"].append(fact)
        
        # Extract sources
        try:
            sources_tab = driver.find_element(By.CSS_SELECTOR, "button[role='tab']:nth-child(3)")
            sources_tab.click()
            time.sleep(2)
            
            source_elements = driver.find_elements(By.CSS_SELECTOR, ".source-item")
            profile_data["sources"] = [elem.text.strip() for elem in source_elements]
        except:
            print("Could not extract sources")
        
    except Exception as e:
        print(f"Error extracting profile data: {str(e)}")
    
    return profile_data

def process_family_member(driver, member_element):
    """Process individual family member with improved navigation and error handling."""
    main_window = driver.current_window_handle
    profile_data = None
    
    try:
        print(f"Processing member: {member_element.text}")
        
        # Click on member name and wait for popup
        if not safe_click(driver, member_element):
            print("Failed to click member name")
            return None
            
        time.sleep(2)  # Wait for popup to appear
        
        # Look for the profile link with multiple possible selectors
        profile_link = None
        selectors = [
            "a[data-testid='person-profile-link']",
            "a.profileLink",
            "a[href*='person/']",
            "//a[contains(text(), 'Profile')]"
        ]
        
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    profile_link = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    profile_link = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                if profile_link:
                    print("Found profile link")
                    break
            except:
                continue
        
        if not profile_link:
            print("Could not find profile link")
            return None
            
        # Click profile link using JavaScript
        try:
            driver.execute_script("arguments[0].click();", profile_link)
        except Exception as e:
            print(f"Failed to click profile link: {str(e)}")
            return None
            
        # Wait for new window/tab
        time.sleep(3)
        
        # Handle new window/tab
        new_window = None
        try:
            windows = driver.window_handles
            if len(windows) > 1:
                new_window = windows[-1]
                driver.switch_to.window(new_window)
                print("Switched to profile window")
            else:
                print("No new window opened, staying in current window")
        except Exception as e:
            print(f"Error switching windows: {str(e)}")
            return None
            
        # Wait for profile page to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "personTitle"))
            )
            print("Profile page loaded")
        except:
            print("Profile page did not load properly")
            return None
            
        # Extract profile data
        profile_data = extract_profile_data(driver)
        
        # Clean up
        if new_window:
            driver.close()
            driver.switch_to.window(main_window)
            
        return profile_data
        
    except Exception as e:
        print(f"Error in process_family_member: {str(e)}")
        # Recovery attempt
        try:
            windows = driver.window_handles
            if len(windows) > 1:
                driver.close()
            driver.switch_to.window(main_window)
        except:
            pass
        return None

def extract_family_data(driver):
    """Extract data for all family members with improved element detection."""
    all_profile_data = []
    
    try:
        print("Waiting for family tree to load...")
        # Wait for the page to load completely
        time.sleep(10)  # Give more time for the initial load
        
        # Try different selectors for finding family members
        possible_selectors = [
            ".person-card",  # Try person cards
            ".nodeTitle",    # Try node titles
            "[data-testid='person-name']",  # Try test IDs
            ".person-box",   # Try person boxes
            ".treeCard"      # Try tree cards
        ]
        
        member_elements = []
        for selector in possible_selectors:
            try:
                print(f"Trying selector: {selector}")
                elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                if elements:
                    member_elements = elements
                    print(f"Found {len(elements)} members using selector: {selector}")
                    break
            except Exception as e:
                print(f"Selector {selector} failed: {str(e)}")
                continue
        
        if not member_elements:
            print("Could not find any family members with standard selectors.")
            print("Attempting to find elements by XPath...")
            
            # Try XPath selectors as fallback
            xpath_selectors = [
                "//div[contains(@class, 'person')]",
                "//span[contains(@class, 'name')]",
                "//div[contains(@class, 'card')]//span",
                "//div[contains(@class, 'treeNode')]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elements = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.XPATH, xpath))
                    )
                    if elements:
                        member_elements = elements
                        print(f"Found {len(elements)} members using XPath: {xpath}")
                        break
                except Exception as e:
                    print(f"XPath {xpath} failed: {str(e)}")
                    continue
        
        if not member_elements:
            print("Failed to find any family members. Trying to capture page source...")
            print("Page source preview:")
            print(driver.page_source[:1000])  # Print first 1000 chars for debugging
            return all_profile_data
        
        print(f"\nProcessing {len(member_elements)} family members...")
        
        for i, member in enumerate(member_elements, 1):
            try:
                print(f"\nProcessing member {i}/{len(member_elements)}")
                
                # Print element details for debugging
                print(f"Element HTML: {member.get_attribute('outerHTML')}")
                print(f"Element text: {member.text}")
                print(f"Element tag: {member.tag_name}")
                print(f"Element classes: {member.get_attribute('class')}")
                
                # Try to ensure element is clickable
                driver.execute_script("arguments[0].scrollIntoView(true);", member)
                time.sleep(2)  # Wait for any animations
                
                # Try to click the element directly
                try:
                    member.click()
                except:
                    try:
                        # Try JavaScript click
                        driver.execute_script("arguments[0].click();", member)
                    except:
                        try:
                            # Try finding a clickable child element
                            clickable = member.find_element(By.CSS_SELECTOR, "a, span, div")
                            clickable.click()
                        except:
                            print(f"Could not click member {i}")
                            continue
                
                time.sleep(2)  # Wait for popup/menu
                
                # Look for profile link or button
                try:
                    profile_link = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "a[href*='person'], button[data-testid*='profile']")
                        )
                    )
                    profile_link.click()
                    time.sleep(3)  # Wait for new page/tab
                    
                    # Handle new window if opened
                    handles = driver.window_handles
                    if len(handles) > 1:
                        driver.switch_to.window(handles[-1])
                    
                    # Extract profile data
                    profile_data = extract_profile_data(driver)
                    
                    if profile_data:
                        all_profile_data.append(profile_data)
                        print(f"Successfully extracted data for {profile_data['name']}")
                    
                    # Clean up
                    if len(handles) > 1:
                        driver.close()
                        driver.switch_to.window(handles[0])
                    
                except Exception as e:
                    print(f"Error processing profile: {str(e)}")
                    continue
                
            except Exception as e:
                print(f"Error processing member {i}: {str(e)}")
                continue
            
            time.sleep(2)  # Wait between members
    
    except Exception as e:
        print(f"Error in extract_family_data: {str(e)}")
        print("Current URL:", driver.current_url)
    
    return all_profile_data
def save_to_csv(data, filename):
    """Save extracted data to CSV."""
    headers = [
        "Name",
        "Birth Date",
        "Birth Location",
        "Death Date",
        "Death Location",
        "Facts",
        "Sources"
    ]
    
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            
            for profile in data:
                facts_str = "; ".join([
                    f"{fact['type']}: {fact['date']} - {fact['location']}"
                    for fact in profile['facts']
                ])
                
                writer.writerow({
                    "Name": profile["name"],
                    "Birth Date": profile["birth_info"].get("date", "Unknown"),
                    "Birth Location": profile["birth_info"].get("location", "Unknown"),
                    "Death Date": profile["death_info"].get("date", "Unknown"),
                    "Death Location": profile["death_info"].get("location", "Unknown"),
                    "Facts": facts_str,
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