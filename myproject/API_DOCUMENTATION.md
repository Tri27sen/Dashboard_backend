# Finance Dashboard API - Detailed Documentation

This document provides comprehensive API reference with curl examples and expected responses.

## Table of Contents

1. [Authentication](#authentication)
2. [Response Format](#response-format)
3. [Users API](#users-api)
4. [Transactions API](#transactions-api)
5. [Dashboard Analytics API](#dashboard-analytics-api)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

---

## Authentication

All API endpoints require authentication via token in the `Authorization` header.

### Format
```
Authorization: Token <username>
```

In development, the token is simply the username. For production, implement proper JWT or session-based authentication.

### Example
```bash
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/users/
```

---

## Response Format

### Success Response (2xx)
```json

the token for this is "admin"
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": {
    "id": 1,
    "name": "analyst",
    "description": "Can view and create transactions"
  },
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Error Response (4xx, 5xx)
```json
{
  "error": "Only analysts and admins can access this.",
  "status": "error",
  "code": "PERMISSION_DENIED"
}
```

### Status Codes
- `200 OK` - Successful GET or PATCH request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Users API

### Create User (Admin Only)

**Endpoint:** `POST /api/users/`

**Required Permissions:** Admin role

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "role_name": "analyst"
}
```

**Parameters:**
- `username` (string, required): Unique username, 3+ characters
- `email` (string, required): Valid email address
- `password` (string, required): Minimum 6 characters
- `role_name` (string, required): One of `viewer`, `analyst`, `admin`

**Response:** `201 Created`
```json
{
  "id": 2,
  "username": "john_doe",
  "email": "john@example.com",
  "role": {
    "id": 2,
    "name": "analyst",
    "description": "Can view and create transactions"
  },
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Authorization: Token admin" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_smith",
    "email": "jane@example.com",
    "password": "secure123",
    "role_name": "analyst"
  }'
```

---

### List Users (Admin Only)

**Endpoint:** `GET /api/users/`

**Required Permissions:** Admin role

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": {
      "id": 3,
      "name": "admin",
      "description": "Full management access"
    },
    "is_active": true,
    "created_at": "2024-01-10T08:00:00Z",
    "updated_at": "2024-01-10T08:00:00Z"
  },
  {
    "id": 2,
    "username": "analyst",
    "email": "analyst@example.com",
    "role": {
      "id": 2,
      "name": "analyst",
      "description": "Can view and create transactions"
    },
    "is_active": true,
    "created_at": "2024-01-12T09:15:00Z",
    "updated_at": "2024-01-12T09:15:00Z"
  }
]
```

**Example:**
```bash
curl -H "Authorization: Token admin" \
  http://localhost:8000/api/users/
```

---

### Get User Details

**Endpoint:** `GET /api/users/{id}/`

**Required Permissions:** Admin (for others) or user themselves

**Response:** `200 OK` (same format as Create User response)

**Example:**
```bash
curl -H "Authorization: Token admin" \
  http://localhost:8000/api/users/1/
```

---

### Get Current User Profile

**Endpoint:** `GET /api/users/me/`

**Required Permissions:** Authenticated

**Response:** `200 OK`
```json
{
  "id": 2,
  "username": "analyst",
  "email": "analyst@example.com",
  "role": {
    "id": 2,
    "name": "analyst"
  },
  "is_active": true,
  "created_at": "2024-01-12T09:15:00Z",
  "updated_at": "2024-01-12T09:15:00Z"
}
```

**Example:**
```bash
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/users/me/
```

---

### Update User (Admin Only)

**Endpoint:** `PATCH /api/users/{id}/`

**Required Permissions:** Admin role

**Request Body (all optional):**
```json
{
  "email": "new_email@example.com",
  "is_active": false,
  "password": "new_password"
}
```

**Response:** `200 OK`

**Example:**
```bash
curl -X PATCH http://localhost:8000/api/users/2/ \
  -H "Authorization: Token admin" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

---

### Delete User (Admin Only)

**Endpoint:** `DELETE /api/users/{id}/`

**Required Permissions:** Admin role

**Note:** Marks user as inactive rather than deleting

**Response:** `204 No Content`

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/users/2/ \
  -H "Authorization: Token admin"
```

---

## Transactions API

### Create Transaction (Analyst, Admin)

**Endpoint:** `POST /api/transactions/`

**Required Permissions:** Analyst or Admin role

**Request Body:**
```json
{
  "amount": "1500.00",
  "type": "income",
  "category": "salary",
  "date": "2024-01-15",
  "description": "Monthly salary"
}
```

**Parameters:**
- `amount` (decimal, required): Must be > 0
- `type` (string, required): `income` or `expense`
- `category` (string, required): One of the valid categories
- `date` (date, required): ISO format (YYYY-MM-DD), cannot be future date
- `description` (string, optional): Notes about the transaction

**Valid Categories:**
- Income: `salary`, `bonus`, `investment`
- Expense: `food`, `transportation`, `utilities`, `entertainment`, `health`, `education`, `shopping`, `other`

**Response:** `201 Created`
```json
{
  "id": 5,
  "user": 2,
  "user_username": "analyst",
  "amount": "1500.00",
  "type": "income",
  "category": "salary",
  "date": "2024-01-15",
  "description": "Monthly salary",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_deleted": false
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Token analyst" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "1500.00",
    "type": "income",
    "category": "salary",
    "date": "2024-01-15",
    "description": "Monthly salary"
  }'
```

---

### List Transactions

**Endpoint:** `GET /api/transactions/`

**Required Permissions:** All authenticated roles (viewers see only own, analysts/admins see all)

**Query Parameters:**
- `type` (string): Filter by `income` or `expense`
- `category` (string): Filter by category name
- `start_date` (date): YYYY-MM-DD format
- `end_date` (date): YYYY-MM-DD format

**Response:** `200 OK`
```json
[
  {
    "id": 5,
    "user_username": "analyst",
    "amount": "1500.00",
    "type": "income",
    "category": "salary",
    "date": "2024-01-15",
    "created_at": "2024-01-15T10:30:00Z",
    "is_deleted": false
  },
  {
    "id": 6,
    "user_username": "analyst",
    "amount": "45.50",
    "type": "expense",
    "category": "food",
    "date": "2024-01-15",
    "created_at": "2024-01-15T14:22:00Z",
    "is_deleted": false
  }
]
```

**Examples:**
```bash
# List all transactions
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/transactions/

# Filter by type
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/transactions/?type=income

# Filter by type and category
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/transactions/?type=expense&category=food

# Filter by date range
curl -H "Authorization: Token analyst" \
  "http://localhost:8000/api/transactions/?start_date=2024-01-01&end_date=2024-01-31"
```

---

### Get Transaction Details

**Endpoint:** `GET /api/transactions/{id}/`

**Required Permissions:** Analyst/Admin (see own) or Admin (see all)

**Response:** `200 OK`
```json
{
  "id": 5,
  "user": 2,
  "user_username": "analyst",
  "amount": "1500.00",
  "type": "income",
  "category": "salary",
  "date": "2024-01-15",
  "description": "Monthly salary",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_deleted": false
}
```

**Example:**
```bash
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/transactions/5/
```

---

### Update Transaction (Own or Admin)

**Endpoint:** `PATCH /api/transactions/{id}/`

**Required Permissions:** Analyst (own) or Admin

**Request Body (all optional):**
```json
{
  "amount": "2000.00",
  "category": "bonus",
  "description": "Updated description"
}
```

**Response:** `200 OK`

**Example:**
```bash
curl -X PATCH http://localhost:8000/api/transactions/5/ \
  -H "Authorization: Token analyst" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "2000.00",
    "category": "bonus"
  }'
```

---

### Delete Transaction (Soft Delete)

**Endpoint:** `DELETE /api/transactions/{id}/`

**Required Permissions:** Analyst (own) or Admin

**Note:** Marks as deleted without removing from database

**Response:** `204 No Content`

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/transactions/5/ \
  -H "Authorization: Token analyst"
```

---

### Restore Deleted Transaction (Admin Only)

**Endpoint:** `POST /api/transactions/{id}/restore/`

**Required Permissions:** Admin role

**Response:** `200 OK`
```json
{
  "id": 5,
  "user": 2,
  "user_username": "analyst",
  "amount": "1500.00",
  "type": "income",
  "category": "salary",
  "date": "2024-01-15",
  "description": "Monthly salary",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_deleted": false
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/transactions/5/restore/ \
  -H "Authorization: Token admin"
```

---

## Dashboard Analytics API

### Dashboard Summary

**Endpoint:** `GET /api/dashboard/summary/`

**Required Permissions:** All authenticated roles

**Query Parameters:**
- `start_date` (date, optional): YYYY-MM-DD
- `end_date` (date, optional): YYYY-MM-DD

**Response:** `200 OK`
```json
{
  "total_income": "5700.00",
  "total_expenses": "1495.50",
  "net_balance": "4204.50",
  "period": "all_time",
  "transaction_count": 10
}
```

**Example:**
```bash
# All time summary
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/dashboard/summary/

# Monthly summary
curl -H "Authorization: Token analyst" \
  "http://localhost:8000/api/dashboard/summary/?start_date=2024-01-01&end_date=2024-01-31"
```

---

### Category Breakdown

**Endpoint:** `GET /api/dashboard/category-breakdown/`

**Required Permissions:** All authenticated roles

**Query Parameters:**
- `period` (string): `all_time` (default), `monthly`, or `yearly`

**Response:** `200 OK`
```json
{
  "categories": [
    {
      "name": "salary",
      "amount": "5000.00",
      "type": "income",
      "percentage": "87.72"
    },
    {
      "name": "food",
      "amount": "45.50",
      "type": "expense",
      "percentage": "3.04"
    },
    {
      "name": "transportation",
      "amount": "120.00",
      "type": "expense",
      "percentage": "8.02"
    }
  ]
}
```

**Example:**
```bash
# All time breakdown
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/dashboard/category-breakdown/

# Monthly breakdown
curl -H "Authorization: Token analyst" \
  "http://localhost:8000/api/dashboard/category-breakdown/?period=monthly"
```

---

### Monthly Trends

**Endpoint:** `GET /api/dashboard/monthly-trends/`

**Required Permissions:** All authenticated roles

**Query Parameters:**
- `months` (integer): Number of months to return (default 12, max 60)

**Response:** `200 OK`
```json
{
  "data": [
    {
      "month": "2023-12",
      "income": "5000.00",
      "expenses": "1000.00",
      "net": "4000.00"
    },
    {
      "month": "2024-01",
      "income": "700.00",
      "expenses": "495.50",
      "net": "204.50"
    }
  ]
}
```

**Example:**
```bash
# Last 12 months
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/dashboard/monthly-trends/

# Last 6 months
curl -H "Authorization: Token analyst" \
  "http://localhost:8000/api/dashboard/monthly-trends/?months=6"
```

---

### Recent Activity

**Endpoint:** `GET /api/dashboard/recent-activity/`

**Required Permissions:** All authenticated roles

**Query Parameters:**
- `limit` (integer): Number of recent transactions (default 10, max 100)

**Response:** `200 OK`
```json
{
  "activities": [
    {
      "id": 10,
      "amount": "45.50",
      "type": "expense",
      "category": "food",
      "date": "2024-01-15",
      "description": "Lunch",
      "created_at": "2024-01-15T14:22:00Z"
    },
    {
      "id": 9,
      "amount": "120.00",
      "type": "expense",
      "category": "transportation",
      "date": "2024-01-14",
      "description": "Uber rides",
      "created_at": "2024-01-14T18:45:00Z"
    }
  ]
}
```

**Example:**
```bash
# Last 10 activities
curl -H "Authorization: Token analyst" \
  http://localhost:8000/api/dashboard/recent-activity/

# Last 20 activities
curl -H "Authorization: Token analyst" \
  "http://localhost:8000/api/dashboard/recent-activity/?limit=20"
```

---

## Error Handling

### Validation Error

**Status:** `400 Bad Request`

```json
{
  "error": {
    "amount": ["Amount must be greater than 0."]
  },
  "status": "error",
  "code": "VALIDATION_ERROR"
}
```

### Permission Denied

**Status:** `403 Forbidden`

```json
{
  "error": "Only analysts and admins can access this.",
  "status": "error",
  "code": "PERMISSION_DENIED"
}
```

### Not Found

**Status:** `404 Not Found`

```json
{
  "error": "Not found.",
  "status": "error",
  "code": "NOT_FOUND"
}
```

### Unauthorized

**Status:** `401 Unauthorized`

```json
{
  "error": "Authentication credentials were not provided.",
  "status": "error",
  "code": "UNAUTHORIZED"
}
```

---

## Examples

### Complete Workflow Example

```bash
# 1. Create a new user (as admin)
curl -X POST http://localhost:8000/api/users/ \
  -H "Authorization: Token admin" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newanalyst",
    "email": "newanalyst@example.com",
    "password": "secure_password",
    "role_name": "analyst"
  }'

# 2. Create a transaction (as analyst)
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Token newanalyst" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "3000.00",
    "type": "income",
    "category": "salary",
    "date": "2024-01-15",
    "description": "Salary deposit"
  }'

# 3. Get dashboard summary
curl -H "Authorization: Token newanalyst" \
  http://localhost:8000/api/dashboard/summary/

# 4. Get category breakdown
curl -H "Authorization: Token newanalyst" \
  http://localhost:8000/api/dashboard/category-breakdown/

# 5. Get recent activity
curl -H "Authorization: Token newanalyst" \
  http://localhost:8000/api/dashboard/recent-activity/?limit=5
```

---

## Testing with cURL

All examples use `cURL`. You can also test using:
- **Postman**: Import API endpoints manually
- **Thunder Client**: VS Code extension
- **REST Client**: VS Code extension
- **Python requests**: See test file

---
