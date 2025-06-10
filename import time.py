import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from faker import Faker
import random

# Set up Faker for Dutch names and phone numbers
fake = Faker('nl_NL')

# Website URL
url = "https://www.gloudemans.nl/kaaswiel/?gf_protect_submission=1"
my_email = "sharnevesht@gmail.com"  # Fixed email address

# Function to generate random Dutch name and phone number
def get_fake_dutch_info():
    name = fake.name()
    phone = fake.phone_number()
    return name, phone

# Function to submit one guess
def submit_cheese_guess(weight):
    driver = webdriver.Chrome()
    driver.get(url)

    time.sleep(3)  # Wait for page to load

    # Get fake name and phone
    name, phone = get_fake_dutch_info()

    # Fill the form
    driver.find_element(By.ID, "input_9_1").send_keys(name) #extracted from the WebMode F12
    driver.find_element(By.ID, "input_9_3").send_keys(phone) #extracted from the WebMode F12
    driver.find_element(By.ID, "input_9_4").send_keys(my_email) #extracted from the WebMode F12
    driver.find_element(By.ID, "input_9_5").send_keys(str(weight)) #extracted from the WebMode F12

    # Submit the form
    driver.find_element(By.ID, "gform_submit_button_9").click()

    time.sleep(2)  # Wait for submission
    driver.quit()

    print(f"Submitted {weight}g as {name} ({phone})")

# Try a small range of weights for demo
for weight in range(7000, 7005):
    submit_cheese_guess(weight)
    time.sleep(random.uniform(2, 3))  # Small delay between submissions
