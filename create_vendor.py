import re
import os
import time
import json
import tkinter as tk
from tkinter import StringVar
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

def submit_form(email, password, vendor_name, pin_no):
    """Automate the vendor creation process and handle potential errors."""
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
            page.goto("https://bctest.dayliff.com/BC160/?company=KENYA&bookmark=21%3bFwAAAAJ7%2f0QAIABIACAATA%3d%3d&page=27&dc=0")
            time.sleep(5)

            frame.get_by_role("menuitem", name="New", exact=True).click()
            time.sleep(5)
            frame.get_by_label("Description, Vendor LOCAL").click()
            time.sleep(2)

            # Extract vendor number dynamically and save it
            header = frame.locator("div[role='heading'][class*='title---'][aria-level='2']").first

            # Wait for up to 10 seconds for the header to appear
            header.wait_for(timeout=10000)

            # Extract the text content of the header
            text_content = header.text_content()
            print(f"Text content of the header: {text_content}")

            # Use regex to find the pattern "V" followed by digits (e.g., V13691)
            match = re.search(r"V\d+", text_content)
    
            if match:
                vendor_no = match.group(0)  # Extract the vendor number (e.g., V13694)
                print(f"Extracted vendor number: {vendor_no}")
        
            # Save the vendor number to JSON
                extracted_data = {"vendor_no": vendor_no}
                save_extracted_data(extracted_data)
                print(f"Vendor number extracted and saved: {vendor_no}")
            else:
                print("Vendor number not found.")
                vendor_no = None

            # Fill in vendor name
            frame.get_by_label("Name, (Blank)").click()
            frame.get_by_label("Name, (Blank)").fill(vendor_name)
            frame.get_by_label("Name, (Blank)").press("Enter")
            time.sleep(2)

            frame.get_by_label("General, Show more").click()
            frame.get_by_role("button", name="Toggle FactBox").click()
            time.sleep(2)

            frame.get_by_role("button", name="Registration").click()
            frame.get_by_role("textbox", name="PIN No., (Blank)").click()
            frame.get_by_role("textbox", name="PIN No., (Blank)").fill(pin_no)
            frame.get_by_role("textbox", name="PIN No., (Blank)").press("Enter")
            time.sleep(2)

            # Save success screenshot
            take_screenshot(page, "Vendor_Creation_Success")

            print("Vendor created successfully!")

        except Exception as e:
            error_screenshot = take_screenshot(page, "Error")
            print(f"An error occurred: {str(e)}. Screenshot saved at {error_screenshot}.")

        finally:
            browser.close()

def on_submit():
    """Handle the form submission from the UI."""
    email = email_var.get()
    password = password_var.get()
    vendor_name = vendor_name_var.get()
    pin_no = pin_no_var.get()

    # Save inputs to JSON
    inputs = {
        "email": email,
        "password": password,
        "vendor_name": vendor_name,
        "pin_no": pin_no,
    }
    save_inputs(inputs)

    # Run the automation process
    submit_form(email, password, vendor_name, pin_no)

# Tkinter UI setup
root = tk.Tk()
root.title("Vendor Entry")
root.geometry("400x350")

# Variables for user inputs
email_var = StringVar()
password_var = StringVar()
vendor_name_var = StringVar()
pin_no_var = StringVar()

# Creating the form
tk.Label(root, text="Email:").pack()
tk.Entry(root, textvariable=email_var).pack()
tk.Label(root, text="Password:").pack()
tk.Entry(root, textvariable=password_var, show="*").pack()
tk.Label(root, text="Vendor Name:").pack()
tk.Entry(root, textvariable=vendor_name_var).pack()
tk.Label(root, text="PIN No:").pack()
tk.Entry(root, textvariable=pin_no_var).pack()

tk.Button(root, text="Submit", command=on_submit).pack()

root.mainloop()
