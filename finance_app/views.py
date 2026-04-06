"""
Django REST Framework views for API endpoints.

Views handle:
- HTTP request/response
- Permission checks
- Serialization/deserialization
- Query filtering
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from datetime import datetime, date

from finance_app.models import User, Transaction, Role
from finance_app.serializers import (
    UserSerializer, TransactionSerializer, TransactionListSerializer,
    DashboardSummarySerializer, CategoryBreakdownSerializer,
    MonthlyTrendSerializer, RecentActivitySerializer
)
from finance_app.permissions import (
    IsAdmin, IsAnalyst, IsViewer, CanCreateTransaction,
    CanEditTransaction, CanManageUsers, CanAccessDashboard
)
from finance_app.services import FinanceService


class UserViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for user management.
    
    Only admins can:
    - List all users
    - Create new users
    - Update users
    - Delete users
    
    Users can view their own profile.
    """
    
    queryset = User.objects.select_related('role')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, CanManageUsers]
    
    def get_queryset(self):
        """Filter users based on permissions."""
        user = self.request.user
        
        # Admins see all users
        if user.role.name == 'admin':
            return User.objects.select_related('role').all()
        
        # Others only see themselves
        return User.objects.filter(id=user.id)
    
    def create(self, request, *args, **kwargs):
        """Create new user (admin only)."""
        # Permission check done by permission class
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete user (admin only).
        
        Note: Soft deletes user by marking is_active=False
        """
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for financial transactions.
    
    Permissions:
    - Viewers: can list and retrieve (read-only)
    - Analysts: can list, retrieve, create, update, delete own transactions
    - Admins: full access to all transactions
    """
    
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, CanCreateTransaction, CanEditTransaction]
    
    def get_queryset(self):
        """Filter transactions based on user role."""
        user = self.request.user
        
        # Admins see all transactions
        if user.role.name == 'admin':
            return Transaction.objects.filter(deleted_at__isnull=True).select_related('user')
        
        # Analysts and viewers only see their own
        return Transaction.objects.filter(
            user=user,
            deleted_at__isnull=True
        ).select_related('user')
    
    def get_serializer_class(self):
        """Use simplified serializer for list views."""
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionSerializer
    
    def perform_create(self, serializer):
        """Create transaction with current user."""
        serializer.save(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        """
        List transactions with optional filtering.
        
        Query parameters:
        - type: 'income' or 'expense'
        - category: transaction category
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
        """
        queryset = self.get_queryset()
        
        # Filter by type
        trans_type = request.query_params.get('type')
        if trans_type:
            queryset = queryset.filter(type=trans_type)
        
        # Filter by category
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by date range
        start_date = request.query_params.get('start_date')
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid start_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        end_date = request.query_params.get('end_date')
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid end_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Order by date descending
        queryset = queryset.order_by('-date', '-created_at')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete transaction."""
        transaction = self.get_object()
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def restore(self, request, pk=None):
        """Restore a soft-deleted transaction (admin only)."""
        if request.user.role.name != 'admin':
            return Response(
                {'error': 'Only admins can restore transactions'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        transaction = get_object_or_404(Transaction, pk=pk)
        transaction.restore()
        
        serializer = self.get_serializer(transaction)
        return Response(serializer.data)


class DashboardSummaryView(APIView):
    """
    API endpoint for dashboard summary data.
    
    GET /api/dashboard/summary/
    
    Optional query parameters:
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    
    Returns:
    - total_income
    - total_expenses
    - net_balance
    - transaction_count
    - period
    """
    
    permission_classes = [IsAuthenticated, CanAccessDashboard]
    
    def get(self, request):
        """Get dashboard summary."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates if provided
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid start_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid end_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get summary from service
        summary = FinanceService.get_dashboard_summary(
            request.user,
            start_date=start_date,
            end_date=end_date
        )
        
        serializer = DashboardSummarySerializer(summary)
        return Response(serializer.data)


class CategoryBreakdownView(APIView):
    """
    API endpoint for category-wise breakdown.
    
    GET /api/dashboard/category-breakdown/
    
    Optional query parameters:
    - period: 'all_time' (default), 'monthly', 'yearly'
    
    Returns:
    - List of categories with amounts and percentages
    """
    
    permission_classes = [IsAuthenticated, CanAccessDashboard]
    
    def get(self, request):
        """Get category breakdown."""
        period = request.query_params.get('period', 'all_time')
        
        if period not in ['all_time', 'monthly', 'yearly']:
            return Response(
                {'error': "Period must be 'all_time', 'monthly', or 'yearly'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        breakdown = FinanceService.get_category_breakdown(request.user, period=period)
        serializer = CategoryBreakdownSerializer(breakdown, many=True)
        return Response({'categories': serializer.data})


class MonthlyTrendsView(APIView):
    """
    API endpoint for monthly trends.
    
    GET /api/dashboard/monthly-trends/
    
    Optional query parameters:
    - months: number of months to return (default 12)
    
    Returns:
    - List of monthly income, expenses, and net amounts
    """
    
    permission_classes = [IsAuthenticated, CanAccessDashboard]
    
    def get(self, request):
        """Get monthly trends."""
        try:
            months = int(request.query_params.get('months', 12))
            if months < 1 or months > 60:
                months = 12
        except ValueError:
            months = 12
        
        trends = FinanceService.get_monthly_trends(request.user, months=months)
        serializer = MonthlyTrendSerializer(trends, many=True)
        return Response({'data': serializer.data})


class RecentActivityView(APIView):
    """
    API endpoint for recent activity.
    
    GET /api/dashboard/recent-activity/
    
    Optional query parameters:
    - limit: number of recent transactions (default 10)
    
    Returns:
    - List of recent transactions
    """
    
    permission_classes = [IsAuthenticated, CanAccessDashboard]
    
    def get(self, request):
        """Get recent activity."""
        try:
            limit = int(request.query_params.get('limit', 10))
            if limit < 1 or limit > 100:
                limit = 10
        except ValueError:
            limit = 10
        
        activities = FinanceService.get_recent_activity(request.user, limit=limit)
        serializer = RecentActivitySerializer(activities, many=True)
        return Response({'activities': serializer.data})