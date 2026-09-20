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
        print(message.from_user.id)
        return False

# Function to create and manage expenses.csv file
def create_csv_file(file_name):
    """Creates/updates the specified CSV file with proper headers and data structure."""
    csv_path = file_name

    # Define CSV headers for expense tracking
    headers = [
        "Date", 
        "Category", 
        "Description", 
        "Amount",
        "isShared",
        "User",
    ]
            
    try:
        # Check if file exists and has data
        if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
            with open(csv_path, 'r', newline='') as f:
                reader = csv.reader(f)
                existing_data = list(reader)
                if not existing_data or headers not in existing_data[0]:
                    # File is empty or headers missing, add them back
                    with open(csv_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        # Preserve any existing data rows
                        for row in existing_data[1:]:
                            writer.writerow(row)
        else:
            # Create new file with headers
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        return True
        
    except Exception as e:
        return False



def append_expense_to_csv(file_name, expense: Mapping[str, str]) -> bool:
    """Appends a new expense record to the CSV file."""
    csv_path = file_name
    
    try:
        with open(csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                expense.get('date'),
                expense.get('category'),
                expense.get('description'),
                expense.get('amount'),
                expense.get('isShared'),
                expense.get('user')
            ])
        
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
    if append_expense_to_csv('expenses.csv', expense):
        bot.send_message(message.chat.id, "Expense added successfully!")
    else:
        bot.send_message(message.chat.id, "Failed to add expense. Please try again.")

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
    print("User: {}  ".format(message.from_user.id))
    if UserCheck(message) == True:
            bot.send_message(message.chat.id, "Welcome {}\nUser: {}  ".format(message.from_user.first_name,message.from_user.id))
            bot.reply_to(message, "/start & /help to start and get commands\n/add to add record")
    else:
        print("Unauthorized User: {}  ".format(message.from_user.id))
        pass

print("I'm listening...")
bot.infinity_polling()
