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

def save_inputs(data, filename="inputs.json"):
    """Save user inputs into a JSON file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    print(f"User inputs saved to {filename}.")

def save_extracted_data(new_data, filename="extracted_data.json"):
    """Save extracted data into a JSON file, updating without erasing previous entries."""
    if os.path.exists(filename):
        # Load existing data if the file exists
        with open(filename, "r") as f:
            try:
                data = json.load(f)
                # Ensure the data is a list
                if not isinstance(data, list):
                    data = [data]  # Convert dictionary or single entry to a list
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    
    # Append the new data
    data.append(new_data)

    # Save the updated data
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
                    return data[-1]  # Return the last entry
            except json.JSONDecodeError:
                print("Error reading JSON file. Returning None.")
    return None  # Return None if the file doesn't exist or is empty

def load_inputs(filename="inputs.json"):
    """Load user inputs from the JSON file."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Error reading inputs JSON file.")
    return None  # Return None if the file doesn't exist or is empty

def load_extracted_data(filename="extracted_data.json"):
    """Load extracted data from the JSON file."""
    return get_latest_entry(filename)

def submit_form():
    """Automate the vendor creation process and handle potential errors."""
    # Load user inputs and extracted data
    inputs = load_inputs()
    extracted_data = load_extracted_data()

    if not inputs or not extracted_data:
        print("Missing required data from inputs or extracted_data.")
        return

    email = inputs["email"]
    password = inputs["password"]
    vendor_no = extracted_data.get("vendor_no")

    if not vendor_no:
        print("Vendor number not found in extracted data.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            # Login to the platform
            page.goto("https://login.microsoftonline.com/dayliffCloud.onmicrosoft.com/wsfed?wa=wsignin1.0&wtrealm=https%3a%2f%2fdayliffCloud.onmicrosoft.com%2fbusinesscentral&wreply=https%3a%2f%2fbctest.dayliff.com%2fBC160%2fSignIn%3fReturnUrl%3d%252fBC160%252f")
            page.get_by_placeholder("someone@example.com").fill(email)
            page.get_by_role("button", name="Next").click()
            page.get_by_placeholder("Password").fill(password)
            page.get_by_role("button", name="Sign in").click()
            page.get_by_role("button", name="No").click()
            page.goto("https://bctest.dayliff.com/BC160/")

            # Navigate to vendor creation
            frame = page.frame_locator("iframe[title='Main Content']").first
            page.goto("https://bctest.dayliff.com/BC160/?company=KENYA&bookmark=29%3busMAAAJ7%2f1AAUgAwADAAMAAyADUAMwA3&page=50152&dc=0")
            time.sleep(5)

            frame.get_by_role("menuitem", name="New").click()
            time.sleep(5)
            frame.get_by_label("Requisition Type, (Blank)").select_option("1")
            time.sleep(5)

            frame.get_by_label("General, Show more").click()
            frame.get_by_role("button", name="Toggle FactBox").click()
            time.sleep(5)

            frame.get_by_role("textbox", name="Description, (Blank)").click()

            header = frame.locator("div[role='heading'][class*='title---'][aria-level='2']").first

            # Wait for up to 10 seconds for the header to appear
            header.wait_for(timeout=10000)

            # Extract the text content of the header
            text_content = header.text_content()
            print(f"Text content of the header: {text_content}")

            # Use regex to find the pattern "RFQ" followed by digits (e.g., RFQ007686)
            match = re.search(r"RFQ\d+", text_content)
    
            if match:
                RFQ_no = match.group(0)  # Extract the RFQ number (e.g., RFQ007686)
                print(f"Extracted RFQ number: {RFQ_no}")
        
                # Save the RFQ number to JSON with the key "RFQ_no"
                extracted_data = {"RFQ_no": RFQ_no}
                save_extracted_data(extracted_data)
                print(f"RFQ number extracted and saved: {RFQ_no}")
            else:
                print("RFQ number not found.")
                RFQ_no = None

            frame.get_by_role("textbox", name="Description, (Blank)").click()
            frame.get_by_role("textbox", name="Description, (Blank)").fill("testing rfq proceess\n")
            time.sleep(2)

            frame.get_by_role("row", name="  Location Code, 22010 0 0.").get_by_label("Type, (Blank)", exact=True).click()
            frame.get_by_role("row", name="  Location Code, 22010 0 0.").get_by_label("Type, (Blank)", exact=True).select_option("20")
            time.sleep(2)

            frame.get_by_role("combobox", name="No., (Blank)", exact=True).click()
            frame.get_by_role("combobox", name="No., (Blank)", exact=True).fill("20928")
            time.sleep(2)



            frame.get_by_label("Comments, (Blank)").click()
            time.sleep(2)

            frame.get_by_label("Quantity,", exact=True).fill("1")
            frame.get_by_label("Quantity,", exact=True).press("Enter")
            time.sleep(2)
            frame.get_by_label("Source Doc Type,", exact=True).select_option("4")

            frame.get_by_role("combobox", name="Source No., (Blank)").click()
            frame.get_by_role("combobox", name="Source No., (Blank)").fill("J066872")
            frame.get_by_label("Comments, (Blank)").click()

            frame.get_by_label("Source Line No.,", exact=True).click()
            frame.get_by_label("Source Line No.,", exact=True).fill("1010")
            time.sleep(2)

            frame.get_by_role("menuitem", name="Process").click()
            frame.get_by_role("menuitem", name="Send to Procurement").click()
            time.sleep(5)

            take_screenshot(page, "RFQ_created")
            frame.get_by_role("button", name="Yes").click()
            time.sleep(5)
            
            print("RFQ created successfully!")

        except Exception as e:
            error_screenshot = take_screenshot(page, "Error")
            print(f"An error occurred: {str(e)}. Screenshot saved at {error_screenshot}.")

        finally:
            browser.close()

if __name__ == "__main__":
    submit_form()
