# SHL Assessment Recommendation Engine

A production-ready FastAPI service that provides product recommendations using a hybrid content-based and popularity-based approach.

## Features

- Hybrid recommendation system combining TF-IDF content similarity with popularity scores
- Deterministic outputs with seed-based tie-breaking
- Cursor-based pagination for large result sets
- Explainable recommendations with reasoning
- Cold-start handling for new products

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Training (Optional)

The model artifact `models/recommender.pkl` is already included. To regenerate it:

```bash
python train_and_serialize.py
```

### Running the Service

```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Running Tests

```bash
pytest -q
```

### Docker

Build and run with Docker:

```bash
docker build -t shl-recommender .
docker run -p 8000:8000 shl-recommender
```

Or use the convenience script:

```bash
chmod +x run.sh
./run.sh
```

## Deployment

### Option 1: Render.com (Recommended - Free)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) and sign up/login
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: shl-recommender
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt && python train_and_serialize.py`
   - **Start Command**: `uvicorn src.app:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add `PYTHONHASHSEED=0`
6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Your app will be available at `https://shl-recommender.onrender.com`

### Option 2: Railway.app

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) and sign up
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect the Dockerfile and deploy
6. Your app will be available at a Railway-provided URL

### Option 3: Heroku

1. Install Heroku CLI
2. Run:
   ```bash
   heroku create shl-recommender
   heroku config:set PYTHONHASHSEED=0
   git push heroku main
   ```

## API Endpoints

### 1. Text Search Endpoint

**GET** `/search?query=<text>&k=<number>`

Search for products by text query. Searches in product name, description, brand, and category.

**Query Parameters:**
- `query` (required): Text query to search for
- `k` (optional, default=10): Number of results to return

**Example Request:**

```bash
curl "http://localhost:8000/search?query=headphones&k=5"
```

**Example Response:**

```json
{
  "query": "headphones",
  "total_results": 3,
  "items": [
    {
      "product_id": "prod_1",
      "product_name": "Wireless Bluetooth Headphones",
      "brand": "AudioTech",
      "category": "Electronics",
      "price": 129.99,
      "description": "High-quality wireless headphones with noise cancellation..."
    },
    {
      "product_id": "prod_15",
      "product_name": "Noise Cancelling Headphones",
      "brand": "AudioTech",
      "category": "Electronics",
      "price": 199.99,
      "description": "Over-ear headphones with active noise cancellation..."
    }
  ]
}
```

### 2. Search and Recommend Endpoint

**GET** `/search-and-recommend?query=<text>&k=<number>&alpha=<0-1>`

Search for a product by text, then get recommendations for the first match.

**Query Parameters:**
- `query` (required): Text query to find a product
- `k` (optional, default=10): Number of recommendations to return
- `alpha` (optional, default=0.6): Weight for content similarity (0-1)

**Example Request:**

```bash
curl "http://localhost:8000/search-and-recommend?query=wireless%20headphones&k=10&alpha=0.6"
```

**Example Response:**

```json
{
  "query": "wireless headphones",
  "matched_product": {
    "product_id": "prod_1",
    "product_name": "Wireless Bluetooth Headphones",
    "brand": "AudioTech",
    "category": "Electronics"
  },
  "recommendations": [
    {
      "product_id": "prod_15",
      "score": 0.847,
      "reason": "strong content match & same brand"
    },
    {
      "product_id": "prod_11",
      "score": 0.732,
      "reason": "high text similarity"
    }
  ],
  "total_available": 49
}
```

### 3. Product Recommendations

**GET** `/recommend`

Get product recommendations for a given product.

**Query Parameters:**
- `product_id` (required): The product ID to get recommendations for
- `k` (optional, default=10): Number of recommendations to return
- `alpha` (optional, default=0.6): Weight for content similarity (0-1). Higher values favor content similarity over popularity
- `cursor` (optional): Pagination cursor from previous response
- `diversify` (optional, default=false): Whether to diversify results

**Example Request:**

```bash
curl "http://localhost:8000/recommend?product_id=prod_1&k=10&alpha=0.6"
```

**Example Response:**

```json
{
  "product_id": "prod_1",
  "product_name": "Wireless Bluetooth Headphones",
  "alpha": 0.6,
  "page_size": 10,
  "offset": 0,
  "total_available": 49,
  "items": [
    {
      "product_id": "prod_15",
      "score": 0.847,
      "reason": "strong content match & same brand"
    },
    {
      "product_id": "prod_23",
      "score": 0.732,
      "reason": "high text similarity"
    },
    {
      "product_id": "prod_8",
      "score": 0.689,
      "reason": "same category & moderate popularity"
    }
  ],
  "next_cursor": "cHJvZF8xfDB8MA=="
}
```

**Error Response (404):**

```json
{
  "error": "product_id not found"
}
```

### 4. Health Check

**GET** `/health`

Check if the service is running.

**Example Request:**

```bash
curl "http://localhost:8000/health"
```

**Example Response:**

```json
{
  "status": "healthy"
}
```

## Architecture

- **src/app.py**: FastAPI application with `/recommend`, `/search`, and `/search-and-recommend` endpoints
- **src/model.py**: Recommender class with hybrid recommendation logic
- **src/features.py**: TF-IDF vectorization and feature engineering
- **src/utils.py**: Cursor encoding/decoding and utility functions
- **train_and_serialize.py**: Model training script
- **data/sample_catalog.csv**: Product catalog (50 products)
- **data/sample_interactions.csv**: User interaction data (200 interactions)
- **models/recommender.pkl**: Pre-trained model artifact

## Determinism

All outputs are deterministic through:
- `PYTHONHASHSEED=0` environment variable
- `np.random.seed(0)` in all relevant scripts
- Deterministic tie-breaking using product IDs

## License

This is a submission for SHL Assessment.

