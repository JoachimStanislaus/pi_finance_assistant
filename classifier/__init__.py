"""
Main classifier module for classifying expense descriptions
"""

import numpy as np
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import to_categorical


class ExpenseClassifier:
    """Expense category classification model"""
    
    def __init__(self, model_path='classifier/model.h5'):
        self.model = load_model(model_path)
        with open('classifier/label_encoder.pkl', 'rb') as f:
            data = pickle.load(f)
            self.label_classes = data['label_classes']
            self.model = data['model']
    
    def classify(self, description):
        """Classify a single expense description"""
        # Preprocess text
        text = description.lower()
        text = ''.join(c for c in text if c.isalnum() or c in ' ,.!?')
        
        # Create features (simplified approach - use character counts)
        features = []
        
        # Character bigrams
        bigrams = {}
        for i in range(len(text) - 1):
            bigram = text[i:i+2]
            if len(bigram) == 2:
                features.append([ord(bigram[0]) % 100, ord(bigram[1]) % 100])
        
        if not features:
            # Default prediction if no text
            return {"category": self.label_classes[0], "confidence": 0.0}
        
        features = np.array(features).reshape(1, -1)
        
        # Make prediction
        prediction = self.model.predict(features)
        predicted_label = np.argmax(prediction)
        confidence = float(np.max(prediction))
        
        return {
            "category": self.label_classes[predicted_label],
            "confidence": confidence
        }
    
    def batch_classify(self, descriptions):
        """Classify multiple expense descriptions"""
        predictions = []
        for desc in descriptions:
            result = self.classify(desc)
            predictions.append(result)
        return predictions


# Global classifier instance
_classifier = None

def get_classifier():
    """Get or create the classifier instance"""
    global _classifier
    if _classifier is None:
        from training import train_classifier
        model_path = 'model.h5'
        
        try:
            _classifier = ExpenseClassifier(model_path)
        except FileNotFoundError:
            print("Model not found. Training from scratch...")
            model = train_classifier('sample_data.csv')
            _classifier = ExpenseClassifier(model_path=model_path)
    
    return _classifier


def classify_expense(description):
    """Convenience function to classify an expense"""
    clf = get_classifier()
    return clf.classify(description)
