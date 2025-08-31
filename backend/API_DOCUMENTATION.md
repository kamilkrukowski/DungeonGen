# DungeonGen API Documentation

## Overview

The DungeonGen API is now fully documented using **Flask-RESTX**, which provides automatic OpenAPI/Swagger documentation generation. This makes it easy for developers to understand and test the API endpoints.

## Accessing the Documentation

### Interactive Swagger UI
- **URL**: `http://localhost:5001/docs`
- **Description**: Interactive web interface for exploring and testing all API endpoints
- **Features**:
  - Try out endpoints directly from the browser
  - View request/response schemas
  - See example requests and responses
  - Test with different parameters

### OpenAPI Specification
- **URL**: `http://localhost:5001/swagger.json`
- **Description**: Machine-readable OpenAPI 2.0 specification
- **Use Cases**:
  - Generate client libraries
  - Import into API testing tools (Postman, Insomnia)
  - Integration with CI/CD pipelines

## Features

### Automatic Documentation
- **Request/Response Models**: All endpoints have documented request and response schemas
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Examples**: Pre-filled example requests for easy testing
- **Validation**: Automatic request validation using Pydantic models

### Security
- **API Key Support**: Configured for API key authentication (X-API-Key header)
- **CORS**: Configured for frontend integration

### Development Features
- **Interactive Testing**: Test endpoints directly from the Swagger UI
- **Schema Validation**: Automatic validation of request/response formats
- **Error Messages**: Clear error messages for debugging

## Usage Examples

### Using the Swagger UI
1. Open `http://localhost:5001/docs` in your browser
2. Click on any endpoint to expand it
3. Click "Try it out" to test the endpoint
4. Fill in the required parameters
5. Click "Execute" to make the request
6. View the response and status code

## Configuration

### Environment Variables
- `PORT`: Server port (default: 5000)
- `FLASK_ENV`: Environment mode (development/production)
- `GROQ_API_KEY`: API key for GROQ service (required for generation)

### CORS Configuration
The API is configured to accept requests from:
- `http://localhost:3000` (local frontend development)
- `http://frontend:3000` (Docker container)

## Benefits of Flask-RESTX

1. **Automatic Documentation**: No need to manually maintain API docs
2. **Interactive Testing**: Built-in testing interface
3. **Schema Validation**: Automatic request/response validation
4. **Code Generation**: Can generate client libraries
5. **Standards Compliant**: Follows OpenAPI 2.0 specification
6. **Easy Maintenance**: Documentation stays in sync with code

## Next Steps

- Configure your GROQ API key to test dungeon generation
- Explore the interactive documentation at `/docs`
- Use the generated OpenAPI spec for client integration
- Consider adding more endpoints as your API grows

## Troubleshooting

### Common Issues
1. **Port 5000 in use**: Use `PORT=5001 python app.py` to use a different port
2. **GROQ API not configured**: Set the `GROQ_API_KEY` environment variable
3. **CORS errors**: Check that your frontend URL is in the allowed origins

### Getting Help
- Check the server logs for detailed error messages
- Use the interactive documentation to test endpoints
- Verify your environment variables are set correctly
