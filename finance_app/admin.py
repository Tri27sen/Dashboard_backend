"""
Django admin configuration for finance_app.
"""

from django.contrib import admin
from finance_app.models import Role, User, Transaction


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role model."""
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin interface for User model."""
    list_display = ('username', 'email', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'created_at')
    search_fields = ('username', 'email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Account Information', {
            'fields': ('username', 'email', 'password', 'is_active')
        }),
        ('Role & Permissions', {
            'fields': ('role',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction model."""
    list_display = ('user', 'type', 'category', 'amount', 'date', 'deleted_at')
    list_filter = ('type', 'category', 'date', 'deleted_at')
    search_fields = ('user__username', 'description', 'category')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'type', 'category', 'amount')
        }),
        ('Date & Description', {
            'fields': ('date', 'description')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )