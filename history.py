import pandas as pd
from constants import EXPENSE_FILE_PATH


def get_user_last_num_expenses(user, num_expenses=5):
    """
    Returns the last N expenses entered by a specific user.

    Parameters:
        user (str): User name to filter by.
        num_expenses (int): Number of recent expenses to return.

    Returns:
        pd.DataFrame: Last N expenses entered by the user.
    """

    expenses_df = pd.read_csv(EXPENSE_FILE_PATH)

    # Filter by user
    user_expenses = expenses_df[
        expenses_df["User"].str.lower() == user.lower()
    ]

    # Get the last N rows entered
    last_n_expenses = user_expenses.tail(num_expenses)

    return last_n_expenses