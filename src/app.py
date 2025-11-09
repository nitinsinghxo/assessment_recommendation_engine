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


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

