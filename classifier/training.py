"""
Expense Category Classifier Training Pipeline

Trains a CNN model to classify expense descriptions
into expense categories.

The model uses character n-grams, which works well for
short expense descriptions such as:

    "Tesco groceries"
    "Dinner at Pizza Express"
    "Uber to work"
    "Amazon dog food"
"""

import os
import re
import pickle

import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Embedding,
    Conv1D,
    GlobalMaxPooling1D,
    Dense,
    Dropout,
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.preprocessing.sequence import pad_sequences


# ============================================================
# Configuration
# ============================================================

MAX_SEQUENCE_LENGTH = 100
MAX_N_GRAM = 3
EMBEDDING_DIM = 64

BATCH_SIZE = 32
EPOCHS = 50

LEARNING_RATE = 0.001

MODEL_PATH = "models/model.h5"
VOCAB_PATH = "models/vocabulary.pkl"
LABEL_ENCODER_PATH = "models/label_encoder.pkl"


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
# Vocabulary creation
# ============================================================

def build_vocabulary(texts):
    """
    Build ONE vocabulary from the entire training dataset.

    Character n-grams of size 1-3 are used.

    Example:

        "tesco"

    produces:

        t
        te
        tes
        e
        es
        esc
        s
        sco
        c
        co
        o
    """

    vocabulary = {
        "<PAD>": 0,
        "<UNK>": 1,
    }

    for text in texts:

        for i in range(len(text)):

            for n in range(1, MAX_N_GRAM + 1):

                token = text[i:i + n]

                if token and token not in vocabulary:
                    vocabulary[token] = len(vocabulary)

    return vocabulary


# ============================================================
# Convert text to token IDs
# ============================================================

def text_to_sequence(text, vocabulary):
    """
    Convert a description into integer token IDs.
    """

    tokens = []

    for i in range(len(text)):

        for n in range(1, MAX_N_GRAM + 1):

            token = text[i:i + n]

            if not token:
                continue

            token_id = vocabulary.get(
                token,
                vocabulary["<UNK>"]
            )

            tokens.append(token_id)

    # Limit sequence length
    tokens = tokens[:MAX_SEQUENCE_LENGTH]

    return tokens


# ============================================================
# Create model
# ============================================================

def create_model(num_features, num_categories):

    model = Sequential([
        Embedding(
            input_dim=num_features,
            output_dim=EMBEDDING_DIM,
            input_length=MAX_SEQUENCE_LENGTH
        ),

        Conv1D(
            filters=128,
            kernel_size=3,
            activation="relu"
        ),

        Dropout(0.5),

        GlobalMaxPooling1D(),

        Dense(
            64,
            activation="relu"
        ),

        Dropout(0.5),

        Dense(
            32,
            activation="relu"
        ),

        Dense(
            num_categories,
            activation="softmax"
        )
    ])

    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer=Adam(
            learning_rate=LEARNING_RATE
        ),
        metrics=["accuracy"]
    )

    return model


# ============================================================
# Training
# ============================================================

def train_classifier(csv_path):

    print("=" * 60)
    print("Loading training data")
    print("=" * 60)

    df = pd.read_csv(csv_path)

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

    cleaned_descriptions = []

    for description in df["description"]:

        cleaned = preprocess_text(
            description
        )

        cleaned_descriptions.append(cleaned)

    # --------------------------------------------------------
    # Build vocabulary
    # --------------------------------------------------------

    print("\nBuilding vocabulary...")

    vocabulary = build_vocabulary(
        cleaned_descriptions
    )

    print(
        f"Vocabulary size: {len(vocabulary)}"
    )

    # --------------------------------------------------------
    # Convert descriptions to sequences
    # --------------------------------------------------------

    print("\nConverting descriptions to sequences...")

    sequences = []

    for description in cleaned_descriptions:

        sequence = text_to_sequence(
            description,
            vocabulary
        )

        sequences.append(sequence)

    # Pad sequences
    X = pad_sequences(
        sequences,
        maxlen=MAX_SEQUENCE_LENGTH,
        padding="post",
        truncating="post",
        value=vocabulary["<PAD>"]
    )

    print(
        f"Input shape: {X.shape}"
    )

    # --------------------------------------------------------
    # Encode categories
    # --------------------------------------------------------

    print("\nEncoding categories...")

    label_encoder = LabelEncoder()

    y = label_encoder.fit_transform(
        df["category"]
    )

    num_categories = len(
        label_encoder.classes_
    )

    print(
        f"Categories ({num_categories}):"
    )

    for i, category in enumerate(
        label_encoder.classes_
    ):
        print(f"  {i}: {category}")

    # --------------------------------------------------------
    # Train/test split
    # --------------------------------------------------------

    print("\nSplitting dataset...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print(
        f"Training samples: {len(X_train)}"
    )

    print(
        f"Testing samples: {len(X_test)}"
    )

    # --------------------------------------------------------
    # Create model
    # --------------------------------------------------------

    print("\nCreating model...")

    model = create_model(
        num_features=len(vocabulary),
        num_categories=num_categories
    )

    model.summary()

    # --------------------------------------------------------
    # Training callbacks
    # --------------------------------------------------------

    callbacks = [

        EarlyStopping(
            monitor="val_loss",
            patience=5,
            restore_best_weights=True
        ),

        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-5
        )
    ]

    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    print("\nTraining model...")
    print("=" * 60)

    history = model.fit(
        X_train,
        y_train,

        epochs=EPOCHS,

        batch_size=BATCH_SIZE,

        validation_data=(
            X_test,
            y_test
        ),

        callbacks=callbacks,

        verbose=1
    )

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("Model evaluation")
    print("=" * 60)

    loss, accuracy = model.evaluate(
        X_test,
        y_test,
        verbose=0
    )

    print(
        f"Test Loss: {loss:.4f}"
    )

    print(
        f"Test Accuracy: {accuracy:.4f}"
    )

    # --------------------------------------------------------
    # Detailed classification report
    # --------------------------------------------------------

    predictions = model.predict(
        X_test,
        verbose=0
    )

    predicted_classes = np.argmax(
        predictions,
        axis=1
    )

    print("\nClassification report:")

    print(
        classification_report(
            y_test,
            predicted_classes,
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

    model.save(
        MODEL_PATH
    )

    print(
        f"Model saved to: {MODEL_PATH}"
    )

    # --------------------------------------------------------
    # Save vocabulary
    # --------------------------------------------------------

    with open(
        VOCAB_PATH,
        "wb"
    ) as f:

        pickle.dump(
            {
                "vocabulary": vocabulary,
                "max_sequence_length": MAX_SEQUENCE_LENGTH,
                "max_n_gram": MAX_N_GRAM
            },
            f
        )

    print(
        f"Vocabulary saved to: {VOCAB_PATH}"
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
        csv_path
    )