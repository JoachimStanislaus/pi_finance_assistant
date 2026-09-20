"""
Expense Category Prediction

Loads the trained scikit-learn model and predicts
the category of an expense description.
"""

import pickle
import re

import numpy as np


MODEL_PATH = "models/model.pkl"
LABEL_ENCODER_PATH = "models/label_encoder.pkl"


# ============================================================
# Load model
# ============================================================

with open(
    MODEL_PATH,
    "rb"
) as f:

    model_data = pickle.load(f)


vectorizer = model_data["vectorizer"]
model = model_data["model"]


# ============================================================
# Load label encoder
# ============================================================

with open(
    LABEL_ENCODER_PATH,
    "rb"
) as f:

    label_encoder = pickle.load(f)


# ============================================================
# Text preprocessing
# ============================================================

def preprocess_text(text):

    text = str(text).lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


# ============================================================
# Prediction
# ============================================================

def predict_category(description):

    description = preprocess_text(
        description
    )

    # Convert description into TF-IDF features
    X = vectorizer.transform(
        [description]
    )

    # Predict category
    predicted_class = model.predict(
        X
    )[0]

    # Convert number back to category name
    category = label_encoder.inverse_transform(
        [predicted_class]
    )[0]

    # Get confidence
    probabilities = model.predict_proba(
        X
    )[0]

    confidence = float(
        np.max(probabilities)
    )

    return category, confidence


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    while True:

        description = input("\nExpense description: ")

        if description.lower() == "quit":
            break

        category, confidence = predict_category(
            description
        )

        print(f"Category: {category}")
        print(f"Confidence: {confidence:.2%}")