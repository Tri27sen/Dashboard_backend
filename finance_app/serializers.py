"""
Django REST Framework serializers for API requests and responses.

Serializers handle:
- Data validation
- Transformation between models and JSON
- Nested relationships
- Custom field validation
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from finance_app.models import User, Role, Transaction


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    
    Handles user creation, updates, and API responses.
    Password is write-only and hashed on save.
    """
    
    role = RoleSerializer(read_only=True)
    role_name = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Role name: 'viewer', 'analyst', or 'admin'"
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        help_text="User password (at least 6 characters)"
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'role',
            'role_name', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_username(self, value):
        """Validate username is not already taken."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        return value
    
    def validate_email(self, value):
        """Validate email is not already taken."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value
    
    def validate_role_name(self, value):
        """Validate role exists."""
        try:
            Role.objects.get(name=value)
        except Role.DoesNotExist:
            raise serializers.ValidationError(f"Role '{value}' does not exist.")
        return value
    
    def create(self, validated_data):
        """Create user with hashed password and assigned role."""
        role_name = validated_data.pop('role_name')
        password = validated_data.pop('password')
        
        role = Role.objects.get(name=role_name)
        user = User.objects.create(**validated_data, role=role)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user. Password handled specially if provided."""
        password = validated_data.pop('password', None)
        validated_data.pop('role_name', None)  # Role not updatable via API
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model.
    
    Handles transaction creation, updates, and API responses.
    Includes validation for amounts and date ranges.
    """
    
    user_username = serializers.CharField(
        source='user.username',
        read_only=True,
        help_text="Username of transaction owner"
    )
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'user_username', 'amount', 'type',
            'category', 'date', 'description', 'created_at',
            'updated_at', 'is_deleted'
        ]
        read_only_fields = ['id', 'user', 'user_username', 'created_at', 'updated_at', 'is_deleted']
    
    def validate_amount(self, value):
        """Amount must be positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value
    
    def validate_type(self, value):
        """Type must be valid choice."""
        if value not in dict(Transaction.TYPE_CHOICES):
            raise serializers.ValidationError(f"Invalid type. Must be one of: {', '.join(dict(Transaction.TYPE_CHOICES).keys())}")
        return value
    
    def validate_category(self, value):
        """Category must be valid choice."""
        if value not in dict(Transaction.CATEGORY_CHOICES):
            raise serializers.ValidationError(f"Invalid category. Must be one of: {', '.join(dict(Transaction.CATEGORY_CHOICES).keys())}")
        return value
    
    def validate(self, data):
        """Additional cross-field validation."""
        from datetime import date
        
        # Check date is not in future
        if data.get('date', date.today()) > date.today():
            raise serializers.ValidationError({
                'date': 'Transaction date cannot be in the future.'
            })
        
        return data
    
    def to_representation(self, instance):
        """Override to exclude deleted transactions in responses."""
        representation = super().to_representation(instance)
        if instance.is_deleted:
            representation['is_deleted'] = True
        return representation


class TransactionListSerializer(TransactionSerializer):
    """
    Simplified serializer for transaction list views.
    Excludes description for cleaner list responses.
    """
    
    class Meta(TransactionSerializer.Meta):
        fields = [
            'id', 'user_username', 'amount', 'type', 'category',
            'date', 'created_at', 'is_deleted'
        ]


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for dashboard summary data."""
    
    total_income = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    total_expenses = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    net_balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    period = serializers.CharField(read_only=True)
    transaction_count = serializers.IntegerField(read_only=True)


class CategoryBreakdownSerializer(serializers.Serializer):
    """Serializer for category-wise breakdown."""
    
    name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    type = serializers.CharField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class MonthlyTrendSerializer(serializers.Serializer):
    """Serializer for monthly trend data."""
    
    month = serializers.CharField()
    income = serializers.DecimalField(max_digits=12, decimal_places=2)
    expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net = serializers.DecimalField(max_digits=12, decimal_places=2)


class RecentActivitySerializer(serializers.Serializer):
    """Serializer for recent activity feed."""
    
    id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    type = serializers.CharField()
    category = serializers.CharField()
    date = serializers.DateField()
    description = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()