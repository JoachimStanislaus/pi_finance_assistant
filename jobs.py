import pandas as pd

from helper import add_data_to_csv, create_csv_file_if_not_exists, today_date
from pi_finance_assistant import EXPENSE_FIELDS

#decorator for is_job_executed
def job_executed(job_name:str):
    """
    Decorator to check if a job has been executed before
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if is_job_executed(job_name):
                print(f"Job '{job_name}' has already been executed. Skipping...")
                return None
            else:
                result = func(*args, **kwargs)
                update_job_history(job_name, today_date())
                return result
        return wrapper
    return decorator

def is_job_executed(job_name:str):
    """
    Checks if a job has been executed before
    """
    create_csv_file_if_not_exists("data/job_history.csv", ["job_name", "timestamp"])
    df = pd.read_csv("data/job_history.csv")
    return job_name in df['job_name'].values

def update_job_history(job_name:str, timestamp:str):
    """
    Updates the job history with jobs that have been executed
    """
    add_data_to_csv("data/job_history.csv", {"job_name": job_name, "timestamp": timestamp}, ["job_name", "timestamp"])

def execute_jobs():
    """
    Executes one time jobs on startup
    """
    update_expenses_from_history()
    pass

@job_executed("update_expenses_from_history_1")
def update_expenses_from_history():
    """
    Updates the expenses.csv file with new data from history.csv
    """
    history_df = pd.read_csv('classifier/datasets/history.csv')
    create_csv_file_if_not_exists("data/expenses.csv", EXPENSE_FIELDS)
    expenses_df = pd.read_csv('data/expenses.csv')

    # Give history_df the same columns as expenses df (Date,Category,Description,Amount,isShared,User,expense_id), history_df has columns (Date,Category,Description,Amount) user should be set to Joachim and expense_id should be set to None and isShared should be set to False
    history_df['isShared'] = False
    history_df['User'] = 'Joachim'
    history_df['expense_id'] = None

    # Merge the two dataframes, the new rows from history_df should be added to expenses_df, and the result should be saved to expenses.csv. 
    merged_df = pd.concat([expenses_df, history_df], ignore_index=True)
    merged_df.to_csv('data/expenses.csv', index=False)