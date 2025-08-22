#!/bin/bash

# Docker deployment script for EUDR Deforestation API
# This script builds and deploys the application using Docker

set -e  # Exit on any error

echo "Starting deployment process..."

# Load environment variables
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

source .env

# Check required environment variables
if [ -z "$COPERNICUS_USERNAME" ] || [ -z "$COPERNICUS_PASSWORD" ] || [ -z "$HEROKU_API_KEY" ]; then
    echo "Error: Missing required environment variables. Please check your .env file."
    echo "Required: COPERNICUS_USERNAME, COPERNICUS_PASSWORD, HEROKU_API_KEY"
    exit 1
fi

echo "Building Docker image..."
docker build -t $APP_NAME:latest .

echo "Tagging image for registry..."
docker tag $APP_NAME:latest $DOCKER_REGISTRY/$APP_NAME:latest

echo "Pushing image to registry..."
docker push $DOCKER_REGISTRY/$APP_NAME:latest

echo "Deploying to Heroku..."
heroku container:login
heroku container:push web --app $APP_NAME
heroku container:release web --app $APP_NAME

echo "Deployment completed successfully!"
echo "Application is available at: https://$APP_NAME.herokuapp.com"
