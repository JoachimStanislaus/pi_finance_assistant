from collections.abc import Mapping
import os
import csv
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import json
import telebot
from datetime import datetime

load_dotenv()

base_tele_ids = os.getenv("BASE_TELE_USER_ID")

bot = telebot.TeleBot(os.getenv("TELE_API_KEY"))
TelegramUsers = json.loads(base_tele_ids) if base_tele_ids else []

#Get today's date in integer format
def today_date():
    # Creating a datetime object so we can test.
    a = datetime.now()
    # Converting a to string in the desired format (YYYYMMDD) using strftime
    # and then to int.
    a = str(a.strftime('%d/%m/%y'))
    return a

#Checks if User is Authorized or not
def UserCheck(message):
    if message.from_user.id in TelegramUsers:    
        return True
    else:
        bot.reply_to(message, "Unauthorized User")
        return False

# Function to create and manage expenses.csv file
def create_csv_file_if_not_exists(file_path,headers):
    """Creates/updates the specified CSV file with proper headers and data structure."""
    try:
        # Check if file exists and has data
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r', newline='') as f:
                reader = csv.reader(f)
                existing_data = list(reader)
                if not existing_data or headers not in existing_data[0]:
                    # File is empty or headers missing, add them back
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        # Preserve any existing data rows
                        for row in existing_data[1:]:
                            writer.writerow(row)
        else:
            # Create new file with headers
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        return True
        
    except Exception as e:
        return False

def add_data_to_csv(file_path, data: Mapping[str, str], headers: list) -> bool:
    """Adds a new record to the CSV file."""
    create_csv_file_if_not_exists(file_path, headers)
    try:
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data.values())
        return True
    except Exception as e:
        print(f"✗ Error adding data: {e}")
        return False


def append_expense_to_csv(file_path, expense: Mapping[str, str]) -> bool:
    """Appends a new expense record to the CSV file."""
    EXPENSE_FIELDS = (
            "Date", 
            "Category", 
            "Description", 
            "Amount",
            "isShared",
            "User",
        )    
    try:
        add_data_to_csv(file_path, expense, EXPENSE_FIELDS)
        return True
        
    except Exception as e:
        print(f"✗ Error appending expense: {e}")
        return False

def resolve_fields_from_description(description):
    """Resolves category, isShared from a given description string."""
    from classifier.predict import predict_category
    
    # Classify the expense using the trained model
    category, confidence = predict_category(description)

    # If category is Groceries, bills then it is shared
    if category in ['Groceries', "Dogs"]:
        is_shared = True
    elif category == 'Bills' and any(keyword.lower() in description.lower() for keyword in ('thames water', 'council tax', 'octopus', 'electricity', 'heating', 'water', 'wifi','hyperoptic')):
        is_shared = True
    else:
        shared_keywords = ('shared', 'split', 'half', 'joint', 'nicole','joachim')
        # if nicole or joachim is in the description and treat is not in the description then it is shared
        if any(keyword.lower() in description.lower() for keyword in ('nicole', 'joachim')) and 'treat' not in description.lower():
            is_shared = True
        else:
            is_shared = any(keyword.lower() in description.lower() for keyword in shared_keywords)
    
    return category, str(is_shared)

def get_amount(message, expense):
    try:
        amount = float(message.text)
        expense['amount'] = amount

        msg = bot.send_message(message.chat.id, "What is the description?")
        bot.register_next_step_handler(msg, get_description, expense)

    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "Please enter a valid amount, e.g. 12.50"
        )
        bot.register_next_step_handler(msg, get_amount, expense)


def get_description(message, expense):
    description = message.text
    expense['description'] = description
    get_expense(message, expense)


def get_expense(message, expense):
    # Resolve category and isShared from description
    category, isShared = resolve_fields_from_description(expense.get('description'))
    expense['category'] = category
    expense['isShared'] = isShared

    # Get today's date
    expense['date'] = today_date()

    # Get username
    expense['user'] = message.from_user.first_name

    # Append to CSV
    if append_expense_to_csv('data/expenses.csv', expense):
        bot.send_message(message.chat.id, "Expense added successfully!")
    else:
        bot.send_message(message.chat.id, "Failed to add expense. Please try again.")

def get_take_home_pay(message, profile_file_path, PROFILE_HEADERS):
    try:
        take_home_pay = float(message.text)
        # Update the profile.csv with the take home pay and date added
        date_added = today_date()
        add_data_to_csv(profile_file_path, {"Name": message.from_user.first_name, "Take Home Pay": take_home_pay, "Date_added": date_added}, PROFILE_HEADERS)
        bot.send_message(message.chat.id, "Profile updated successfully!")
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "Please enter a valid amount for take home pay, e.g. 2500.00"
        )
        bot.register_next_step_handler(msg, get_take_home_pay, profile_file_path, PROFILE_HEADERS)

# Setup/Edit Profile command
@bot.message_handler(commands=['setup_profile', 'edit_profile'])
def setup_profile(message):
    if UserCheck(message) == True:
        profile_file_path = 'data/profile.csv'
        PROFILE_HEADERS = ("Name", "Take Home Pay","Date_added")
        # get take home pay from user
        msg = bot.send_message(message.chat.id, "What is your take home pay?")
        bot.register_next_step_handler(msg, get_take_home_pay, profile_file_path, PROFILE_HEADERS)

@bot.message_handler(commands=['profile'])
def get_profile(message):
    if UserCheck(message) == True:
        profile_file_path = 'data/profile.csv'
        if os.path.exists(profile_file_path):
            with open(profile_file_path, 'r') as f:
                reader = csv.DictReader(f)
                profile_data = list(reader)
                if profile_data:
                    profile_data = sorted(profile_data, key=lambda x: (x['Name'], x['Date_added']), reverse=True)
                    profile_data = [p for p in profile_data if p['Name'] == message.from_user.first_name]
                    if not profile_data:
                        bot.send_message(message.chat.id, "Profile not found for your user. Please set up your profile using /setup_profile.")
                        return
                    latest_profile = profile_data[-1]
                    bot.send_message(
                        message.chat.id,
                        f"Name: {latest_profile['Name']}\nTake Home Pay: {latest_profile['Take Home Pay']}\nDate Added: {latest_profile['Date_added']}"
                    )
                else:
                    bot.send_message(message.chat.id, "Profile is empty. Please set up your profile using /setup_profile.")
        else:
            bot.send_message(message.chat.id, "Profile not found. Please set up your profile using /setup_profile.")

# Retrieve all data from data folder and return file to chat
@bot.message_handler(commands=['get_all_data'])
def retrieve_all_data(message):
    if UserCheck(message) == True:
        try:
            for file in os.listdir('data'):
                # return any file in data
                if file.endswith('.csv'):
                    with open(os.path.join('data', file), 'rb') as f:
                        bot.send_document(message.chat.id, f)
        except Exception as e:
            bot.send_message(message.chat.id, f"Error retrieving data: {e}")

#Handle '/add' command to add a new expense record
@bot.message_handler(commands=['add'])
def add_expense(message):
    if UserCheck(message) == True:
        expense = {}
        msg = bot.send_message(message.chat.id, "What is the amount?")
        bot.register_next_step_handler(msg, get_amount, expense)

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    if UserCheck(message) == True:
            bot.send_message(message.chat.id, "Welcome {}\nUser: {}  ".format(message.from_user.first_name,message.from_user.id))
            bot.reply_to(message, "/start & /help to start and get commands\n/add to add record")

print("I'm listening...")
bot.infinity_polling()
