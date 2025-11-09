"""Feature engineering and vectorization for products."""
import os
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from scipy.sparse import hstack

# Set deterministic seeds
os.environ['PYTHONHASHSEED'] = '0'
np.random.seed(0)


class ProductVectorizer:
    """Vectorizes products using TF-IDF and one-hot encoding."""
    
    def __init__(self, max_features: int = 100):
        """Initialize vectorizer.
        
        Args:
            max_features: Maximum number of TF-IDF features
        """
        self.tfidf = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )
        self.brand_encoder = OneHotEncoder(sparse_output=True, handle_unknown='ignore')
        self.category_encoder = OneHotEncoder(sparse_output=True, handle_unknown='ignore')
        self.is_fitted = False
        
    def fit_transform(self, catalog_df: pd.DataFrame) -> np.ndarray:
        """Fit vectorizers and transform catalog to vectors.
        
        Args:
            catalog_df: DataFrame with product_id, product_name, brand, category, description
            
        Returns:
            Normalized product vectors as dense numpy array
        """
        # Combine text features
        text_features = (
            catalog_df['product_name'].fillna('') + ' ' +
            catalog_df['description'].fillna('')
        )
        
        # Fit and transform TF-IDF
        tfidf_features = self.tfidf.fit_transform(text_features)
        
        # Fit and transform one-hot encoders
        brand_features = self.brand_encoder.fit_transform(
            catalog_df[['brand']].values
        )
        category_features = self.category_encoder.fit_transform(
            catalog_df[['category']].values
        )
        
        # Combine all features
        combined = hstack([tfidf_features, brand_features, category_features])
        
        # Convert to dense and normalize to unit length
        dense = combined.toarray()
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        normalized = dense / norms
        
        self.is_fitted = True
        return normalized
    
    def transform(self, catalog_df: pd.DataFrame) -> np.ndarray:
        """Transform new products to vectors.
        
        Args:
            catalog_df: DataFrame with product_id, product_name, brand, category, description
            
        Returns:
            Normalized product vectors as dense numpy array
        """
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted first")
        
        # Combine text features
        text_features = (
            catalog_df['product_name'].fillna('') + ' ' +
            catalog_df['description'].fillna('')
        )
        
        # Transform TF-IDF
        tfidf_features = self.tfidf.transform(text_features)
        
        # Transform one-hot encoders
        brand_features = self.brand_encoder.transform(
            catalog_df[['brand']].values
        )
        category_features = self.category_encoder.transform(
            catalog_df[['category']].values
        )
        
        # Combine all features
        combined = hstack([tfidf_features, brand_features, category_features])
        
        # Convert to dense and normalize to unit length
        dense = combined.toarray()
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        normalized = dense / norms
        
        return normalized

