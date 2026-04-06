# Architecture & Design Decisions

This document explains the architectural choices, design patterns, and reasoning behind the Finance Dashboard Backend.

## Table of Contents

1. [Overall Architecture](#overall-architecture)
2. [Layered Design Pattern](#layered-design-pattern)
3. [Database Design](#database-design)
4. [Authentication & Authorization](#authentication--authorization)
5. [API Design](#api-design)
6. [Error Handling](#error-handling)
7. [Testing Strategy](#testing-strategy)
8. [Security Considerations](#security-considerations)

---

## Overall Architecture

The backend follows a **three-tier layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│          HTTP Layer (Views)                  │
│  - Handle requests/responses                 │
│  - Permission checks                        │
│  - Request validation                       │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│       Business Logic Layer (Services)        │
│  - Financial calculations                   │
│  - Analytics processing                     │
│  - Data aggregations                        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│       Data Access Layer (Models)             │
│  - Database entities                        │
│  - Relationships                            │
│  - Soft deletes                             │
└─────────────────────────────────────────────┘
```

### Benefits

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Testability**: Layers can be tested independently
3. **Reusability**: Services can be used by multiple views
4. **Maintainability**: Clear structure easy to understand and modify
5. **Scalability**: Easy to add caching, queuing, or other layers

---

## Layered Design Pattern

### Layer 1: Views (HTTP Layer)

**File:** `views.py`

**Responsibility:**
- Handle HTTP requests and responses
- Parse query parameters
- Check permissions
- Serialize/deserialize data
- Return appropriate HTTP status codes

**Key Characteristics:**
- Thin views - delegates business logic to services
- Uses DRF ViewSets for consistency
- Permission classes for access control
- Explicit error handling

**Example:**
```python
class DashboardSummaryView(APIView):
    """View handles HTTP request, service handles logic."""
    
    permission_classes = [IsAuthenticated, CanAccessDashboard]
    
    def get(self, request):
        # Parse parameters
        start_date = request.query_params.get('start_date')
        
        # Delegate to service
        summary = FinanceService.get_dashboard_summary(
            request.user,
            start_date=start_date
        )
        
        # Serialize and return
        serializer = DashboardSummarySerializer(summary)
        return Response(serializer.data)
```

### Layer 2: Services (Business Logic)

**File:** `services.py`

**Responsibility:**
- Implement business logic
- Perform calculations
- Handle data aggregations
- Remain independent of HTTP context

**Key Characteristics:**
- Static methods for easy testing
- No knowledge of HTTP/requests
- Can be called from views or management commands
- Focused on a single domain (Finance)

**Example:**
```python
class FinanceService:
    """Pure business logic, no HTTP dependencies."""
    
    @staticmethod
    def get_dashboard_summary(user, start_date=None, end_date=None):
        """Calculate totals - reusable from any view."""
        queryset = FinanceService.get_transactions_queryset(user)
        
        income = queryset.filter(type='income').aggregate(Sum('amount'))
        expenses = queryset.filter(type='expense').aggregate(Sum('amount'))
        
        return {
            'total_income': income['amount__sum'] or 0,
            'total_expenses': expenses['amount__sum'] or 0,
            'net_balance': income - expenses
        }
```

### Layer 3: Models (Data Access)

**File:** `models.py`

**Responsibility:**
- Define database schema
- Enforce constraints
- Manage relationships
- Handle data persistence

**Key Characteristics:**
- Clean field definitions with help_text
- Proper indexes for query performance
- Meaningful `__str__` methods
- Soft delete support

**Example:**
```python
class Transaction(models.Model):
    """Data model with proper structure."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['deleted_at']),
        ]
    
    def delete(self, *args, **kwargs):
        """Soft delete implementation."""
        self.deleted_at = timezone.now()
        self.save()
```

---

## Database Design

### Schema Design

The database uses **normalized relational design** with three main entities:

#### Role Table
```
Role
├── id (PK)
├── name (UNIQUE) - viewer, analyst, admin
├── description
└── created_at
```

**Why separate Role table:**
- Allows multiple roles in future
- Easier permission management
- Better referential integrity

#### User Table
```
User
├── id (PK)
├── username (UNIQUE, indexed)
├── email (UNIQUE, indexed)
├── password (hashed)
├── role_id (FK -> Role)
├── is_active
├── created_at
└── updated_at
```

**Why these fields:**
- Hashed passwords for security
- is_active for soft-disabling users
- Timestamps for audit trails
- Indexes on frequently queried fields

#### Transaction Table
```
Transaction
├── id (PK)
├── user_id (FK -> User, indexed)
├── amount (Decimal)
├── type (income/expense)
├── category
├── date (indexed)
├── description
├── created_at
├── updated_at
└── deleted_at (soft delete, indexed)
```

**Design Decisions:**

1. **Decimal for Money**: Uses `Decimal` instead of Float to avoid floating-point precision errors
   ```python
   amount = models.DecimalField(max_digits=12, decimal_places=2)
   # Safe: 1500.00, not 1500.0000000001
   ```

2. **Soft Deletes**: Keeps data for auditing/recovery
   ```python
   deleted_at = models.DateTimeField(null=True, blank=True)
   # Query excludes deleted: Transaction.objects.filter(deleted_at__isnull=True)
   ```

3. **Denormalization Opportunities** (for future optimization):
   - Cache frequently calculated totals
   - Add materialized views for trends
   - Archive old transactions

4. **Indexes Strategy**:
   ```python
   indexes = [
       models.Index(fields=['user', '-date']),  # Common queries
       models.Index(fields=['type']),           # Filtering by type
       models.Index(fields=['deleted_at']),     # Filtering deleted
   ]
   ```

### Why SQLite for Development

**Chosen:** SQLite

**Reasoning:**
- Zero configuration needed
- Perfect for development/demo
- Can easily migrate to PostgreSQL
- Good for small-to-medium apps

**For Production:**
```python
# settings.py
if os.getenv('ENVIRONMENT') == 'production':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            # ... credentials
        }
    }
```

---

## Authentication & Authorization

### Authentication Strategy

**Current (Development):**
- Simple token-based using username
- Header: `Authorization: Token username`
- Implemented in `auth.py`

```python
class TokenAuthentication(BaseTokenAuth):
    """Mock authentication for development."""
    
    def authenticate_credentials(self, key):
        user = User.objects.get(username=key)
        return (user, key)
```

**Why this approach:**
- Simple to test
- Demonstrates authentication flow
- Easy to replace with JWT

**For Production:**
```bash
pip install djangorestframework-simplejwt
```

```python
# Use JWT tokens instead
from rest_framework_simplejwt.views import TokenObtainPairView

path('api/token/', TokenObtainPairView.as_view()),
```

### Authorization Strategy

**Pattern: Role-Based Access Control (RBAC)**

Three roles with hierarchical permissions:

```
Viewer (read-only)
  ├── View own profile
  └── View dashboard & transactions (read-only)

Analyst (contributor)
  ├── All Viewer permissions
  ├── Create transactions
  ├── Edit own transactions
  └── Delete own transactions

Admin (manager)
  ├── All Analyst permissions
  ├── Create users
  ├── Edit any transaction
  ├── Delete any transaction
  └── Manage all users
```

**Implementation in `permissions.py`:**

```python
class IsAnalyst(permissions.BasePermission):
    """Check if user is analyst or higher."""
    
    def has_permission(self, request, view):
        if not request.user or not hasattr(request.user, 'role'):
            return False
        return request.user.role.name in ['analyst', 'admin']
```

**Object-level permissions:**

```python
class CanEditTransaction(permissions.BasePermission):
    """Admin can edit any, analyst only own."""
    
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role.name == 'admin':
            return True
        
        # Analyst only own transactions
        if request.user.role.name == 'analyst':
            return obj.user == request.user
        
        return False
```

**Why this design:**
- Clear permission rules
- Easy to add new roles
- Prevents privilege escalation
- Audit trail through user roles

---

## API Design

### RESTful Principles

**Base URL:** `/api/`

**Resource-based URLs:**
```
/api/users/              - Collection
/api/users/1/            - Resource
/api/transactions/       - Collection
/api/transactions/5/     - Resource
```

**HTTP Methods:**
```
GET    - Retrieve data (safe, idempotent)
POST   - Create new resource
PATCH  - Partial update
DELETE - Remove resource
```

### Request/Response Format

**Consistent Request Format:**
```json
{
  "amount": "1500.00",
  "type": "income",
  "category": "salary",
  "date": "2024-01-15",
  "description": "Monthly salary"
}
```

**Consistent Response Format:**
```json
{
  "id": 1,
  "amount": "1500.00",
  "type": "income",
  "category": "salary",
  "date": "2024-01-15",
  "description": "Monthly salary",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Response Format:**
```json
{
  "error": "Only analysts and admins can access this.",
  "status": "error",
  "code": "PERMISSION_DENIED"
}
```

### Filtering & Querying

**Query Parameters:**
```
GET /api/transactions/?type=income&category=salary&start_date=2024-01-01
```

**Why this approach:**
- Simple and standard
- Easy to extend
- Good caching support
- Clear semantics

**Alternative (GraphQL):**
- More flexible
- Better for complex queries
- Higher client complexity
- Not chosen for simplicity

---

## Error Handling

### Custom Exception Handler

**File:** `exceptions.py`

**Strategy:** Centralized error handling with consistent format

```python
def custom_exception_handler(exc, context):
    """Standardize all error responses."""
    
    response = exception_handler(exc, context)
    
    if response is not None:
        # Transform to consistent format
        response.data = {
            'error': str(exc.detail),
            'status': 'error',
            'code': 'ERROR_CODE'
        }
    
    return response
```

### Validation Errors

**Input Validation Layers:**

1. **Serializer Level** (field validation)
   ```python
   def validate_amount(self, value):
       if value <= 0:
           raise serializers.ValidationError("Amount must be positive")
       return value
   ```

2. **Model Level** (constraints)
   ```python
   amount = models.DecimalField(decimal_places=2)  # Forces precision
   ```

3. **View Level** (business logic)
   ```python
   if start_date and end_date and start_date > end_date:
       return Response({'error': 'Invalid date range'}, status=400)
   ```

**Why multi-layer:**
- Defense in depth
- Clear error messages
- Data consistency
- Early error detection

---

## Testing Strategy

### Test Organization

**File:** `tests.py`

**Test Classes:**
1. `UserManagementTest` - User CRUD and permissions
2. `TransactionManagementTest` - Transaction operations
3. `ValidationTest` - Input validation
4. `DashboardAnalyticsTest` - Analytics calculations

**Test Pyramid:**
```
         UI Tests (Selenium, E2E)
         ↑
      Integration Tests (API + DB)
         ↑
      Unit Tests (Isolated)
```

### Test Examples

**Unit Test (Isolated):**
```python
def test_amount_must_be_positive(self):
    """Validation catches invalid amounts."""
    
    data = {'amount': '-100.00', 'type': 'income'}
    response = self.client.post('/api/transactions/', data)
    
    self.assertEqual(response.status_code, 400)
```

**Integration Test (API + DB):**
```python
def test_analyst_can_create_transaction(self):
    """Full flow: auth -> create -> verify."""
    
    self.client.credentials(HTTP_AUTHORIZATION='Token analyst')
    response = self.client.post('/api/transactions/', {...})
    
    self.assertEqual(response.status_code, 201)
    self.assertTrue(Transaction.objects.filter(...).exists())
```

**Run Tests:**
```bash
python manage.py test                    # All tests
python manage.py test -v 2               # Verbose
coverage run --source='finance_app' manage.py test  # Coverage
```

---

## Security Considerations

### Input Validation

**Why it matters:** Prevents injection attacks, invalid states

```python
# Decimal validation (not string)
amount = models.DecimalField(max_digits=12, decimal_places=2)

# Email validation
email = models.EmailField()

# Choice validation
type = models.CharField(choices=TYPE_CHOICES)
```

### Password Security

**Hashing implementation:**
```python
def set_password(self, raw_password):
    """Hash password using Django's hashing."""
    self.password = make_password(raw_password)

def check_password(self, raw_password):
    """Verify password matches hash."""
    return check_password(raw_password, self.password)
```

**Why:** Never store plaintext passwords

### SQL Injection Prevention

**Using ORM instead of raw SQL:**
```python
# Safe: ORM parameterizes queries
Transaction.objects.filter(user=user, type='income')

# Not recommended: Raw SQL (if needed, use parameterization)
# Transaction.objects.raw('SELECT * FROM finance_app_transaction WHERE user_id = %s', [user_id])
```

### CORS Security

**For frontend integration:**
```python
INSTALLED_APPS = ['corsheaders', ...]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Only allow specific origins
]
```

### Rate Limiting

**Future enhancement:**
```bash
pip install djangorestframework-throttling
```

### HTTPS & SSL

**Production requirement:**
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## Scalability Considerations

### Current Limitations

1. **Single-server design**: No horizontal scaling
2. **SQLite**: Not suitable for concurrent writes
3. **No caching**: Every request queries database
4. **No async tasks**: Long operations block requests

### Scaling Path

**Stage 1: Database**
- Migrate SQLite → PostgreSQL
- Add connection pooling (pgbouncer)
- Implement read replicas

**Stage 2: Caching**
```bash
pip install django-redis
```
- Cache dashboard summaries
- Cache user permissions
- Cache analytics results

**Stage 3: Async**
```bash
pip install celery redis
```
- Background calculations
- Email notifications
- Heavy exports

**Stage 4: Distribution**
- Load balancer (nginx)
- Multiple app servers (gunicorn workers)
- CDN for static files
- Separate analytics database

---

## Performance Optimizations

### Database Query Optimization

**Select Related** (eager load relationships):
```python
User.objects.select_related('role')  # Single query instead of N+1
```

**Filter & Aggregate** (server-side):
```python
Transaction.objects.filter(user=user).aggregate(Sum('amount'))
# Calculates on database, not in Python
```

**Indexes** (speed up queries):
```python
indexes = [
    models.Index(fields=['user', '-date']),  # Common filter pattern
]
```

### API Response Optimization

**Pagination** (limit response size):
```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

**Field Selection** (only needed fields):
```python
# List view uses simplified serializer
if self.action == 'list':
    return TransactionListSerializer
```

---

## Future Enhancements

### Recommended Additions

1. **Pagination**
   - Add `PageNumberPagination` for large datasets
   - Implement cursor-based pagination for better performance

2. **Search**
   - Full-text search on transaction descriptions
   - Advanced filtering with elasticsearch

3. **Bulk Operations**
   - Create multiple transactions at once
   - Batch update functionality

4. **Export**
   - CSV export of transactions
   - PDF report generation
   - Monthly statements

5. **Budget Tracking**
   - Set spending limits by category
   - Alert when exceeding budget
   - Track against budget

6. **Multi-Currency**
   - Store original currency
   - Support currency conversion
   - Exchange rate management

7. **Audit Trail**
   - Track all changes to transactions
   - User action history
   - Compliance reporting

8. **Advanced Analytics**
   - Spending forecasts
   - Trend analysis
   - Anomaly detection

---

## Conclusion

This architecture provides:
- ✅ Clear separation of concerns
- ✅ Testability and maintainability
- ✅ Security best practices
- ✅ Performance considerations
- ✅ Extensibility for future features
- ✅ Production-ready foundation

The design prioritizes **code clarity** over clever optimizations, making it easy to understand, modify, and scale.

---
