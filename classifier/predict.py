import pickle
import re
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from training import MODEL_PATH, VOCAB_PATH, LABEL_ENCODER_PATH 


# -----------------------------
# Load everything
# -----------------------------

model = tf.keras.models.load_model(MODEL_PATH)

with open(VOCAB_PATH, "rb") as f:
    vocab_data = pickle.load(f)

vocabulary = vocab_data["vocabulary"]
max_sequence_length = vocab_data["max_sequence_length"]
max_n_gram = vocab_data["max_n_gram"]

with open(LABEL_ENCODER_PATH, "rb") as f:
    label_encoder = pickle.load(f)


# -----------------------------
# Text preprocessing
# -----------------------------

def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# -----------------------------
# Convert text to numbers
# -----------------------------

def text_to_sequence(text):
    tokens = []

    for n in range(1, max_n_gram + 1):
        for i in range(len(text) - n + 1):
            token = text[i:i+n]

            # Use UNK if the model hasn't seen this token
            token_id = vocabulary.get(
                token,
                vocabulary["<UNK>"]
            )

            tokens.append(token_id)

    return tokens[:max_sequence_length]


# -----------------------------
# Predict category
# -----------------------------

def predict_category(description):

    description = preprocess_text(description)

    sequence = text_to_sequence(description)

    X = pad_sequences(
        [sequence],
        maxlen=max_sequence_length,
        padding="post",
        truncating="post",
        value=vocabulary["<PAD>"]
    )

    probabilities = model.predict(X, verbose=0)[0]

    predicted_class = int(np.argmax(probabilities))

    category = label_encoder.inverse_transform(
        [predicted_class]
    )[0]

    confidence = float(probabilities[predicted_class])

    return category, confidence