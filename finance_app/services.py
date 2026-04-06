"""
Business logic services for financial analytics and data processing.

Services separate business logic from views, making code:
- More testable
- More reusable
- Easier to understand
"""

from decimal import Decimal
from datetime import datetime, timedelta, date
from django.db.models import Sum, Q, F
from django.utils import timezone
from finance_app.models import Transaction


class FinanceService:
    """Service for financial calculations and analytics."""
    
    @staticmethod
    def get_transactions_queryset(user, include_deleted=False):
        """
        Get transactions queryset for a user, excluding soft-deleted by default.
        
        Args:
            user: User instance
            include_deleted: Whether to include soft-deleted transactions
        
        Returns:
            Filtered queryset
        """
        queryset = Transaction.objects.filter(user=user)
        if not include_deleted:
            queryset = queryset.filter(deleted_at__isnull=True)
        return queryset
    
    @staticmethod
    def get_dashboard_summary(user, start_date=None, end_date=None):
        """
        Calculate dashboard summary for a user.
        
        Returns:
        - total_income: Sum of all income transactions
        - total_expenses: Sum of all expense transactions
        - net_balance: Income - Expenses
        - period: Time period description
        - transaction_count: Number of transactions
        """
        queryset = FinanceService.get_transactions_queryset(user)
        
        # Filter by date range if provided
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Calculate totals
        income_agg = queryset.filter(type='income').aggregate(Sum('amount'))
        expense_agg = queryset.filter(type='expense').aggregate(Sum('amount'))
        
        total_income = income_agg['amount__sum'] or Decimal('0.00')
        total_expenses = expense_agg['amount__sum'] or Decimal('0.00')
        net_balance = total_income - total_expenses
        
        # Format period description
        if start_date and end_date:
            period = f"{start_date} to {end_date}"
        elif start_date:
            period = f"From {start_date} onwards"
        elif end_date:
            period = f"Until {end_date}"
        else:
            period = "All time"
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_balance': net_balance,
            'period': period,
            'transaction_count': queryset.count()
        }
    
    @staticmethod
    def get_category_breakdown(user, period='all_time'):
        """
        Get breakdown of transactions by category.
        
        Args:
            user: User instance
            period: 'all_time', 'monthly', 'yearly'
        
        Returns:
            List of dicts with category, amount, type, percentage
        """
        queryset = FinanceService.get_transactions_queryset(user)
        
        # Filter by period
        if period == 'monthly':
            start_date = date.today() - timedelta(days=30)
            queryset = queryset.filter(date__gte=start_date)
        elif period == 'yearly':
            start_date = date.today() - timedelta(days=365)
            queryset = queryset.filter(date__gte=start_date)
        
        # Group by category and type
        categories = {}
        total_amount = Decimal('0.00')
        
        for transaction in queryset:
            key = (transaction.category, transaction.type)
            if key not in categories:
                categories[key] = Decimal('0.00')
            categories[key] += transaction.amount
            total_amount += transaction.amount
        
        # Format results
        result = []
        for (category, trans_type), amount in sorted(categories.items()):
            percentage = (amount / total_amount * 100) if total_amount > 0 else 0
            result.append({
                'name': category,
                'amount': amount,
                'type': trans_type,
                'percentage': Decimal(str(percentage)).quantize(Decimal('0.01'))
            })
        
        return sorted(result, key=lambda x: x['amount'], reverse=True)
    
    @staticmethod
    def get_monthly_trends(user, months=12):
        """
        Get income and expense trends by month.
        
        Args:
            user: User instance
            months: Number of months to include (default 12)
        
        Returns:
            List of dicts with month, income, expenses, net
        """
        queryset = FinanceService.get_transactions_queryset(user)
        
        # Calculate date range
        today = date.today()
        start_date = today - timedelta(days=30 * months)
        
        queryset = queryset.filter(date__gte=start_date)
        
        # Build monthly buckets
        trends = {}
        current_date = datetime(start_date.year, start_date.month, 1)
        end_date = datetime.now()
        
        while current_date <= end_date:
            month_key = current_date.strftime('%Y-%m')
            if month_key not in trends:
                trends[month_key] = {
                    'month': month_key,
                    'income': Decimal('0.00'),
                    'expenses': Decimal('0.00')
                }
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Populate with actual data
        for transaction in queryset:
            month_key = transaction.date.strftime('%Y-%m')
            if month_key in trends:
                if transaction.type == 'income':
                    trends[month_key]['income'] += transaction.amount
                else:
                    trends[month_key]['expenses'] += transaction.amount
        
        # Calculate net and format
        result = []
        for month_key in sorted(trends.keys()):
            trend = trends[month_key]
            trend['net'] = trend['income'] - trend['expenses']
            result.append(trend)
        
        return result
    
    @staticmethod
    def get_recent_activity(user, limit=10):
        """
        Get recent transactions for a user.
        
        Args:
            user: User instance
            limit: Number of recent transactions to return
        
        Returns:
            List of recent transactions as dicts
        """
        transactions = FinanceService.get_transactions_queryset(user).order_by('-date', '-created_at')[:limit]
        
        return [
            {
                'id': t.id,
                'amount': t.amount,
                'type': t.type,
                'category': t.category,
                'date': t.date,
                'description': t.description,
                'created_at': t.created_at
            }
            for t in transactions
        ]
    
    @staticmethod
    def get_expense_analysis(user, period='monthly'):
        """
        Get detailed expense analysis.
        
        Returns categories with highest expenses.
        """
        queryset = FinanceService.get_transactions_queryset(user).filter(type='expense')
        
        # Filter by period
        if period == 'monthly':
            start_date = date.today() - timedelta(days=30)
            queryset = queryset.filter(date__gte=start_date)
        elif period == 'yearly':
            start_date = date.today() - timedelta(days=365)
            queryset = queryset.filter(date__gte=start_date)
        
        # Group by category
        categories = {}
        for transaction in queryset:
            if transaction.category not in categories:
                categories[transaction.category] = {
                    'category': transaction.category,
                    'total': Decimal('0.00'),
                    'count': 0
                }
            categories[transaction.category]['total'] += transaction.amount
            categories[transaction.category]['count'] += 1
        
        # Sort by total amount
        result = sorted(categories.values(), key=lambda x: x['total'], reverse=True)
        return result