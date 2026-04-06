"""
Seed script to populate initial data.

Run with: python manage.py shell < seed_data.py
"""

from finance_app.models import Role, User, Transaction
from datetime import date, timedelta
from decimal import Decimal

print("Creating roles...")
viewer_role, _ = Role.objects.get_or_create(
    name='viewer',
    defaults={'description': 'Can only view dashboard data and transactions'}
)

analyst_role, _ = Role.objects.get_or_create(
    name='analyst',
    defaults={'description': 'Can view and create transactions, access analytics'}
)

admin_role, _ = Role.objects.get_or_create(
    name='admin',
    defaults={'description': 'Full management access to all features and users'}
)


# Admin user
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@example.com',
        'role': admin_role,
        'is_active': True
    }
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()
    
else:
    print("  Admin user already exists")

# Analyst user
analyst_user, created = User.objects.get_or_create(
    username='analyst',
    defaults={
        'email': 'analyst@example.com',
        'role': analyst_role,
        'is_active': True
    }
)
if created:
    analyst_user.set_password('analyst123')
    analyst_user.save()
    
else:
    print("  Analyst user already exists")

# Viewer user
viewer_user, created = User.objects.get_or_create(
    username='viewer',
    defaults={
        'email': 'viewer@example.com',
        'role': viewer_role,
        'is_active': True
    }
)
if created:
    viewer_user.set_password('viewer123')
    viewer_user.save()
    
else:
    print("  Viewer user already exists")

# Create sample transactions
print("\nCreating sample transactions...")

today = date.today()
sample_transactions = [
    # Income transactions
    {
        'user': analyst_user,
        'amount': Decimal('5000.00'),
        'type': 'income',
        'category': 'salary',
        'date': today,
        'description': 'Monthly salary'
    },
    {
        'user': analyst_user,
        'amount': Decimal('500.00'),
        'type': 'income',
        'category': 'bonus',
        'date': today - timedelta(days=5),
        'description': 'Performance bonus'
    },
    {
        'user': analyst_user,
        'amount': Decimal('200.00'),
        'type': 'income',
        'category': 'investment',
        'date': today - timedelta(days=10),
        'description': 'Dividend payment'
    },
    
    # Expense transactions
    {
        'user': analyst_user,
        'amount': Decimal('45.50'),
        'type': 'expense',
        'category': 'food',
        'date': today,
        'description': 'Lunch at restaurant'
    },
    {
        'user': analyst_user,
        'amount': Decimal('120.00'),
        'type': 'expense',
        'category': 'transportation',
        'date': today - timedelta(days=1),
        'description': 'Uber rides'
    },
    {
        'user': analyst_user,
        'amount': Decimal('250.00'),
        'type': 'expense',
        'category': 'utilities',
        'date': today - timedelta(days=3),
        'description': 'Monthly electricity bill'
    },
    {
        'user': analyst_user,
        'amount': Decimal('80.00'),
        'type': 'expense',
        'category': 'entertainment',
        'date': today - timedelta(days=7),
        'description': 'Movie tickets and popcorn'
    },
    {
        'user': analyst_user,
        'amount': Decimal('150.00'),
        'type': 'expense',
        'category': 'health',
        'date': today - timedelta(days=14),
        'description': 'Gym membership'
    },
    {
        'user': analyst_user,
        'amount': Decimal('300.00'),
        'type': 'expense',
        'category': 'shopping',
        'date': today - timedelta(days=7),
        'description': 'Clothing purchase'
    },
    {
        'user': analyst_user,
        'amount': Decimal('99.99'),
        'type': 'expense',
        'category': 'education',
        'date': today - timedelta(days=21),
        'description': 'Online course'
    },
]

created_count = 0
for trans_data in sample_transactions:
    trans, created = Transaction.objects.get_or_create(
        user=trans_data['user'],
        amount=trans_data['amount'],
        type=trans_data['type'],
        category=trans_data['category'],
        date=trans_data['date'],
        defaults={'description': trans_data['description']}
    )
    if created:
        created_count += 1

