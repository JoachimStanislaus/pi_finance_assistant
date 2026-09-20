"""
Expense Category Classifier Training Pipeline

Trains a lightweight scikit-learn model to classify
expense descriptions into expense categories.

The model uses character-level TF-IDF features with
Logistic Regression.

Examples:

    "Tesco groceries"
    "Dinner at Pizza Express"
    "Uber to work"
    "Amazon dog food"
"""

import os
import re
import pickle

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score


# ============================================================
# Configuration
# ============================================================

MODEL_PATH = "models/model.pkl"
LABEL_ENCODER_PATH = "models/label_encoder.pkl"

TEST_SIZE = 0.2
RANDOM_STATE = 42

# Character n-grams from 1 to 3 characters
NGRAM_RANGE = (1, 3)

# Maximum number of TF-IDF features
# Keeping this reasonably small helps on the Raspberry Pi.
MAX_FEATURES = 10000


# ============================================================
# Text preprocessing
# ============================================================

def preprocess_text(text):
    """
    Clean an expense description.
    """

    text = str(text).lower()

    # Keep letters, numbers and spaces
    text = re.sub(r"[^a-z0-9\s]", "", text)

    # Remove repeated whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# Training
# ============================================================

# I want to give 2 paths so that I can train the model on the original dataset and also on the edited dataset. The edited dataset will be used to improve the model over time.
def train_classifier(csv_path, edited_csv_path=None):

    print("=" * 60)
    print("Loading training data")
    print("=" * 60)

    df = pd.read_csv(csv_path)
    edited_df = pd.read_csv(edited_csv_path) if edited_csv_path else pd.DataFrame()
    df = pd.concat([df, edited_df], ignore_index=True)

    print(f"Loaded {len(df)} rows")

    # --------------------------------------------------------
    # Clean dataset
    # --------------------------------------------------------

    print("\nCleaning dataset...")

    initial_count = len(df)

    df = df.dropna(
        subset=["description", "category"]
    )

    removed = initial_count - len(df)

    print(f"Removed {removed} rows with missing data")
    print(f"Remaining samples: {len(df)}")

    df["description"] = (
        df["description"]
        .astype(str)
    )

    df["category"] = (
        df["category"]
        .astype(str)
        .str.strip()
    )

    # Remove empty descriptions/categories
    df = df[
        (df["description"].str.strip() != "")
        &
        (df["category"].str.strip() != "")
    ]

    # --------------------------------------------------------
    # Preprocess descriptions
    # --------------------------------------------------------

    print("\nPreprocessing descriptions...")

    df["cleaned_description"] = (
        df["description"]
        .apply(preprocess_text)
    )

    # Remove descriptions that became empty
    df = df[
        df["cleaned_description"].str.strip() != ""
    ]

    # --------------------------------------------------------
    # Encode categories
    # --------------------------------------------------------

    print("\nEncoding categories...")

    label_encoder = LabelEncoder()

    y = label_encoder.fit_transform(
        df["category"]
    )

    print(
        f"Categories ({len(label_encoder.classes_)}):"
    )

    for i, category in enumerate(
        label_encoder.classes_
    ):
        print(f"  {i}: {category}")

    # --------------------------------------------------------
    # Train/test split
    # --------------------------------------------------------

    print("\nSplitting dataset...")

    X_train_text, X_test_text, y_train, y_test = train_test_split(
        df["cleaned_description"],
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    print(
        f"Training samples: {len(X_train_text)}"
    )

    print(
        f"Testing samples: {len(X_test_text)}"
    )

    # --------------------------------------------------------
    # TF-IDF
    # --------------------------------------------------------

    print("\nCreating TF-IDF vectorizer...")

    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=NGRAM_RANGE,
        max_features=MAX_FEATURES,
        lowercase=False
    )

    print("\nFitting TF-IDF on training data...")

    X_train = vectorizer.fit_transform(
        X_train_text
    )

    # IMPORTANT:
    # Only transform the test data.
    # We do NOT fit the vectorizer on test data.

    X_test = vectorizer.transform(
        X_test_text
    )

    print(
        f"Training feature matrix: {X_train.shape}"
    )

    print(
        f"Testing feature matrix: {X_test.shape}"
    )

    # --------------------------------------------------------
    # Create classifier
    # --------------------------------------------------------

    print("\nCreating Logistic Regression model...")

    model = LogisticRegression(
        max_iter=1000,
        random_state=RANDOM_STATE
    )

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    print("\nTraining model...")
    print("=" * 60)

    model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("Model evaluation")
    print("=" * 60)

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print(
        f"Test Accuracy: {accuracy:.4f}"
    )

    print("\nClassification report:")

    print(
        classification_report(
            y_test,
            predictions,
            target_names=label_encoder.classes_,
            zero_division=0
        )
    )

    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    print("\nSaving model...")

    os.makedirs(
        os.path.dirname(MODEL_PATH),
        exist_ok=True
    )

    # Save vectorizer + classifier together
    model_data = {
        "vectorizer": vectorizer,
        "model": model
    }

    with open(
        MODEL_PATH,
        "wb"
    ) as f:

        pickle.dump(
            model_data,
            f
        )

    print(
        f"Model saved to: {MODEL_PATH}"
    )

    # --------------------------------------------------------
    # Save label encoder
    # --------------------------------------------------------

    with open(
        LABEL_ENCODER_PATH,
        "wb"
    ) as f:

        pickle.dump(
            label_encoder,
            f
        )

    print(
        f"Label encoder saved to: "
        f"{LABEL_ENCODER_PATH}"
    )

    print("\nTraining complete!")

    return model


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    csv_path = (
        "/Users/joachim/Desktop/Coding/"
        "pi_finance_assistant/classifier/datasets/"
        "expenses.csv"
    )

    train_classifier(
        csv_path,
        edited_csv_path="/Users/joachim/Desktop/Coding/pi_finance_assistant/classifier/edited_expenses.csv"
    )