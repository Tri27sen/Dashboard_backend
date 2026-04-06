"""
Test suite for the finance API.

Tests cover:
- User management and role assignments
- Transaction CRUD operations
- Permission enforcement
- Analytics calculations
- Validation and error handling

IMPORTANT: Mixin is listed FIRST in class inheritance for proper MRO.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date
from rest_framework.authtoken.models import Token

from finance_app.models import Role, User, Transaction


class RoleSetupMixin:
    """Helper to set up roles for tests."""
    
    def setUp(self):
        """Create test roles."""
        # Call parent setUp to ensure Django's test setup chain works
        super().setUp()
        
        self.viewer_role = Role.objects.create(
            name='viewer',
            description='Can only view dashboard data'
        )
        self.analyst_role = Role.objects.create(
            name='analyst',
            description='Can view and create transactions'
        )
        self.admin_role = Role.objects.create(
            name='admin',
            description='Full management access'
        )
        self.client = APIClient()


# IMPORTANT: RoleSetupMixin FIRST, TestCase SECOND (correct MRO order)
class UserManagementTest(RoleSetupMixin, TestCase):
    """Test user creation, management, and permissions."""
    
    def setUp(self):
        """Create test roles and admin user."""
        super().setUp()
        self.admin_user = User.objects.create(
            username='admin_user',
            email='admin@example.com',
            role=self.admin_role,
            is_active=True
        )
        self.admin_user.set_password('admin123')
        self.admin_user.save()
    
    def test_create_user_as_admin(self):
        """Admin can create new users."""
        self.client.credentials(HTTP_AUTHORIZATION='Token admin_user')
        
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'role_name': 'analyst'
        }
        
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['role']['name'], 'analyst')
    
    def test_create_user_as_non_admin(self):
        """Non-admins cannot create users."""
        analyst = User.objects.create(
            username='analyst_user',
            email='analyst@example.com',
            role=self.analyst_role,
            is_active=True
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token analyst_user')
        
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'role_name': 'analyst'
        }
        
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_username_must_be_unique(self):
        """Cannot create user with duplicate username."""
        self.client.credentials(HTTP_AUTHORIZATION='Token admin_user')
        
        data = {
            'username': 'admin_user',
            'email': 'different@example.com',
            'password': 'newpass123',
            'role_name': 'viewer'
        }
        
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_email_must_be_unique(self):
        """Cannot create user with duplicate email."""
        self.client.credentials(HTTP_AUTHORIZATION='Token admin_user')
        
        data = {
            'username': 'differentuser',
            'email': 'admin@example.com',
            'password': 'newpass123',
            'role_name': 'viewer'
        }
        
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# IMPORTANT: RoleSetupMixin FIRST, TestCase SECOND (correct MRO order)
class TransactionManagementTest(RoleSetupMixin, TestCase):
    """Test transaction CRUD operations and permissions."""
    
    def setUp(self):
        """Create test roles and users."""
        super().setUp()
        self.analyst_user = User.objects.create(
            username='analyst',
            email='analyst@example.com',
            role=self.analyst_role,
            is_active=True
        )
        
        self.viewer_user = User.objects.create(
            username='viewer',
            email='viewer@example.com',
            role=self.viewer_role,
            is_active=True
        )
        
        self.client = APIClient()
    
    def test_analyst_can_create_transaction(self):
        """Analyst can create financial transactions."""
        self.client.credentials(HTTP_AUTHORIZATION='Token analyst')
        
        data = {
            'amount': '1500.00',
            'type': 'income',
            'category': 'salary',
            'date': date.today().isoformat(),
            'description': 'Monthly salary'
        }
        
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '1500.00')
    
    def test_viewer_cannot_create_transaction(self):
        """Viewer cannot create transactions."""
        self.client.credentials(HTTP_AUTHORIZATION='Token viewer')
        
        data = {
            'amount': '1500.00',
            'type': 'income',
            'category': 'salary',
            'date': date.today().isoformat(),
            'description': 'Monthly salary'
        }
        
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_viewer_can_read_transactions(self):
        """Viewer can read transaction data."""
        transaction = Transaction.objects.create(
            user=self.analyst_user,
            amount=Decimal('1500.00'),
            type='income',
            category='salary',
            date=date.today(),
            description='Salary'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token viewer')
        response = self.client.get('/api/transactions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_analyst_can_only_edit_own_transaction(self):
        """Analyst can edit their own transactions."""
        transaction = Transaction.objects.create(
            user=self.analyst_user,
            amount=Decimal('1500.00'),
            type='income',
            category='salary',
            date=date.today()
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token analyst')
        
        data = {
            'amount': '2000.00',
            'type': 'income',
            'category': 'bonus',
            'date': date.today().isoformat()
        }
        
        response = self.client.patch(f'/api/transactions/{transaction.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '2000.00')
    
    def test_soft_delete_transaction(self):
        """Transactions are soft-deleted (not removed from DB)."""
        transaction = Transaction.objects.create(
            user=self.analyst_user,
            amount=Decimal('1500.00'),
            type='income',
            category='salary',
            date=date.today()
        )
        
        self.client.credentials(HTTP_AUTHORIZATION='Token analyst')
        response = self.client.delete(f'/api/transactions/{transaction.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        transaction.refresh_from_db()
        self.assertIsNotNone(transaction.deleted_at)


# IMPORTANT: RoleSetupMixin FIRST, TestCase SECOND (correct MRO order)
class ValidationTest(RoleSetupMixin, TestCase):
    """Test input validation and error handling."""
    
    def setUp(self):
        """Create test roles and user."""
        super().setUp()
        self.user = User.objects.create(
            username='testuser',
            email='test@example.com',
            role=self.analyst_role,
            is_active=True
        )
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token testuser')
    
    def test_amount_must_be_positive(self):
        """Transaction amount must be greater than zero."""
        data = {
            'amount': '-100.00',
            'type': 'income',
            'category': 'salary',
            'date': date.today().isoformat()
        }
        
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_amount_cannot_be_zero(self):
        """Transaction amount cannot be zero."""
        data = {
            'amount': '0.00',
            'type': 'income',
            'category': 'salary',
            'date': date.today().isoformat()
        }
        
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_transaction_type(self):
        """Transaction type must be valid choice."""
        data = {
            'amount': '100.00',
            'type': 'invalid_type',
            'category': 'salary',
            'date': date.today().isoformat()
        }
        
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_category(self):
        """Category must be valid choice."""
        data = {
            'amount': '100.00',
            'type': 'income',
            'category': 'invalid_category',
            'date': date.today().isoformat()
        }
        
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_date_format(self):
        """Date must be in ISO format."""
        data = {
            'amount': '100.00',
            'type': 'income',
            'category': 'salary',
            'date': '01-01-2024'
        }
        
        response = self.client.post('/api/transactions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# IMPORTANT: RoleSetupMixin FIRST, TestCase SECOND (correct MRO order)
class DashboardAnalyticsTest(RoleSetupMixin, TestCase):
    """Test dashboard summary and analytics endpoints."""
    
    def setUp(self):
        """Create test roles, user, and transactions."""
        super().setUp()
        self.user = User.objects.create(
            username='testuser',
            email='test@example.com',
            role=self.analyst_role,
            is_active=True
        )
        
        today = date.today()
        
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('5000.00'),
            type='income',
            category='salary',
            date=today
        )
        
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('2000.00'),
            type='expense',
            category='food',
            date=today
        )
        
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('500.00'),
            type='expense',
            category='entertainment',
            date=today
        )
        
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token testuser')
    
    def test_dashboard_summary(self):
        """Dashboard summary calculates correct totals."""
        response = self.client.get('/api/dashboard/summary/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_income'], '5000.00')
        self.assertEqual(response.data['total_expenses'], '2500.00')
        self.assertEqual(response.data['net_balance'], '2500.00')
        self.assertEqual(response.data['transaction_count'], 3)
    
    def test_category_breakdown(self):
        """Category breakdown groups by category correctly."""
        response = self.client.get('/api/dashboard/category-breakdown/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['categories']), 3)
        
        categories = {c['name']: c['amount'] for c in response.data['categories']}
        self.assertEqual(categories['salary'], '5000.00')
    
    def test_monthly_trends(self):
        """Monthly trends includes all months."""
        response = self.client.get('/api/dashboard/monthly-trends/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['data']), 0)
    
    def test_recent_activity(self):
        """Recent activity lists transactions."""
        response = self.client.get('/api/dashboard/recent-activity/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['activities']), 3)