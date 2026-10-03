#Get today's date in integer format
from collections.abc import Mapping
import csv
import os
import pandas as pd
from datetime import datetime
from constants import TelegramUsers, bot


def today_date():
    # Creating a datetime object so we can test.
    a = datetime.now()
    # Converting a to string in the desired format (YYYYMMDD) using strftime
    # and then to int.
    a = str(a.strftime('%d/%m/%y'))
    return a

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

def read_csv(file_path):
    """Reads the CSV file and returns a dataframe."""
    try:
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            return df
        else:
            print(f"✗ File not found: {file_path}")
            return pd.DataFrame()  # Return an empty DataFrame if file doesn't exist
    except Exception as e:
        print(f"✗ Error reading CSV: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

def generate_expense_id():
    """Generates a unique ID for each expense based on the current timestamp."""
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

#Checks if User is Authorized or not
def UserCheck(message):
    if message.from_user.id in TelegramUsers:    
        return True
    else:
        bot.reply_to(message, "Unauthorized User")
        return False

def send_message(chat_id, text):
    """Sends a message to the specified chat ID."""
    try:
        bot.send_message(chat_id, text)
        return True
    except Exception as e:
        print(f"✗ Error sending message: {e}")
        return False