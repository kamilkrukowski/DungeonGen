#!/bin/bash

# Script to upload local .env file to AWS Lambda function
# Usage: ./upload-env.sh

set -e

# Configuration
FUNCTION_NAME="dungeongen7bea1f1c-dev"
ENV_FILE=".env"
TEMP_JSON="/tmp/lambda_env.json"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE file not found!"
    echo "Please create a .env file with your environment variables."
    exit 1
fi

echo "Reading environment variables from $ENV_FILE..."

# Start building JSON with required variables
cat > "$TEMP_JSON" << EOF
{
  "ENV": "dev",
  "REGION": "us-east-1"
EOF

# Read each line from .env file and add to JSON
first_var=false
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Extract key and value
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        
        # Remove quotes if present
        value=$(echo "$value" | sed 's/^"//;s/"$//' | sed "s/^'//;s/'$//")
        
        # Add comma before each variable (except the first one from .env)
        if [ "$first_var" = false ]; then
            echo "," >> "$TEMP_JSON"
        fi
        first_var=false
        
        # Add key-value pair to JSON
        printf "  \"%s\": \"%s\"" "$key" "$value" >> "$TEMP_JSON"
        echo "  Found: $key"
    fi
done < "$ENV_FILE"

# Close JSON
echo "" >> "$TEMP_JSON"
echo "}" >> "$TEMP_JSON"

echo ""
echo "Updating Lambda function: $FUNCTION_NAME"
echo "Environment variables:"
cat "$TEMP_JSON" | jq '.'

# Create the full update request JSON
UPDATE_JSON="/tmp/lambda_update.json"
cat > "$UPDATE_JSON" << EOF
{
  "FunctionName": "$FUNCTION_NAME",
  "Environment": {
    "Variables": $(cat "$TEMP_JSON")
  }
}
EOF

# Update Lambda function configuration
aws lambda update-function-configuration --cli-input-json "file://$UPDATE_JSON"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully updated Lambda function environment variables!"
    echo ""
    echo "You can verify the update by running:"
    echo "aws lambda get-function-configuration --function-name $FUNCTION_NAME --query 'Environment.Variables'"
else
    echo ""
    echo "❌ Failed to update Lambda function environment variables!"
    exit 1
fi

# Clean up
rm -f "$TEMP_JSON" "$UPDATE_JSON"
