# Authentication Guide

This project now includes proper JWT-based authentication with password hashing.

## Features

- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: Passwords are hashed using bcrypt
- **Token Expiration**: Tokens expire after 30 minutes (configurable)
- **User Management**: Create, authenticate, and manage users
- **CORS Support**: Cross-origin requests are properly handled

## Default Credentials

For development, a default admin user is created:
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ Change these credentials in production!**

## API Endpoints

### Authentication

#### 1. Login (Form Data)
```bash
POST /api/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@drug-repurposing.com"
  }
}
```

#### 2. Login (JSON)
```bash
POST /api/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

#### 3. Register New User
```bash
POST /api/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securepassword123"
}
```

#### 4. Get Current User Info
```bash
GET /api/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@drug-repurposing.com",
  "is_active": true
}
```

## Using Tokens in Protected Endpoints

All protected endpoints require an `Authorization` header with a bearer token:

```bash
GET /api/diseases
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Protected Endpoints

- `POST /api/upload_gene_profile` - Upload user's gene profile
- `GET /api/diseases` - Get list of diseases
- `GET /api/process` - Process disease analysis
- `GET /api/similar_diseases` - Find similar diseases
- `GET /api/compare_drugs` - Compare two drugs
- `GET /api/symptom_discovery` - Discover diseases by symptoms

## Example: Complete Flow

### 1. Register a user
```bash
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researcher",
    "email": "researcher@example.com",
    "password": "MySecurePass123!"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researcher",
    "password": "MySecurePass123!"
  }'
```

### 3. Use the token in API calls
```bash
curl -X GET "http://localhost:8000/api/diseases" \
  -H "Authorization: Bearer <your_access_token>"
```

## Security Notes

1. **Change SECRET_KEY**: Update `SECRET_KEY` in `backend/utils/security.py` for production
2. **Use HTTPS**: Always use HTTPS in production
3. **Token Expiration**: Tokens expire after 30 minutes; users need to login again
4. **Password Requirements**: Implement password validation (minimum length, complexity, etc.)
5. **User Database**: Current implementation uses JSON file; migrate to SQL database for production

## File Structure

```
backend/
├── utils/
│   ├── security.py        # JWT and password hashing utilities
│   ├── database.py        # User database management
│   └── __init__.py
├── models/
│   ├── user.py            # User models/schemas
│   └── __init__.py
└── app.py                 # Main FastAPI application
```

## Dependencies

Added to `requirements.txt`:
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data parsing
- `pydantic-settings` - Configuration management

## Testing in Swagger UI

1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Choose "OAuth2PasswordBearer" 
4. Login with username and password
5. The token will be automatically added to subsequent requests

## User Database

Users are stored in `data/users.json`. Structure:

```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@drug-repurposing.com",
      "password_hash": "$2b$12$...",
      "is_active": true
    }
  ]
}
```

**Never commit this file with real passwords to version control!**
