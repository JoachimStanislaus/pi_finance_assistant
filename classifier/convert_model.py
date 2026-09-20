import tensorflow as tf
import tf2onnx

MODEL_PATH = "models/model.h5"
OUTPUT_PATH = "models/model.onnx"

print("Loading TensorFlow model...")

model = tf.keras.models.load_model(
    MODEL_PATH,
    compile=False
)

print("Model loaded successfully.")

# Create a concrete TensorFlow function
input_signature = [
    tf.TensorSpec(
        shape=[None, 100],
        dtype=tf.int32,
        name="input"
    )
]

@tf.function(input_signature=input_signature)
def model_function(x):
    return model(x)

print("Converting to ONNX...")

tf2onnx.convert.from_function(
    model_function,
    input_signature=input_signature,
    opset=13,
    output_path=OUTPUT_PATH
)

print(f"ONNX model saved to: {OUTPUT_PATH}")