import sys
from predict import predict_category

# used to test model in terminal eg: python3 classifier/test_model.py "snoopy"

description = " ".join(sys.argv[1:])

category, confidence = predict_category(description)

print(f"Category: {category}")
print(f"Confidence: {confidence:.1%}")