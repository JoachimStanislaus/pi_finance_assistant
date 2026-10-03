from constants import bot, EXPENSE_FILE_PATH, PROFILE_FILE_PATH, CATEGORIES, PROFILE_HEADERS, bot
import os
import csv
from expenses import get_amount
from helper import add_data_to_csv, read_csv, today_date, add_data_to_csv, UserCheck
from jobs import execute_jobs
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from datetime import datetime

from smart_query_router import route_query


def get_take_home_pay(message, PROFILE_HEADERS):
    try:
        take_home_pay = float(message.text)
        # Update the profile.csv with the take home pay and date added
        date_added = today_date()
        add_data_to_csv(PROFILE_FILE_PATH, {"Name": message.from_user.first_name, "Take Home Pay": take_home_pay, "Date_added": date_added}, PROFILE_HEADERS)
        bot.send_message(message.chat.id, "Profile updated successfully!")
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "Please enter a valid amount for take home pay, e.g. 2500.00"
        )
        bot.register_next_step_handler(msg, get_take_home_pay, PROFILE_HEADERS)




# Edit Expense command
@bot.message_handler(commands=['edit'])
def edit_expense(message):
    if UserCheck(message) == True:
        try:
            command_parts = message.text.split()

            if len(command_parts) < 2:
                bot.send_message(
                    message.chat.id,
                    "Please provide the expense ID to edit.\n"
                    "Usage: /edit <expense_id>"
                )
                return

            expense_id = command_parts[1]

            # Read expenses
            df = read_csv(EXPENSE_FILE_PATH)

            # Convert expense IDs to strings
            df['expense_id'] = df['expense_id'].astype(str)
            expense_id = str(expense_id)

            # Find the expense
            matching_expenses = df[df['expense_id'] == expense_id]

            if matching_expenses.empty:
                bot.send_message(
                    message.chat.id,
                    f"No expense found with ID: {expense_id}"
                )
                return

            expense_to_edit = matching_expenses.iloc[0]

            # Create category buttons
            markup = InlineKeyboardMarkup(row_width=2)

            buttons = []

            for category in CATEGORIES:
                buttons.append(
                    InlineKeyboardButton(
                        text=category,
                        callback_data=f"edit_category|{expense_id}|{category}"
                    )
                )

            markup.add(*buttons)

            bot.send_message(
                message.chat.id,
                f"Expense: {expense_to_edit['Description']}\n"
                f"Current category: {expense_to_edit['Category']}\n\n"
                f"Select the new category:",
                reply_markup=markup
            )

        except Exception as e:
            bot.send_message(
                message.chat.id,
                f"Error editing expense: {e}"
            )

# Handle category button selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_category|"))
def handle_edit_category(call):
    try:
        # Extract expense ID and category
        _, expense_id, new_category = call.data.split("|", 2)

        # Read expenses
        df = read_csv(EXPENSE_FILE_PATH)

        # Convert expense IDs to strings
        df['expense_id'] = df['expense_id'].astype(str)
        expense_id = str(expense_id)

        # Find the expense
        matching_expenses = df[df['expense_id'] == expense_id]

        if matching_expenses.empty:
            bot.answer_callback_query(
                call.id,
                "Expense not found."
            )
            return
        expense_to_edit = matching_expenses.iloc[0]

        old_category = expense_to_edit['Category']

        # Update category
        expense_to_edit['Category'] = new_category

        # Write updated expenses back to CSV
        df.to_csv(EXPENSE_FILE_PATH, index=False)

        # Remove the buttons
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )

        # Confirm change
        bot.answer_callback_query(
            call.id,
            "Category updated!"
        )

        bot.send_message(
            call.message.chat.id,
            f"Category updated successfully!\n\n"
            f"Expense: {expense_to_edit['Description']}\n"
            f"Category: {old_category} → {new_category}"
        )
        add_data_to_csv('classifier/datasets/edited_expenses.csv', {'description': expense_to_edit["Description"], 'category': new_category}, ['description', 'category'])

    except Exception as e:
        bot.answer_callback_query(
            call.id,
            "Error updating category."
        )

        bot.send_message(
            call.message.chat.id,
            f"Error editing expense: {e}"
        )

# Get Expense breakdown command
@bot.message_handler(commands=['get_expenses'])
def get_expense_breakdown(message):
    if UserCheck(message) == True:
        try:
            if not os.path.exists(EXPENSE_FILE_PATH):
                bot.send_message(
                    message.chat.id,
                    "Expenses file not found. Please add expenses using /add."
                )
                return

            # Get requested period
            command_parts = message.text.split()

            if len(command_parts) > 1:
                period = command_parts[1].lower()
            else:
                period = "all"

            today = datetime.now()

            # Determine requested period
            if period == "all":
                filter_type = "all"
            elif period == "yearly":
                filter_type = "yearly"
            elif period == "monthly":
                filter_type = "monthly"
            else:
                # Try to interpret as MM/YY
                try:
                    requested_date = datetime.strptime(period, "%m/%y")
                    filter_type = "specific_month"
                except ValueError:
                    bot.send_message(
                        message.chat.id,
                        "Invalid period.\n\n"
                        "Use one of:\n"
                        "/get_expenses all\n"
                        "/get_expenses yearly\n"
                        "/get_expenses monthly\n"
                        "/get_expenses 08/26"
                    )
                    return
            # Read expenses
            with open(EXPENSE_FILE_PATH, 'r') as f:
                reader = csv.DictReader(f)
                expenses = list(reader)

            # Filter expenses for the user
            user_expenses = [
                e for e in expenses
                if e['User'] == message.from_user.first_name
            ]

            # Filter by date
            filtered_expenses = []
            for expense in user_expenses:
                # CSV format is DD/MM/YY
                expense_date = datetime.strptime(
                    expense['Date'],
                    "%d/%m/%y"
                )

                if filter_type == "all":
                    filtered_expenses.append(expense)
                elif filter_type == "yearly":
                    if expense_date.year == today.year:
                        filtered_expenses.append(expense)

                elif filter_type == "monthly":
                    if (
                        expense_date.year == today.year
                        and expense_date.month == today.month
                    ):
                        filtered_expenses.append(expense)

                elif filter_type == "specific_month":
                    if (
                        expense_date.year == requested_date.year
                        and expense_date.month == requested_date.month
                    ):
                        filtered_expenses.append(expense)

            if not filtered_expenses:
                bot.send_message(
                    message.chat.id,
                    "No expenses found for the requested period."
                )
                return

            # Separate shared and personal expenses
            shared_expenses = [
                e for e in filtered_expenses
                if e['isShared'].lower() == 'true'
            ]
            personal_expenses = [
                e for e in filtered_expenses
                if e['isShared'].lower() != 'true'
            ]
            # Calculate personal total
            total_expense = sum(
                float(e['Amount'])
                for e in personal_expenses
            )
            # Breakdown by category
            breakdown = {}
            for e in personal_expenses:
                category = e['Category']
                amount = float(e['Amount'])
                breakdown[category] = (
                    breakdown.get(category, 0) + amount
                )
            # Determine period name
            if filter_type == "all":
                period_name = "All Time"
            elif filter_type == "yearly":
                period_name = str(today.year)
            elif filter_type == "monthly":
                period_name = today.strftime("%B %Y")
            else:
                period_name = requested_date.strftime("%B %Y")

            # Build message
            breakdown_message = (
                f"Expense Breakdown - {period_name}\n\n"
                f"Total Expense: £{total_expense:.2f}\n\n"
                f"Breakdown by Category:\n"
            )

            for category, amount in breakdown.items():
                breakdown_message += (
                    f"{category}: £{amount:.2f}\n"
                )

            # Shared expenses
            if shared_expenses:
                shared_expenses_breakdown = {}
                for e in shared_expenses:
                    category = e['Category']
                    amount = float(e['Amount'])
                    shared_expenses_breakdown[category] = (
                        shared_expenses_breakdown.get(category, 0)
                        + amount
                    )
                shared_total = sum(
                    float(e['Amount'])
                    for e in shared_expenses
                )
                breakdown_message += (
                    f"\nShared Expenses Total: £{shared_total:.2f}\n"
                )
                for category, amount in shared_expenses_breakdown.items():
                    breakdown_message += (
                        f"{category} (Shared): £{amount:.2f}\n"
                    )
            bot.send_message(
                message.chat.id,
                breakdown_message
            )

        except Exception as e:
            bot.send_message(
                message.chat.id,
                f"Error retrieving expense breakdown: {e}"
            )

# get Portfolio command
@bot.message_handler(commands=['portfolio'])
def get_portfolio(message):
    pass

# Setup/Edit Profile command
@bot.message_handler(commands=['setup_profile', 'edit_profile'])
def setup_profile(message):
    if UserCheck(message) == True:
        # get take home pay from user
        msg = bot.send_message(message.chat.id, "What is your take home pay?")
        bot.register_next_step_handler(msg, get_take_home_pay, PROFILE_HEADERS)

@bot.message_handler(commands=['profile'])
def get_profile(message):
    if UserCheck(message) == True:
        if os.path.exists(PROFILE_FILE_PATH):
            with open(PROFILE_FILE_PATH, 'r') as f:
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
        msg =  bot.send_message(message.chat.id, "What is the amount?")
        bot.register_next_step_handler(msg, get_amount, expense)

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    if UserCheck(message) == True:
        bot.send_message(message.chat.id, "Welcome {}\nUser: {}  ".format(message.from_user.first_name,message.from_user.id))
        bot.reply_to(message, "/start & /help to start and get commands\n/add to add record")

@bot.message_handler(func=lambda message: True)
def handle_unhandled_message(message):
    if UserCheck(message) == True:
        resp = route_query(message)
        print(f"Resolved query: {resp}")
        if not resp:
            bot.send_message(message.chat.id, "Failed to parse message")
            return

print("I'm listening...")
execute_jobs()
bot.infinity_polling()