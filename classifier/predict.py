import pickle
import re
import numpy as np
import onnxruntime as ort


MODEL_PATH = "models/model.onnx"
VOCAB_PATH = "models/vocabulary.pkl"
LABEL_ENCODER_PATH = "models/label_encoder.pkl"


# Load ONNX model
session = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)

input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name


# Load vocabulary
with open(VOCAB_PATH, "rb") as f:
    vocab_data = pickle.load(f)

vocabulary = vocab_data["vocabulary"]
max_sequence_length = vocab_data["max_sequence_length"]
max_n_gram = vocab_data["max_n_gram"]


# Load label encoder
with open(LABEL_ENCODER_PATH, "rb") as f:
    label_encoder = pickle.load(f)


def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def text_to_sequence(text):
    tokens = []

    # IMPORTANT:
    # This order should match the order used during training.
    for i in range(len(text)):
        for n in range(1, max_n_gram + 1):
            token = text[i:i+n]

            if not token:
                continue

            token_id = vocabulary.get(
                token,
                vocabulary["<UNK>"]
            )

            tokens.append(token_id)

    return tokens[:max_sequence_length]


def pad_sequence(sequence, maxlen, pad_value):
    """
    Equivalent to the padding we were doing with
    tensorflow.keras.preprocessing.sequence.pad_sequences.
    """

    X = np.full(
        (1, maxlen),
        pad_value,
        dtype=np.int32
    )

    sequence = sequence[:maxlen]

    X[0, :len(sequence)] = sequence

    return X


def predict_category(description):

    # 1. Clean text
    description = preprocess_text(description)

    # 2. Convert text → token IDs
    sequence = text_to_sequence(description)

    # 3. Pad sequence
    X = pad_sequence(
        sequence,
        max_sequence_length,
        vocabulary["<PAD>"]
    )

    # 4. Run ONNX model
    probabilities = session.run(
        [output_name],
        {input_name: X}
    )[0][0]

    # 5. Get highest probability
    predicted_class = int(np.argmax(probabilities))

    # 6. Convert class number → category
    category = label_encoder.inverse_transform(
        [predicted_class]
    )[0]

    confidence = float(
        probabilities[predicted_class]
    )

    return category, confidence


if __name__ == "__main__":

    description = "Tesco groceries"

    category, confidence = predict_category(description)

    print(f"Description: {description}")
    print(f"Category: {category}")
    print(f"Confidence: {confidence:.2%}")