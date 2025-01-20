import csv
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import *
import undetected_chromedriver as uc

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

def process_family_member(driver, member):
    """Process individual family member with improved navigation handling."""
    original_url = driver.current_url
    
    try:
        print(f"\nProcessing: {member.text}")
        
        # Scroll and click member name
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            member
        )
        time.sleep(1)
        
        try:
            member.click()
        except:
            driver.execute_script("arguments[0].click();", member)
        
        print("Successfully clicked member name")
        time.sleep(2)
        
        # Find and click profile link
        profile_selectors = [
            "//a[contains(text(), 'Profile')]",
            "a[data-testid='person-profile-link']",
            "a.profileLink",
            "//a[contains(@href, '/person/')]"
        ]
        
        profile_link = None
        for selector in profile_selectors:
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
        
        if profile_link:
            # Store the URL we're about to navigate to
            profile_url = profile_link.get_attribute('href')
            print(f"Profile URL: {profile_url}")
            
            # Click the profile link
            try:
                profile_link.click()
            except:
                driver.execute_script("arguments[0].click();", profile_link)
            
            print("Clicked profile link")
            time.sleep(3)
            
            # Check if we're on a new URL
            current_url = driver.current_url
            if current_url != original_url:
                print("Successfully navigated to profile page")
                
                # Wait for profile page elements
                try:
                    # Wait for Facts tab
                    facts_tab = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='facts-tab']"))
                    )
                    facts_tab.click()
                    print("Clicked Facts tab")
                    time.sleep(2)
                    
                    # Extract timeline data
                    timeline_items = driver.find_elements(By.CSS_SELECTOR, ".timeline-item, .fact-row")
                    
                    profile_data = {
                        "name": member.text,
                        "birth_info": {},
                        "death_info": {},
                        "facts": [],
                        "sources": []
                    }
                    
                    for item in timeline_items:
                        try:
                            fact_type = item.find_element(By.CSS_SELECTOR, ".fact-type").text.strip()
                            fact_date = item.find_element(By.CSS_SELECTOR, ".fact-date").text.strip()
                            fact_location = item.find_element(By.CSS_SELECTOR, ".fact-location").text.strip()
                            
                            fact = {
                                "type": fact_type,
                                "date": fact_date,
                                "location": fact_location
                            }
                            
                            if "Birth" in fact_type:
                                profile_data["birth_info"] = {"date": fact_date, "location": fact_location}
                            elif "Death" in fact_type:
                                profile_data["death_info"] = {"date": fact_date, "location": fact_location}
                            
                            profile_data["facts"].append(fact)
                            
                        except Exception as e:
                            print(f"Error extracting fact: {str(e)}")
                            continue
                    
                    # Navigate back to tree view
                    print("Navigating back to tree view")
                    driver.get(original_url)
                    time.sleep(3)
                    
                    return profile_data
                    
                except Exception as e:
                    print(f"Error extracting profile data: {str(e)}")
                    driver.get(original_url)
                    return None
            else:
                print("Failed to navigate to profile page")
                return None
        else:
            print("Could not find profile link")
            return None
            
    except Exception as e:
        print(f"Error processing member: {str(e)}")
        # Try to recover by returning to tree view
        driver.get(original_url)
        time.sleep(3)
        return None

def extract_family_data(driver):
    """Extract data for all family members with improved navigation."""
    all_profile_data = []
    tree_url = driver.current_url
    
    try:
        print("Waiting for family tree to load...")
        time.sleep(10)
        
        # Find all member elements
        member_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".nodeTitle"))
        )
        
        print(f"Found {len(member_elements)} family members")
        
        for i, member in enumerate(member_elements, 1):
            try:
                print(f"\nProcessing member {i}/{len(member_elements)}")
                
                # Ensure we're on the tree view
                if driver.current_url != tree_url:
                    print("Navigating back to tree view")
                    driver.get(tree_url)
                    time.sleep(3)
                    
                    # Refresh member elements
                    member_elements = driver.find_elements(By.CSS_SELECTOR, ".nodeTitle")
                    member = member_elements[i-1]
                
                profile_data = process_family_member(driver, member)
                
                if profile_data:
                    all_profile_data.append(profile_data)
                    print(f"Successfully processed {profile_data['name']}")
                
                time.sleep(2)
                
            except StaleElementReferenceException:
                print("Member element became stale, refreshing elements...")
                member_elements = driver.find_elements(By.CSS_SELECTOR, ".nodeTitle")
                continue
            except Exception as e:
                print(f"Error processing member {i}: {str(e)}")
                continue
    
    except Exception as e:
        print(f"Error in extract_family_data: {str(e)}")
    
    return all_profile_data
def save_to_csv(data, filename):
    """Save extracted data to CSV with error handling."""
    if not data:
        print("No data to save to CSV")
        return
        
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
                writer.writerow({
                    "Name": profile.get("name", "Unknown"),
                    "Birth Date": profile.get("birth_info", {}).get("date", "Unknown"),
                    "Birth Location": profile.get("birth_info", {}).get("location", "Unknown"),
                    "Death Date": profile.get("death_info", {}).get("date", "Unknown"),
                    "Death Location": profile.get("death_info", {}).get("location", "Unknown"),
                    "Facts": "; ".join([f"{fact['type']}: {fact['date']} - {fact['location']}" 
                                     for fact in profile.get("facts", [])]),
                    "Sources": "; ".join(profile.get("sources", []))
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