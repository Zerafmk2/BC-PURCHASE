import re
import os
import time
import json
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page

load_dotenv()  # Load environment variables from .env file

def take_screenshot(page: Page, step_name: str) -> str:
    """Take a screenshot and save it with a specified step name."""
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    screenshot_path = os.path.join(screenshot_dir, f"{step_name}_{timestamp}.png")
    page.screenshot(path=screenshot_path)
    print(f"Screenshot taken: {screenshot_path}")
    return screenshot_path

def save_extracted_data(new_data, filename="extracted_data.json"):
    """Save extracted data into a JSON file, updating without erasing previous entries."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]  # Ensure data is stored as a list
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    
    data.append(new_data)
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Extracted data updated in {filename}.")

def get_latest_entry(filename="extracted_data.json"):
    """Retrieve the latest entry from the JSON file."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data[-1]  # Return the most recent entry
            except json.JSONDecodeError:
                print("Error reading JSON file.")
    return None  # Return None if file doesn't exist or is empty

def submit_form():
    """Automate the RFQ process and retrieve the RFQ_no from extracted data."""
    # Load extracted data
    extracted_data = get_latest_entry()
    
    if not extracted_data:
        print("No data found in extracted_data.json.")
        return
    
    RFQ_no = extracted_data.get("RFQ_no")
    
    if not RFQ_no:
        print("RFQ number not found in the extracted data.")
        return
    
    print(f"Using RFQ_no from extracted data: {RFQ_no}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Login to the platform
            page.goto("https://login.microsoftonline.com/dayliffCloud.onmicrosoft.com/wsfed?wa=wsignin1.0&wtrealm=https%3a%2f%2fdayliffCloud.onmicrosoft.com%2fbusinesscentral&wreply=https%3a%2f%2fbctest.dayliff.com%2fBC160%2fSignIn%3fReturnUrl%3d%252fBC160%252f")
            page.get_by_placeholder("someone@example.com").fill(os.getenv("EMAIL"))
            page.get_by_role("button", name="Next").click()
            page.get_by_placeholder("Password").fill(os.getenv("PASSWORD"))
            page.get_by_role("button", name="Sign in").click()
            page.get_by_role("button", name="No").click()
            page.goto("https://bctest.dayliff.com/BC160/")

            # Example of utilizing the RFQ_no in the automation process
            frame = page.frame_locator("iframe[title='Main Content']").first
            page.goto("https://bctest.dayliff.com/BC160/?company=KENYA&bookmark=29%3busMAAAJ7%2f1AAUgAwADAAMAAyADUAMwA3&page=50152&dc=0")

            frame.get_by_text("Search").click()
            frame.get_by_placeholder("Search").fill(RFQ_no)

            frame.get_by_role("button", name=f"No., {RFQ_no}").click()
            
            frame.get_by_label("General, Show more").click()
            frame.get_by_role("button", name="Toggle FactBox").click()

            frame.get_by_role("menuitem", name="Request Approval").click()
            


            take_screenshot(page, f"RFQ_page_{RFQ_no}")

            print(f"RFQ approved performed successfully: {RFQ_no}")

        except Exception as e:
            error_screenshot = take_screenshot(page, "Error")
            print(f"An error occurred: {str(e)}. Screenshot saved at {error_screenshot}.")

        finally:
            browser.close()

if __name__ == "__main__":
    submit_form()