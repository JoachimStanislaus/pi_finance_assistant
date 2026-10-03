from constants import bot, EXPENSE_FILE_PATH, EXPENSE_FIELDS
from helper import today_date, generate_expense_id, today_date, add_data_to_csv
from collections.abc import Mapping

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
    category, isShared = resolve_expense_fields_from_description(expense.get('description'))
    expense['category'] = category
    expense['isShared'] = isShared
    expense['date'] = expense.get('date') or today_date()
    expense['user'] = message.from_user.first_name
    expense['expense_id'] = generate_expense_id()

    # Append to CSV
    if append_expense_to_csv(EXPENSE_FILE_PATH, expense):
        bot.send_message(message.chat.id, f"Expense added successfully! (Predicted Category: {expense['category']}, if incorrect, please edit the expense manually.)")
        bot.send_message(message.chat.id, f"/edit {expense['expense_id']}")
    else:
        bot.send_message(message.chat.id, "Failed to add expense. Please try again.")

def append_expense_to_csv(file_path, expense: Mapping[str, str]) -> bool:
    """Appends a new expense record to the CSV file."""
    try:
        format_expense = {
            "Date": expense.get("date", today_date()),
            "Category": expense.get("category", ""),
            "Description": expense.get("description", ""),
            "Amount": expense.get("amount", ""),
            "isShared": expense.get("isShared", ""),
            "User": expense.get("user", ""),
            "expense_id": expense.get("expense_id", ""),
        }
        add_data_to_csv(file_path, format_expense, EXPENSE_FIELDS)
        return True
        
    except Exception as e:
        print(f"✗ Error appending expense: {e}")
        return False

def resolve_expense_fields_from_description(description):
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
        elif any(keyword.lower() in description.lower() for keyword in ('nicole', 'joachim')) and 'treat' in description.lower():
            is_shared = False
        else:
            is_shared = any(keyword.lower() in description.lower() for keyword in shared_keywords)
    
    return category, str(is_shared)