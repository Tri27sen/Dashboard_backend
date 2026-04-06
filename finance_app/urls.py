"""
URL configuration for finance_project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from finance_app.views import (
    UserViewSet,
    TransactionViewSet,
    DashboardSummaryView,
    CategoryBreakdownView,
    MonthlyTrendsView,
    RecentActivityView,
)

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('api/', include(router.urls)),
    
    # Dashboard endpoints
    path('api/dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('api/dashboard/category-breakdown/', CategoryBreakdownView.as_view(), name='category-breakdown'),
    path('api/dashboard/monthly-trends/', MonthlyTrendsView.as_view(), name='monthly-trends'),
    path('api/dashboard/recent-activity/', RecentActivityView.as_view(), name='recent-activity'),
    
    # Default API auth
    path('api-auth/', include('rest_framework.urls')),
]