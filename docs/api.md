# OpenTrace REST API Documentation

All API endpoints are prefixed with `/api/v1` unless noted otherwise.

## Endpoints

### 1. Health Check
- **`GET /api/health`**
- **Response:**
  ```json
  {
    "status": "healthy",
    "service": "OpenTrace",
    "version": "1.0.0",
    "supported_sites_count": 24,
    "engine": "CuratedOSINTAdapter"
  }
  ```

### 2. Supported Sites Directory
- **`GET /api/v1/sites`**
- **Query Parameters:** `category` (optional, e.g. `developer`, `social`)
- **Response:** List of supported platform definitions with check types and patterns.

### 3. Authentication
- **`POST /api/v1/auth/register`**
  - **Body:** `{ "email": "user@example.com", "password": "password123" }`
  - **Status:** `201 Created`
- **`POST /api/v1/auth/login`**
  - **Body:** `{ "email": "user@example.com", "password": "password123" }`
  - **Response:** `{ "access_token": "jwt_token...", "token_type": "bearer" }`
- **`GET /api/v1/auth/me`**
  - **Header:** `Authorization: Bearer <token>`
  - **Response:** Current authenticated user details.

### 4. Investigations
- **`POST /api/v1/investigations`**
  - **Body:**
    ```json
    {
      "type": "username",
      "value": "tarun_dev",
      "options": {
        "deep_search": false,
        "max_depth": 1,
        "categories": ["developer", "forums"]
      }
    }
    ```
  - **Status:** `201 Created`
- **`GET /api/v1/investigations`**
  - **Response:** List of investigations associated with the current session.
- **`GET /api/v1/investigations/{id}`**
  - **Response:** Investigation progress summary and status.
- **`GET /api/v1/investigations/{id}/results`**
  - **Response:** Full findings including discovered profiles, confidence metrics, and evidence records.
- **`GET /api/v1/investigations/{id}/graph`**
  - **Response:** React Flow compatible `{ "nodes": [...], "edges": [...] }` graph structure.
- **`DELETE /api/v1/investigations/{id}`**
  - **Status:** `204 No Content`
  - Purges investigation and related evidence.

