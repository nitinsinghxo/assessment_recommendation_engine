"""Recommender model with hybrid content-based and popularity-based approach."""
import os
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from src.features import ProductVectorizer

# Set deterministic seeds
os.environ['PYTHONHASHSEED'] = '0'
np.random.seed(0)


class Recommender:
    """Hybrid recommender combining content similarity and popularity."""
    
    def __init__(self):
        """Initialize recommender."""
        self.vectorizer = ProductVectorizer()
        self.product_vectors = None
        self.catalog_df = None
        self.popularity_scores = None
        self.product_id_to_idx = {}
        self.idx_to_product_id = {}
        
    def fit(self, catalog_df: pd.DataFrame, interactions_df: pd.DataFrame):
        """Fit the recommender on catalog and interactions.
        
        Args:
            catalog_df: Product catalog with columns: product_id, product_name, brand, category, description
            interactions_df: User interactions with columns: user_id, product_id, event, timestamp
        """
        self.catalog_df = catalog_df.copy()
        
        # Create product vectors
        self.product_vectors = self.vectorizer.fit_transform(catalog_df)
        
        # Build product ID mappings
        for idx, product_id in enumerate(catalog_df['product_id']):
            self.product_id_to_idx[product_id] = idx
            self.idx_to_product_id[idx] = product_id
        
        # Compute popularity scores (normalized interaction counts)
        purchase_counts = interactions_df[
            interactions_df['event'] == 'purchase'
        ]['product_id'].value_counts()
        
        view_counts = interactions_df[
            interactions_df['event'] == 'view'
        ]['product_id'].value_counts()
        
        # Weight purchases more than views
        total_scores = purchase_counts * 2.0 + view_counts * 1.0
        
        # Normalize to 0-1 range
        if total_scores.max() > 0:
            self.popularity_scores = (total_scores / total_scores.max()).to_dict()
        else:
            self.popularity_scores = {}
        
        # Fill missing products with 0 popularity
        for product_id in catalog_df['product_id']:
            if product_id not in self.popularity_scores:
                self.popularity_scores[product_id] = 0.0
    
    def _get_content_similarity(
        self, 
        query_idx: int, 
        candidate_indices: List[int]
    ) -> np.ndarray:
        """Compute content similarity scores.
        
        Args:
            query_idx: Index of query product
            candidate_indices: List of candidate product indices
            
        Returns:
            Array of similarity scores
        """
        if query_idx not in range(len(self.product_vectors)):
            return np.zeros(len(candidate_indices))
        
        query_vector = self.product_vectors[query_idx]
        candidate_vectors = self.product_vectors[candidate_indices]
        
        # Cosine similarity (vectors already normalized)
        similarities = np.dot(candidate_vectors, query_vector)
        return similarities
    
    def _get_popularity_scores(self, candidate_ids: List[str]) -> np.ndarray:
        """Get popularity scores for candidate products.
        
        Args:
            candidate_ids: List of product IDs
            
        Returns:
            Array of popularity scores
        """
        return np.array([
            self.popularity_scores.get(pid, 0.0) for pid in candidate_ids
        ])
    
    def _generate_reason(
        self, 
        content_sim: float, 
        popularity: float,
        query_product: pd.Series,
        candidate_product: pd.Series
    ) -> str:
        """Generate explainable reason for recommendation.
        
        Args:
            content_sim: Content similarity score
            popularity: Popularity score
            query_product: Query product row
            candidate_product: Candidate product row
            
        Returns:
            Reason string
        """
        reasons = []
        
        if content_sim >= 0.6:
            reasons.append("strong content match")
        elif content_sim >= 0.3:
            reasons.append("moderate text similarity")
        
        if query_product['brand'] == candidate_product['brand']:
            reasons.append("same brand")
        
        if query_product['category'] == candidate_product['category']:
            reasons.append("same category")
        
        if popularity >= 0.7:
            reasons.append("popular item")
        elif popularity >= 0.4:
            reasons.append("moderate popularity")
        
        if not reasons:
            if content_sim > 0:
                reasons.append("low content similarity")
            else:
                reasons.append("popular fallback")
        
        return " & ".join(reasons) if reasons else "general recommendation"
    
    def recommend_for_product(
        self,
        product_id: str,
        k: int = 10,
        alpha: float = 0.6,
        offset: int = 0,
        diversify: bool = False,
        seed: int = 0
    ) -> Tuple[List[Dict], int]:
        """Get recommendations for a product.
        
        Args:
            product_id: Product ID to get recommendations for
            k: Number of recommendations
            alpha: Weight for content similarity (0-1)
            offset: Offset for pagination
            diversify: Whether to diversify results (not implemented)
            seed: Random seed for tie-breaking
            
        Returns:
            Tuple of (recommendations list, total_available)
        """
        if product_id not in self.product_id_to_idx:
            # Cold start: return top popular items
            return self._get_popular_fallback(k, offset, seed), len(self.catalog_df)
        
        query_idx = self.product_id_to_idx[product_id]
        query_product = self.catalog_df.iloc[query_idx]
        
        # Get all candidate indices (exclude query product)
        candidate_indices = [
            i for i in range(len(self.catalog_df))
            if i != query_idx
        ]
        candidate_ids = [self.idx_to_product_id[i] for i in candidate_indices]
        
        # Compute content similarity
        content_sims = self._get_content_similarity(query_idx, candidate_indices)
        
        # Compute popularity scores
        popularity_scores = self._get_popularity_scores(candidate_ids)
        
        # Combine scores
        combined_scores = alpha * content_sims + (1 - alpha) * popularity_scores
        
        # Set seed for deterministic tie-breaking
        np.random.seed(seed)
        
        # Sort by score (descending), with deterministic tie-breaking
        # Use product_id as secondary sort key for determinism
        sort_keys = [
            (-combined_scores[i], candidate_ids[i])
            for i in range(len(candidate_indices))
        ]
        sorted_indices = sorted(
            range(len(candidate_indices)),
            key=lambda i: sort_keys[i]
        )
        
        # Apply pagination
        total_available = len(sorted_indices)
        paginated_indices = sorted_indices[offset:offset + k]
        
        # Build recommendations
        recommendations = []
        for idx in paginated_indices:
            candidate_idx = candidate_indices[idx]
            candidate_id = candidate_ids[idx]
            candidate_product = self.catalog_df.iloc[candidate_idx]
            
            content_sim = float(content_sims[idx])
            popularity = float(popularity_scores[idx])
            score = float(combined_scores[idx])
            
            reason = self._generate_reason(
                content_sim, popularity, query_product, candidate_product
            )
            
            recommendations.append({
                'product_id': candidate_id,
                'score': round(score, 3),
                'reason': reason
            })
        
        return recommendations, total_available
    
    def _get_popular_fallback(
        self, 
        k: int, 
        offset: int, 
        seed: int
    ) -> List[Dict]:
        """Get popular items as fallback for cold start.
        
        Args:
            k: Number of items
            offset: Offset for pagination
            seed: Random seed
            
        Returns:
            List of recommendations
        """
        # Sort products by popularity
        product_scores = [
            (pid, self.popularity_scores.get(pid, 0.0))
            for pid in self.catalog_df['product_id']
        ]
        product_scores.sort(key=lambda x: (-x[1], x[0]))  # Deterministic
        
        # Apply pagination
        paginated = product_scores[offset:offset + k]
        
        recommendations = []
        for product_id, score in paginated:
            product_row = self.catalog_df[
                self.catalog_df['product_id'] == product_id
            ].iloc[0]
            
            recommendations.append({
                'product_id': product_id,
                'score': round(score, 3),
                'reason': 'popular fallback'
            })
        
        return recommendations
    
    def save(self, filepath: str):
        """Save recommender to file.
        
        Args:
            filepath: Path to save file
        """
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load(filepath: str) -> 'Recommender':
        """Load recommender from file.
        
        Args:
            filepath: Path to load file from
            
        Returns:
            Loaded Recommender instance
        """
        with open(filepath, 'rb') as f:
            return pickle.load(f)

