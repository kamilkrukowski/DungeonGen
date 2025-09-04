#!/bin/bash

# Deploy DungeonGen Backend to AWS Lambda
# This script deploys the Flask backend as a Lambda function

set -e

echo "🚀 Starting DungeonGen Backend Lambda Deployment..."

# Check if required environment variables are set
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ Error: GROQ_API_KEY environment variable is not set"
    exit 1
fi

if [ -z "$ADMIN_PASSWORD_HASH" ]; then
    echo "❌ Error: ADMIN_PASSWORD_HASH environment variable is not set"
    exit 1
fi

if [ -z "$JWT_SECRET_KEY" ]; then
    echo "❌ Error: JWT_SECRET_KEY environment variable is not set"
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    exit 1
fi

# Check if Serverless Framework is installed
if ! command -v serverless &> /dev/null; then
    echo "📦 Installing Serverless Framework..."
    npm install -g serverless
fi

# Install serverless plugins
echo "📦 Installing Serverless plugins..."
npm install serverless-python-requirements

# Deploy using Serverless Framework
echo "🚀 Deploying to AWS Lambda..."
serverless deploy --stage prod

echo "✅ Deployment completed successfully!"
echo "📋 API Gateway URL: Check the output above for the API endpoint"
echo "🔧 To update environment variables, run: serverless deploy --stage prod"
