"""FastAPI application for product recommendations."""
import os
from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from src.model import Recommender
from src.utils import encode_cursor, decode_cursor

# Set deterministic hash seed
os.environ['PYTHONHASHSEED'] = '0'

app = FastAPI(title="SHL Recommendation Engine")

# Load recommender model
try:
    recommender = Recommender.load('models/recommender.pkl')
except Exception as e:
    raise RuntimeError(f"Failed to load model: {e}")


@app.get("/recommend")
async def recommend(
    product_id: str = Query(..., description="Product ID to get recommendations for"),
    k: int = Query(10, ge=1, le=100, description="Number of recommendations"),
    alpha: float = Query(0.6, ge=0.0, le=1.0, description="Content similarity weight"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    diversify: bool = Query(False, description="Whether to diversify results")
):
    """Get product recommendations.
    
    Args:
        product_id: Product ID to get recommendations for
        k: Number of recommendations to return
        alpha: Weight for content similarity (0-1)
        cursor: Pagination cursor from previous response
        diversify: Whether to diversify results (not implemented)
        
    Returns:
        JSON response with recommendations
    """
    # Decode cursor if provided
    offset = 0
    seed = 0
    if cursor:
        try:
            decoded_product_id, decoded_offset, decoded_seed = decode_cursor(cursor)
            # Validate cursor matches current request
            if decoded_product_id != product_id:
                raise ValueError("Cursor product_id mismatch")
            offset = decoded_offset
            seed = decoded_seed
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid cursor")
    
    # Check if product exists
    if product_id not in recommender.catalog_df['product_id'].values:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"error": "product_id not found"}
        )
    
    # Get product name
    product_row = recommender.catalog_df[
        recommender.catalog_df['product_id'] == product_id
    ].iloc[0]
    product_name = product_row['product_name']
    
    # Get recommendations
    recommendations, total_available = recommender.recommend_for_product(
        product_id=product_id,
        k=k,
        alpha=alpha,
        offset=offset,
        diversify=diversify,
        seed=seed
    )
    
    # Generate next cursor if there are more results
    next_cursor = None
    if offset + k < total_available:
        next_cursor = encode_cursor(product_id, offset + k, seed)
    
    return {
        "product_id": product_id,
        "product_name": product_name,
        "alpha": round(alpha, 3),
        "page_size": k,
        "offset": offset,
        "total_available": total_available,
        "items": recommendations,
        "next_cursor": next_cursor
    }


@app.get("/search")
async def search(
    query: str = Query(..., description="Text query to search for products"),
    k: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """Search for products by text query and return matching products.
    
    Args:
        query: Text query to search for (searches in product name, description, brand, category)
        k: Number of results to return
        
    Returns:
        JSON response with matching products
    """
    import pandas as pd
    import numpy as np
    
    # Search in product name, description, brand, and category
    catalog_df = recommender.catalog_df
    
    # Create search text by combining relevant fields
    search_text = (
        catalog_df['product_name'].fillna('').str.lower() + ' ' +
        catalog_df['description'].fillna('').str.lower() + ' ' +
        catalog_df['brand'].fillna('').str.lower() + ' ' +
        catalog_df['category'].fillna('').str.lower()
    )
    
    # Simple text matching (case-insensitive)
    query_lower = query.lower()
    matches = search_text.str.contains(query_lower, na=False, regex=False)
    
    if not matches.any():
        return {
            "query": query,
            "total_results": 0,
            "items": []
        }
    
    # Get matching products
    matched_products = catalog_df[matches].head(k)
    
    # Build response
    items = []
    for _, row in matched_products.iterrows():
        items.append({
            "product_id": row['product_id'],
            "product_name": row['product_name'],
            "brand": row['brand'],
            "category": row['category'],
            "price": float(row['price']) if pd.notna(row['price']) else None,
            "description": row['description']
        })
    
    return {
        "query": query,
        "total_results": int(matches.sum()),
        "items": items
    }


@app.get("/search-and-recommend")
async def search_and_recommend(
    query: str = Query(..., description="Text query to find a product"),
    k: int = Query(10, ge=1, le=100, description="Number of recommendations"),
    alpha: float = Query(0.6, ge=0.0, le=1.0, description="Content similarity weight")
):
    """Search for a product by text, then get recommendations for the first match.
    
    Args:
        query: Text query to find a product
        k: Number of recommendations to return
        alpha: Weight for content similarity (0-1)
        
    Returns:
        JSON response with search results and recommendations
    """
    import pandas as pd
    
    # First, search for the product
    catalog_df = recommender.catalog_df
    search_text = (
        catalog_df['product_name'].fillna('').str.lower() + ' ' +
        catalog_df['description'].fillna('').str.lower()
    )
    
    query_lower = query.lower()
    matches = search_text.str.contains(query_lower, na=False, regex=False)
    
    if not matches.any():
        return {
            "query": query,
            "matched_product": None,
            "error": "No products found matching the query",
            "recommendations": []
        }
    
    # Get the first matching product
    matched_product = catalog_df[matches].iloc[0]
    product_id = matched_product['product_id']
    
    # Get recommendations for this product
    recommendations, total_available = recommender.recommend_for_product(
        product_id=product_id,
        k=k,
        alpha=alpha,
        offset=0,
        diversify=False,
        seed=0
    )
    
    return {
        "query": query,
        "matched_product": {
            "product_id": product_id,
            "product_name": matched_product['product_name'],
            "brand": matched_product['brand'],
            "category": matched_product['category']
        },
        "recommendations": recommendations,
        "total_available": total_available
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

