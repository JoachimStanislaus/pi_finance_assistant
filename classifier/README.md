# Classifier Module - Expense Category Classification

This module provides machine learning-based classification of expense descriptions into 10 predefined categories.

## Categories
- Eating Out
- Entertainment / Social
- Transportation
- Groceries
- Learning
- Bills
- Travel
- Grooming
- Shopping
- Dogs
- Gifts

## Usage

### Training the Model
```bash
python classifier/training.py
```

This will:
1. Load sample_data.csv (or any CSV with 'description' and 'category' columns)
2. Preprocess text data
3. Train a neural network model
4. Save the trained model to `classifier/model.h5`
5. Save label encoder to `classifier/label_encoder.pkl`

### Classifying Expenses
The classifier is automatically loaded in `pi_finance_assistant.py`. The `resolve_fields_from_description()` function uses the trained model to classify expense descriptions.

## Text Categories Used for Training
Each sample data record includes:
- **description**: Raw expense description text (e.g., "starbucks coffee morning")
- **category**: Target category label (one of the 10 predefined categories)

The classifier uses character n-gram features to classify text descriptions into categories.
