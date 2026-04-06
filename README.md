# Finance Dashboard Backend

A production-ready Django REST API backend for a finance dashboard system with role-based access control, financial records management, and analytics APIs.

## Overview

This is a clean, well-structured backend that demonstrates:

- **Layered Architecture**: Separation of concerns with models, serializers, views, services, and permissions
- **Role-Based Access Control (RBAC)**: Three role levels (Viewer, Analyst, Admin) with granular permission checks
- **RESTful APIs**: Comprehensive endpoints for users, financial records, and analytics
- **Data Validation**: Robust input validation and error handling
- **Database Design**: Well-normalized relational schema with SQLite (easily swappable for PostgreSQL)
- **Professional Code Quality**: Clean, maintainable, and well-documented code

## Key Features

### 1. User & Role Management
- Create and manage users with role assignments
- Three predefined roles: Viewer, Analyst, Admin
- Active/Inactive user status management
- Role-based permission enforcement

### 2. Financial Records Management
- Create, read, update, and delete financial transactions
- Support for Income/Expense transaction types
- Categorization of transactions
- Date-based filtering and searching
- Soft delete functionality

### 3. Dashboard Summary APIs
- Total income, expenses, and net balance
- Category-wise breakdown
- Monthly/weekly trends
- Recent activity feed
- Expense analysis by category

### 4. Access Control
- Middleware-based permission enforcement
- Custom permission classes for different role levels
- View-level and object-level access control
- Clear separation between what each role can access

### 5. Validation & Error Handling
- Comprehensive input validation
- Meaningful error messages
- Appropriate HTTP status codes
- Protection against invalid operations

## Technology Stack

- **Framework**: Django 4.2+ & Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production-ready)
- **Python**: 3.10+
- **Authentication**: Token-based (JWT-compatible structure)
- **Testing**: Django TestCase with example tests

## Project Structure

```
finance_backend/
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
├── finance_project/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── __init__.py
└── finance_app/
    ├── models.py              # Data models for User, Role, Transaction
    ├── serializers.py         # DRF serializers for API responses
    ├── views.py               # API viewsets and views
    ├── permissions.py         # Custom permission classes
    ├── services.py            # Business logic and analytics
    ├── utils.py               # Helper functions and validators
    ├── urls.py                # URL routing
    ├── tests.py               # Test cases
    └── migrations/            # Database migrations
```

## Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/Tri27sen/Dashboard_backend.git

# Move into the project directory
cd finance_backend

# Install dependencies (Pipenv)
pipenv install

# Activate virtual environment
pipenv shell

# Run database migrations
python manage.py migrate

# Run the development server
python manage.py runserver


### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create initial seed data (optional)
python manage.py shell < seed_data.py
```

### 4. Run Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Endpoints

### Authentication
All requests should include a token header (mock token for development):
```
Authorization: Token <user-token>
```

### Users & Roles

**Create User** (Admin only)
```
POST /api/users/
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "role": "analyst"
}
```

**List Users** (Admin only)
```
GET /api/users/
```

**Get User Details**
```
GET /api/users/{id}/
```

**Update User** (Admin only)
```
PATCH /api/users/{id}/
```

### Financial Records

**Create Transaction** (Analyst, Admin only)
```
POST /api/transactions/
{
  "amount": 1500.00,
  "type": "income",
  "category": "salary",
  "date": "2024-01-15",
  "description": "Monthly salary"
}
```

**List Transactions** (Viewer+)
```
GET /api/transactions/
GET /api/transactions/?type=income&category=salary&start_date=2024-01-01
```

**Get Transaction Details**
```
GET /api/transactions/{id}/
```

**Update Transaction** (Analyst, Admin only)
```
PATCH /api/transactions/{id}/
```

**Delete Transaction** (Analyst, Admin only)
```
DELETE /api/transactions/{id}/
```

### Dashboard Analytics

**Dashboard Summary** (All roles)
```
GET /api/dashboard/summary/
Response:
{
  "total_income": 5000.00,
  "total_expenses": 2000.00,
  "net_balance": 3000.00,
  "period": "all_time"
}
```

**Category Breakdown** (All roles)
```
GET /api/dashboard/category-breakdown/?period=monthly
Response:
{
  "categories": [
    {"name": "salary", "amount": 3000.00, "type": "income"},
    {"name": "food", "amount": 500.00, "type": "expense"}
  ]
}
```

**Monthly Trends** (All roles)
```
GET /api/dashboard/monthly-trends/
Response:
{
  "data": [
    {"month": "2024-01", "income": 5000, "expenses": 2000},
    {"month": "2024-02", "income": 5000, "expenses": 2500}
  ]
}
```

**Recent Activity** (All roles)
```
GET /api/dashboard/recent-activity/?limit=10
Response:
{
  "activities": [
    {
      "id": 1,
      "amount": 1500.00,
      "type": "income",
      "category": "salary",
      "date": "2024-01-15",
      "description": "Monthly salary"
    }
  ]
}
```

## Role Permissions

| Action | Viewer | Analyst | Admin |
|--------|--------|---------|-------|
| View Dashboard | ✓ | ✓ | ✓ |
| View Transactions | ✓ | ✓ | ✓ |
| Create Transaction | ✗ | ✓ | ✓ |
| Edit Transaction | ✗ | ✓ | ✓ |
| Delete Transaction | ✗ | ✓ | ✓ |
| View Users | ✗ | ✗ | ✓ |
| Manage Users | ✗ | ✗ | ✓ |

## Design Decisions & Assumptions

### 1. Database Choice
- **SQLite** for development and simplicity
- **Easily swappable** to PostgreSQL for production
- Relational database for clean data modeling and referential integrity

### 2. Authentication
- Mock token-based authentication for development
- Can be extended with Django Allauth or Simple JWT
- Token stored in `Authorization` header

### 3. Soft Deletes
- Transactions support soft delete (keeps data for auditing)
- A `deleted_at` field tracks deletion time
- Deleted records excluded from normal queries

### 4. Date Handling
- All dates in YYYY-MM-DD format (ISO 8601)
- Timezone-aware datetime storage (UTC)
- Aggregations handle partial months gracefully

### 5. Permission Model
- View-level permission checks via custom permission classes
- Object-level checks where needed
- Explicit deny-by-default approach (more secure)

### 6. API Design
- RESTful design with resource-based URLs
- Standard HTTP methods (GET, POST, PATCH, DELETE)
- Consistent error response format
- Pagination ready (can be added without breaking changes)

## Validation & Error Handling

### Input Validation
- Amount must be positive
- Type must be 'income' or 'expense'
- Category must be non-empty string
- Date must be valid ISO format
- Email must be valid format

### Error Responses
```json
{
  "error": "Permission denied. Only admins can create users.",
  "status": "error",
  "code": "PERMISSION_DENIED"
}
```

### Status Codes Used
- `200 OK`: Successful GET/PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Missing/invalid authentication
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Testing

Run the test suite:

```bash
python manage.py test
```

Test coverage includes:
- User creation and role assignment
- Permission checks for each role
- Transaction CRUD operations
- Analytics calculation correctness
- Input validation
- Error handling

## Running with Different Configurations

### Production Setup

1. Set `DEBUG = False` in settings.py
2. Use PostgreSQL database
3. Use environment variables for secrets
4. Enable CSRF protection and secure headers
5. Deploy with Gunicorn/uWSGI

```bash
# Example with Gunicorn
gunicorn finance_project.wsgi
```

### Adding Authentication with JWT

Replace the mock token system:

```bash
pip install djangorestframework-simplejwt
```

Update settings.py to use SimpleJWT and update the permission classes.

## Future Enhancements

1. **Advanced Filtering**: More complex transaction filters
2. **Pagination**: Cursor-based pagination for large datasets
3. **Search**: Full-text search on transaction descriptions
4. **Bulk Operations**: Batch create/update transactions
5. **Rate Limiting**: Throttle API requests per user
6. **Caching**: Redis for dashboard analytics caching
7. **File Export**: CSV/Excel export of transactions
8. **Audit Logging**: Track all data changes
9. **Multi-currency**: Support multiple currencies
10. **Budget Tracking**: Set and monitor budgets

## Troubleshooting

### Issue: "No such table" error
**Solution**: Run `python manage.py migrate`

### Issue: "Permission denied" on allowed action
**Solution**: Check user's role assignment in database

### Issue: CORS errors
**Solution**: Install django-cors-headers and add to INSTALLED_APPS

## Code Quality Notes

- **Follows PEP 8** style guidelines
- **DRY Principle**: Reusable components and services
- **Separation of Concerns**: Models, serializers, views, and business logic are separate
- **Clear Naming**: Self-documenting code with meaningful variable names
- **Docstrings**: All complex functions documented
- **Consistent Error Handling**: Centralized exception handling
- **Testable Design**: Services can be tested independently

## License

MIT License - Feel free to use this project as a reference or starting point.

## Support

For questions or issues, refer to the inline code documentation and commit messages that explain design decisions.
