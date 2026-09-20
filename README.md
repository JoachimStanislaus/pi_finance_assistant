# pi_finance_assistant
a financial assistant run on my raspberry pi, one of the many bots managed by my pi mgmt bot

# Create your venv
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install all requirements
pip install -r requirements.txt


# for converting tensorflow model to onnx
python -m venv onnx-converter
source onnx-converter/bin/activate
python -m pip install tensorflow tf2onnx onnx