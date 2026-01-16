#!/bin/bash

# Deployment script for JobScoutAI

set -e

echo "🚀 JobScoutAI Deployment Script"
echo "================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI not found. Please install it first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your Yutori API key before continuing."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Build the application
echo "📦 Building SAM application..."
sam build

# Deploy (first time will prompt for Yutori API key)
echo "🚀 Deploying to AWS..."
if [ -f samconfig.toml ] && grep -q "s3_bucket" samconfig.toml; then
    # Subsequent deployments
    sam deploy
else
    # First deployment - use guided mode
    echo "⚠️  First deployment detected. Running guided setup..."
    sam deploy --guided
fi

echo "✅ Deployment complete!"
echo ""
echo "Get your API endpoint with:"
echo "aws cloudformation describe-stacks --stack-name jobscoutai --query 'Stacks[0].Outputs'"
