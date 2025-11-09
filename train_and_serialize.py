"""Train and serialize the recommender model."""
import os
import numpy as np
import pandas as pd
from src.model import Recommender

# Set deterministic seeds
os.environ['PYTHONHASHSEED'] = '0'
np.random.seed(0)

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

# Load data
print("Loading data...")
catalog_df = pd.read_csv('data/sample_catalog.csv')
interactions_df = pd.read_csv('data/sample_interactions.csv')

print(f"Loaded {len(catalog_df)} products and {len(interactions_df)} interactions")

# Train recommender
print("Training recommender...")
recommender = Recommender()
recommender.fit(catalog_df, interactions_df)

# Save model
print("Saving model...")
recommender.save('models/recommender.pkl')

print("Model training complete! Saved to models/recommender.pkl")

