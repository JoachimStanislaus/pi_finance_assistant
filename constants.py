import os
import json

from dotenv import load_dotenv
import telebot

load_dotenv()
base_tele_ids = os.getenv("BASE_TELE_USER_ID")
TelegramUsers = json.loads(base_tele_ids) if base_tele_ids else []
bot = telebot.TeleBot(os.getenv("TELE_API_KEY"))

PROFILE_HEADERS = ("Name", "Take Home Pay","Date_added")
PROFILE_FILE_PATH = 'data/profile.csv'
EXPENSE_FILE_PATH = 'data/expenses.csv'
EXPENSE_FIELDS = (
        "Date", 
        "Category", 
        "Description", 
        "Amount",
        "isShared",
        "User",
        "expense_id",
    )
CATEGORIES = (
    "Eating Out",
    "Groceries",
    "Transportation",
    "Travel",
    "Social",
    "Bills",
    "Shopping",
    "Dogs",
    "Gifts",
    "Grooming",
    "Health/Medical",
    "Learning"
)