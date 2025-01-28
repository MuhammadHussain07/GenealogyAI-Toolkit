import csv
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURATIONS ---
ANCESTRY_URL = "https://www.ancestry.com/signin"
TREE_PAGE_URL = "https://www.ancestry.com/family-tree/tree/191247410/family?cfpid=382485586551"
EMAIL = "***********@gmail.com"
PASSWORD = "*******"
CSV_FILENAME = "ancestry_family_data.csv"

def initialize_driver():
    """Initialize undetected Chrome driver with performance options."""
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options)
    return driver

def save_to_csv(data, filename):
    """Save data to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "DOB", "Place of Birth", "Death Status", "Timeline", "Sources", "Profile Link"])
        writer.writerows(data)

def extract_modal_data(driver):
    """Extract data from the modal that appears after clicking a name."""
    try:
        print("[INFO] Waiting for modal to appear...")
        modal = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.treeProfileInfoWrapper"))
        )

        # Extract Name
        name = modal.find_element(By.CSS_SELECTOR, "span.treeProfileInfoName").text.strip()

        # Extract DOB and Place of Birth
        dob_text = modal.find_element(By.CSS_SELECTOR, "div.treeProfileInfoDatePlace").text.strip()
        dob, place_of_birth = "Unknown", "Unknown"
        if "B:" in dob_text:
            dob_info = dob_text.split("B:")[-1].strip()
            dob = dob_info.split(",")[0].strip()
            place_of_birth = dob_info.split(",")[1].strip() if "," in dob_info else "Unknown"

        # Extract Death Status
        death_status = "Living"
        if "D:" in dob_text:
            death_status = dob_text.split("D:")[-1].strip()

        print("[SUCCESS] Modal data extracted!")
        return name, dob, place_of_birth, death_status

    except Exception as e:
        print(f"[ERROR] Failed to extract modal data: {e}")
        return "Error", "", "", ""

def extract_profile_data(driver):
    """Extract additional data from the profile page."""
    try:
        print("[INFO] Extracting profile information...")

        # Wait for the profile page to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.personFacts"))
        )

        # Extract Timeline Data
        timeline_elements = driver.find_elements(By.CSS_SELECTOR, "div.timelineSection div")
        timeline = [el.text.strip() for el in timeline_elements if el.text.strip()]

        # Extract Sources Data
        sources_elements = driver.find_elements(By.CSS_SELECTOR, "div.sourcesSection div")
        sources = [el.text.strip() for el in sources_elements if el.text.strip()]

        print("[SUCCESS] Profile information extracted!")
        return " | ".join(timeline), " | ".join(sources)

    except Exception as e:
        print(f"[ERROR] Failed to extract profile data: {e}")
        return "", ""

def extract_family_data(driver):
    """Extracts family tree data."""
    family_data = []
    try:
        print("[INFO] Waiting for family tree members...")
        members = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.nodeTitle.notranslate"))
        )
        
        for i, member in enumerate(members):
            print(f"[INFO] Clicking on family member {i + 1}...")
            driver.execute_script("arguments[0].scrollIntoView(true);", member)
            member.click()

            # Extract data from the modal
            name, dob, place_of_birth, death_status = extract_modal_data(driver)

            # Click the Profile button
            print("[INFO] Clicking the Profile button...")
            profile_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.treeProfileInfoViewProfile"))
            )
            profile_link = profile_button.get_attribute("href")  # Get profile link
            profile_button.click()

            # Extract additional profile data
            timeline, sources = extract_profile_data(driver)

            # Append all extracted data
            family_data.append([name, dob, place_of_birth, death_status, timeline, sources, profile_link])

            # Navigate back to the family tree page
            driver.back()
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.nodeTitle.notranslate"))
            )

    except Exception as e:
        print(f"[ERROR] Failed to extract family data: {e}")

    return family_data

def login_and_navigate(driver):
    """Logs in to ancestry.com and navigates to the family tree page."""
    try:
        print("[INFO] Opening Ancestry login page...")
        driver.get(ANCESTRY_URL)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "username")))

        print("[INFO] Entering credentials...")
        driver.find_element(By.ID, "username").send_keys(EMAIL)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()

        WebDriverWait(driver, 30).until(lambda d: "signin" not in d.current_url.lower())
        print("[SUCCESS] Login successful!")

        print("[INFO] Navigating to the family tree page...")
        driver.get(TREE_PAGE_URL)
        time.sleep(3)

        family_data = extract_family_data(driver)
        save_to_csv(family_data, CSV_FILENAME)
        print(f"[SUCCESS] Data saved to {CSV_FILENAME}!")

    except Exception as e:
        print(f"[ERROR] An error occurred during login or navigation: {e}")

if __name__ == "__main__":
    driver = initialize_driver()
    try:
        login_and_navigate(driver)
    finally:
        driver.quit()
