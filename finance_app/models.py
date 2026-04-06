"""
Data models for the finance application.

Models:
- Role: Represents user roles (Viewer, Analyst, Admin)
- User: Represents system users with role assignments
- Transaction: Represents financial entries (income/expense)
"""

from django.db import models
from django.contrib.auth.hashers import make_password
from django.utils import timezone


class Role(models.Model):
    """
    Represents a user role in the system.
    
    Roles define permission levels:
    - VIEWER: Can only view dashboard data
    - ANALYST: Can view and create records, access insights
    - ADMIN: Full management access to records and users
    """
    
    ROLE_CHOICES = [
        ('viewer', 'Viewer'),
        ('analyst', 'Analyst'),
        ('admin', 'Admin'),
    ]
    
    name = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        unique=True,
        help_text="Role identifier: viewer, analyst, or admin"
    )
    description = models.TextField(
        help_text="Description of role and its permissions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']
    
    def __str__(self):
        return self.get_name_display()


class User(models.Model):
    """
    Represents a system user.
    
    Users have:
    - Basic credentials (username, email, password)
    - Role assignment
    - Active/Inactive status
    - Audit timestamps
    """
    
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Unique username for login"
    )
    email = models.EmailField(
        unique=True,
        help_text="User's email address"
    )
    password = models.CharField(
        max_length=255,
        help_text="Hashed password"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        help_text="User's role (determines permissions)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this user account is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.role.get_name_display()})"
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
    
    def set_password(self, raw_password):
        """Hash and set password."""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if provided password matches stored hash."""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)


class Transaction(models.Model):
    """
    Represents a financial transaction (income or expense).
    
    Each transaction:
    - Belongs to a user
    - Has amount, type (income/expense), and category
    - Includes date and optional description
    - Supports soft delete via deleted_at
    """
    
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('bonus', 'Bonus'),
        ('investment', 'Investment'),
        ('food', 'Food & Dining'),
        ('transportation', 'Transportation'),
        ('utilities', 'Utilities'),
        ('entertainment', 'Entertainment'),
        ('health', 'Health & Fitness'),
        ('education', 'Education'),
        ('shopping', 'Shopping'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text="User who owns this transaction"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Transaction amount (must be positive)"
    )
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        help_text="Type of transaction: income or expense"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        help_text="Category of transaction"
    )
    date = models.DateField(
        help_text="Date of transaction"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description or notes"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Soft delete timestamp (null if not deleted)"
    )
    
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['type']),
            models.Index(fields=['category']),
            models.Index(fields=['deleted_at']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.amount} ({self.category})"
    
    def delete(self, *args, **kwargs):
        """Soft delete: mark as deleted without removing from database."""
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore a soft-deleted transaction."""
        self.deleted_at = None
        self.save()
    
    @property
    def is_deleted(self):
        """Check if transaction is soft-deleted."""
        return self.deleted_at is not None