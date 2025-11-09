# Deployment Guide

## Quick Deployment Steps

### Step 1: Push to GitHub

```bash
cd /Users/nitin/Documents/Developer/shl
git add .
git commit -m "Initial submission: SHL recommender — API, model, data, tests, Dockerfile"
git push origin main
```

### Step 2: Deploy on Render.com (Recommended)

1. Go to https://render.com and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub account and select your repository
4. Configure the service:
   - **Name**: `shl-recommender`
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Build Command**: `pip install -r requirements.txt && python train_and_serialize.py`
   - **Start Command**: `uvicorn src.app:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variable:
   - Key: `PYTHONHASHSEED`
   - Value: `0`
6. Click "Create Web Service"
7. Wait 5-10 minutes for deployment
8. Your app will be live at: `https://shl-recommender.onrender.com`

### Step 3: Test Your Deployment

Once deployed, test these endpoints:

**Health Check:**
```bash
curl https://shl-recommender.onrender.com/health
```

**Text Search:**
```bash
curl "https://shl-recommender.onrender.com/search?query=headphones&k=5"
```

**Search and Recommend:**
```bash
curl "https://shl-recommender.onrender.com/search-and-recommend?query=wireless%20headphones&k=10&alpha=0.6"
```

**Product Recommendations:**
```bash
curl "https://shl-recommender.onrender.com/recommend?product_id=prod_1&k=10&alpha=0.6"
```

## Alternative: Railway.app

1. Go to https://railway.app and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect the Dockerfile
5. Add environment variable: `PYTHONHASHSEED=0`
6. Deploy automatically

## Alternative: Heroku

```bash
# Install Heroku CLI first
heroku login
heroku create shl-recommender
heroku config:set PYTHONHASHSEED=0
git push heroku main
```

## API Endpoints Summary

### 1. Text Search
- **URL**: `/search?query=<text>&k=<number>`
- **Method**: GET
- **Returns**: JSON with matching products

### 2. Search and Recommend
- **URL**: `/search-and-recommend?query=<text>&k=<number>&alpha=<0-1>`
- **Method**: GET
- **Returns**: JSON with matched product and recommendations

### 3. Product Recommendations
- **URL**: `/recommend?product_id=<id>&k=<number>&alpha=<0-1>&cursor=<cursor>`
- **Method**: GET
- **Returns**: JSON with recommendations

### 4. Health Check
- **URL**: `/health`
- **Method**: GET
- **Returns**: `{"status": "healthy"}`

## Troubleshooting

- **Build fails**: Check that `models/recommender.pkl` exists or the build command runs `train_and_serialize.py`
- **Port errors**: Ensure `$PORT` environment variable is used in start command
- **Model not loading**: Verify the model file is committed to git (it's under 100KB, so it should be fine)

