import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

# --- CONFIGURATIONS ---
ANCESTRY_URL = "https://www.ancestry.com/signin"
TREE_PAGE_URL = "https://www.ancestry.com/family-tree/tree/191247410/family?cfpid=382485586551"
EMAIL = "anthonymdavenport@gmail.com"
PASSWORD = "************"

# --- STEP 1: Login ---
def selenium_login():
    print("[INFO] Launching Selenium...")
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options)

    try:
        driver.get(ANCESTRY_URL)

        print("[INFO] Waiting for login form...")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username")))

        # Fill login credentials
        driver.find_element(By.ID, "username").send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()

        print("[INFO] Waiting for login to complete...")
        WebDriverWait(driver, 30).until(EC.url_contains("ancestry.com"))

        print("[SUCCESS] Login successful!")
        return driver

    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        driver.quit()
        return None

# --- STEP 2: Extract Timeline and Sources Data ---
def extract_profile_data(driver):
    print("[INFO] Extracting profile data...")
    data = {}

    try:
        # Wait for timeline section
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "timeline")))
        timeline_items = driver.find_elements(By.CSS_SELECTOR, "#timeline .event")

        timeline_data = []
        for item in timeline_items:
            try:
                event_title = item.find_element(By.CLASS_NAME, "title").text.strip()
                event_date = item.find_element(By.CLASS_NAME, "date").text.strip()
                timeline_data.append({"Event": event_title, "Date": event_date})
            except Exception as e:
                print(f"[WARNING] Failed to extract timeline event: {e}")

        data["Timeline"] = timeline_data

        # Wait for sources section
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "sources")))
        sources_items = driver.find_elements(By.CSS_SELECTOR, "#sources .source-item")

        sources_data = []
        for item in sources_items:
            try:
                source_title = item.find_element(By.CLASS_NAME, "source-title").text.strip()
                source_details = item.find_element(By.CLASS_NAME, "source-details").text.strip()

                # If a source file needs to be opened
                try:
                    view_link = item.find_element(By.TAG_NAME, "a")
                    view_link.click()
                    time.sleep(random.uniform(2, 5))  # Avoid detection

                    # Extract additional source details
                    additional_details = driver.find_element(By.CSS_SELECTOR, "div.source-view").text.strip()
                    sources_data.append({"Title": source_title, "Details": source_details, "Additional Details": additional_details})

                    driver.back()
                    time.sleep(random.uniform(2, 4))
                except Exception:
                    sources_data.append({"Title": source_title, "Details": source_details})
            except Exception as e:
                print(f"[WARNING] Failed to extract source item: {e}")

        data["Sources"] = sources_data

    except Exception as e:
        print(f"[ERROR] Failed to extract profile data: {e}")

    return data

# --- MAIN FUNCTION ---
def main():
    driver = selenium_login()
    if not driver:
        print("[ERROR] Selenium login failed. Exiting.")
        return

    print("[INFO] Navigating to tree page...")
    driver.get(TREE_PAGE_URL)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span.nodeTitle.notranslate"))
    )

    try:
        # Click on the first person's name
        first_person = driver.find_element(By.CSS_SELECTOR, "span.nodeTitle.notranslate")
        first_person.click()
        time.sleep(random.uniform(2, 5))

        # Click on the profile button
        profile_button = driver.find_element(By.CSS_SELECTOR, "button.profile-button")
        profile_button.click()
        time.sleep(random.uniform(2, 5))

        # Extract profile data
        profile_data = extract_profile_data(driver)
        print("[INFO] Extracted data:", profile_data)

        # Save the data to CSV
        with open("ancestry_profile_data.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Section", "Data"])
            for section, items in profile_data.items():
                for item in items:
                    writer.writerow([section, item])

        print("[SUCCESS] Data saved to ancestry_profile_data.csv!")

    except Exception as e:
        print(f"[ERROR] Failed to extract data: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
