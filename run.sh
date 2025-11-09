#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t shl-recommender .

echo "Starting container..."
docker run -p 8000:8000 shl-recommender

