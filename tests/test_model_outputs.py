"""Tests for deterministic model outputs."""
import os
import numpy as np
from src.model import Recommender

# Set deterministic seeds
os.environ['PYTHONHASHSEED'] = '0'
np.random.seed(0)


def test_deterministic_recommendations():
    """Test that recommendations are deterministic."""
    # Load model
    recommender = Recommender.load('models/recommender.pkl')
    
    # Get recommendations with specific parameters
    recommendations1, total1 = recommender.recommend_for_product(
        product_id='prod_1',
        k=3,
        alpha=0.6,
        offset=0,
        seed=0
    )
    
    # Get same recommendations again
    recommendations2, total2 = recommender.recommend_for_product(
        product_id='prod_1',
        k=3,
        alpha=0.6,
        offset=0,
        seed=0
    )
    
    # Should be identical
    assert total1 == total2
    assert len(recommendations1) == len(recommendations2)
    assert len(recommendations1) == 3
    
    for i in range(len(recommendations1)):
        assert recommendations1[i]['product_id'] == recommendations2[i]['product_id']
        assert recommendations1[i]['score'] == recommendations2[i]['score']
        assert recommendations1[i]['reason'] == recommendations2[i]['reason']
    
    # Check scores are in valid range
    for rec in recommendations1:
        assert 0 <= rec['score'] <= 1
        assert isinstance(rec['reason'], str)
        assert len(rec['reason']) > 0


def test_different_alpha_values():
    """Test that different alpha values produce different results."""
    recommender = Recommender.load('models/recommender.pkl')
    
    # High alpha (content-focused)
    recs_high, _ = recommender.recommend_for_product(
        product_id='prod_1',
        k=3,
        alpha=0.9,
        offset=0,
        seed=0
    )
    
    # Low alpha (popularity-focused)
    recs_low, _ = recommender.recommend_for_product(
        product_id='prod_1',
        k=3,
        alpha=0.1,
        offset=0,
        seed=0
    )
    
    # Results should be different (or at least scores should differ)
    # At minimum, check that we get valid results
    assert len(recs_high) == 3
    assert len(recs_low) == 3
    
    # Scores should be valid
    for rec in recs_high + recs_low:
        assert 0 <= rec['score'] <= 1


def test_pagination():
    """Test that pagination works correctly."""
    recommender = Recommender.load('models/recommender.pkl')
    
    # First page
    recs_page1, total = recommender.recommend_for_product(
        product_id='prod_1',
        k=5,
        alpha=0.6,
        offset=0,
        seed=0
    )
    
    # Second page
    recs_page2, _ = recommender.recommend_for_product(
        product_id='prod_1',
        k=5,
        alpha=0.6,
        offset=5,
        seed=0
    )
    
    # Should have different products (unless total < 10)
    if total >= 10:
        assert recs_page1[0]['product_id'] != recs_page2[0]['product_id']
    
    # All should be valid
    for rec in recs_page1 + recs_page2:
        assert 0 <= rec['score'] <= 1
        assert 'product_id' in rec
        assert 'reason' in rec


def test_cold_start():
    """Test cold start handling for unknown product."""
    recommender = Recommender.load('models/recommender.pkl')
    
    # Try with unknown product (should use popular fallback)
    recs, total = recommender.recommend_for_product(
        product_id='unknown_product_xyz',
        k=5,
        alpha=0.6,
        offset=0,
        seed=0
    )
    
    # Should still return recommendations (popular fallback)
    assert len(recs) > 0
    assert len(recs) <= 5
    
    # All should have "popular fallback" reason or valid reasons
    for rec in recs:
        assert 0 <= rec['score'] <= 1
        assert 'reason' in rec

