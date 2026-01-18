# Phase 5: Django/Web Integration

**Priority:** MEDIUM
**Duration:** 5-10 days
**Impact:** HIGH - Production readiness

## Overview

Make estrattoconto production-ready for Django web applications, specifically for the family house bill management use case.

---

## Task 5.1: Create Django Package Structure

### Overview

**Duration:** 2-3 days
**Impact:** HIGH

Create a separate Django package for integration.

### File Structure

```
estrattoconto-django/
├── setup.py
├── README.md
├── estrattoconto_django/
│   ├── __init__.py
│   ├── models.py           # Django models
│   ├── views.py            # Upload views
│   ├── tasks.py            # Celery tasks
│   ├── serializers.py      # DRF serializers
│   ├── urls.py             # URL patterns
│   ├── admin.py            # Admin interface
│   ├── signals.py          # Django signals
│   ├── forms.py            # Upload forms
│   └── templates/
│       └── estrattoconto/
│           ├── upload.html
│           ├── list.html
│           └── detail.html
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_tasks.py
└── migrations/
    └── 0001_initial.py
```

### Implementation

#### models.py

```python
"""Django models for estrattoconto."""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()


class BankStatement(models.Model):
    """Bank statement upload."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # File info
    uploaded_file = models.FileField(
        upload_to='bank_statements/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    original_filename = models.CharField(max_length=255)

    # Metadata
    bank_type = models.CharField(max_length=100, blank=True)
    period = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=100, blank=True)

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    processing_error = models.TextField(blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    # Relationships
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bank_statements'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['bank_type']),
            models.Index(fields=['uploaded_by', '-created_at']),
        ]

    def __str__(self):
        return f"{self.original_filename} - {self.status}"

    @property
    def transaction_count(self):
        """Count of related transactions."""
        return self.transactions.count()

    @property
    def processing_duration(self):
        """Duration of processing in seconds."""
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return delta.total_seconds()
        return None


class Transaction(models.Model):
    """Individual transaction from bank statement."""

    statement = models.ForeignKey(
        BankStatement,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    # Transaction data
    date = models.DateField()
    value_date = models.DateField()
    description = models.TextField()

    # Amounts
    debit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    credit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Combined amount (credit - debit)"
    )

    # Extracted entities
    payer = models.CharField(max_length=255, blank=True)
    payee = models.CharField(max_length=255, blank=True)
    id_mandato = models.CharField(max_length=100, blank=True)

    # Classification flags
    is_bill = models.BooleanField(default=False)
    is_incoming_transfer = models.BooleanField(default=False)
    is_outgoing_transfer = models.BooleanField(default=False)
    is_bank_fee = models.BooleanField(default=False)

    # ML categorization
    category = models.CharField(max_length=100, blank=True)
    category_confidence = models.FloatField(null=True, blank=True)

    # Metadata
    related_account = models.CharField(max_length=100, blank=True)
    period = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['statement', '-date']),
            models.Index(fields=['date']),
            models.Index(fields=['is_bill']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.date} - {self.description[:50]} - {self.amount}"


class ProcessingLog(models.Model):
    """Log of processing steps."""

    statement = models.ForeignKey(
        BankStatement,
        on_delete=models.CASCADE,
        related_name='logs'
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(
        max_length=20,
        choices=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('error', 'Error'),
        ]
    )
    message = models.TextField()
    details = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.level}: {self.message}"
```

#### tasks.py (Celery)

```python
"""Celery tasks for background processing."""

from celery import shared_task
from django.utils import timezone
from .models import BankStatement, Transaction, ProcessingLog
import estrattoconto


@shared_task(bind=True)
def process_bank_statement(self, statement_id: int):
    """
    Process bank statement in background.

    Args:
        statement_id: BankStatement ID
    """
    try:
        statement = BankStatement.objects.get(id=statement_id)
    except BankStatement.DoesNotExist:
        return {'error': 'Statement not found'}

    # Update status
    statement.status = 'processing'
    statement.processing_started_at = timezone.now()
    statement.save()

    # Log start
    ProcessingLog.objects.create(
        statement=statement,
        level='info',
        message='Processing started'
    )

    try:
        # Update progress
        self.update_state(
            state='PROCESSING',
            meta={'progress': 10, 'message': 'Converting PDF...'}
        )

        # Process with estrattoconto
        estratto = estrattoconto.convert(
            statement.uploaded_file.path,
            use_cache=True
        )

        self.update_state(
            state='PROCESSING',
            meta={'progress': 50, 'message': 'Extracting transactions...'}
        )

        # Update statement metadata
        # (Assuming we can extract this from the data)
        statement.bank_type = "CENTROVENETO"  # TODO: Get from provider
        statement.account_number = "PLACEHOLDER"  # TODO: Extract from data

        # Create transactions
        df = estratto.get_dataframe()
        transactions_created = 0

        for _, row in df.iterrows():
            Transaction.objects.create(
                statement=statement,
                date=row.get('DATA MOV.'),
                value_date=row.get('VALUTA'),
                description=row.get('DESCRIZIONE OPERAZIONE', ''),
                debit=row.get('DARE_Numeric'),
                credit=row.get('AVERE_Numeric'),
                amount=row.get('amount', 0),
                payer=row.get('payer', ''),
                payee=row.get('payee', ''),
                id_mandato=row.get('id_mandato', ''),
                is_bill=row.get('is_bill', False),
                is_incoming_transfer=row.get('is_incoming_transfer', False),
                is_outgoing_transfer=row.get('is_outcoming_transfer', False),
                is_bank_fee=row.get('is_bank_fee', False),
                related_account=row.get('related_account', ''),
                period=row.get('period', ''),
            )
            transactions_created += 1

        self.update_state(
            state='PROCESSING',
            meta={'progress': 90, 'message': 'Finalizing...'}
        )

        # Update statement
        statement.status = 'completed'
        statement.processing_completed_at = timezone.now()
        statement.save()

        # Log success
        ProcessingLog.objects.create(
            statement=statement,
            level='info',
            message=f'Processing completed: {transactions_created} transactions extracted',
            details={'transaction_count': transactions_created}
        )

        return {
            'status': 'success',
            'transactions': transactions_created,
            'duration': statement.processing_duration
        }

    except Exception as e:
        # Update statement
        statement.status = 'failed'
        statement.processing_error = str(e)
        statement.processing_completed_at = timezone.now()
        statement.save()

        # Log error
        ProcessingLog.objects.create(
            statement=statement,
            level='error',
            message=f'Processing failed: {str(e)}',
            details={'error_type': type(e).__name__}
        )

        raise
```

#### views.py

```python
"""Django views for bank statement upload."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import BankStatement, Transaction
from .forms import BankStatementUploadForm
from .tasks import process_bank_statement


@login_required
def upload_statement(request):
    """Upload bank statement view."""
    if request.method == 'POST':
        form = BankStatementUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # Save file
            statement = form.save(commit=False)
            statement.uploaded_by = request.user
            statement.original_filename = request.FILES['uploaded_file'].name
            statement.save()

            # Trigger background processing
            process_bank_statement.delay(statement.id)

            return redirect('statement_detail', pk=statement.id)
    else:
        form = BankStatementUploadForm()

    return render(request, 'estrattoconto/upload.html', {'form': form})


@login_required
def statement_list(request):
    """List all bank statements."""
    statements = BankStatement.objects.filter(
        uploaded_by=request.user
    ).select_related('uploaded_by')

    return render(request, 'estrattoconto/list.html', {
        'statements': statements
    })


@login_required
def statement_detail(request, pk):
    """View statement details and transactions."""
    statement = get_object_or_404(
        BankStatement,
        pk=pk,
        uploaded_by=request.user
    )

    transactions = statement.transactions.all()

    return render(request, 'estrattoconto/detail.html', {
        'statement': statement,
        'transactions': transactions
    })


@login_required
@require_http_methods(["GET"])
def statement_progress(request, pk):
    """Get processing progress (for AJAX polling)."""
    statement = get_object_or_404(
        BankStatement,
        pk=pk,
        uploaded_by=request.user
    )

    # Get task status from Celery
    from celery.result import AsyncResult
    # Note: You'd need to store task_id on the statement model

    return JsonResponse({
        'status': statement.status,
        'transaction_count': statement.transaction_count,
        'error': statement.processing_error,
    })
```

#### serializers.py (Django REST Framework)

```python
"""DRF serializers for REST API."""

from rest_framework import serializers
from .models import BankStatement, Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer."""

    class Meta:
        model = Transaction
        fields = [
            'id', 'date', 'value_date', 'description',
            'debit', 'credit', 'amount',
            'payer', 'payee', 'id_mandato',
            'is_bill', 'is_incoming_transfer',
            'is_outgoing_transfer', 'is_bank_fee',
            'category', 'category_confidence',
            'created_at'
        ]


class BankStatementSerializer(serializers.ModelSerializer):
    """Bank statement serializer."""

    transaction_count = serializers.IntegerField(read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = BankStatement
        fields = [
            'id', 'original_filename', 'bank_type', 'period',
            'status', 'processing_error',
            'transaction_count', 'transactions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'processing_error']


class BankStatementUploadSerializer(serializers.ModelSerializer):
    """Serializer for upload."""

    class Meta:
        model = BankStatement
        fields = ['uploaded_file']

    def create(self, validated_data):
        user = self.context['request'].user
        statement = BankStatement.objects.create(
            uploaded_by=user,
            original_filename=validated_data['uploaded_file'].name,
            **validated_data
        )

        # Trigger processing
        from .tasks import process_bank_statement
        process_bank_statement.delay(statement.id)

        return statement
```

#### admin.py

```python
"""Django admin configuration."""

from django.contrib import admin
from .models import BankStatement, Transaction, ProcessingLog


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'bank_type', 'status',
        'transaction_count', 'uploaded_by', 'created_at'
    ]
    list_filter = ['status', 'bank_type', 'created_at']
    search_fields = ['original_filename', 'account_number']
    readonly_fields = [
        'status', 'processing_error',
        'processing_started_at', 'processing_completed_at',
        'created_at', 'updated_at'
    ]

    fieldsets = (
        ('File Information', {
            'fields': ('uploaded_file', 'original_filename', 'uploaded_by')
        }),
        ('Bank Information', {
            'fields': ('bank_type', 'period', 'account_number')
        }),
        ('Processing Status', {
            'fields': (
                'status', 'processing_error',
                'processing_started_at', 'processing_completed_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'description_short', 'amount',
        'payer', 'payee', 'is_bill'
    ]
    list_filter = [
        'is_bill', 'is_incoming_transfer',
        'is_outgoing_transfer', 'is_bank_fee',
        'date'
    ]
    search_fields = ['description', 'payer', 'payee']
    date_hierarchy = 'date'

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'statement', 'level', 'message']
    list_filter = ['level', 'timestamp']
    readonly_fields = ['timestamp']
```

### Acceptance Criteria
- [ ] Django models created and tested
- [ ] Celery tasks implemented
- [ ] Views for upload and display created
- [ ] REST API with DRF
- [ ] Admin interface configured
- [ ] Migrations generated
- [ ] Tests for all components

---

## Task 5.2: WebSocket Support for Real-time Progress

### Implementation

Using Django Channels:

```python
# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class StatementProcessingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time processing updates."""

    async def connect(self):
        self.statement_id = self.scope['url_route']['kwargs']['statement_id']
        self.room_group_name = f'statement_{self.statement_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def statement_progress(self, event):
        """Receive progress update."""
        await self.send(text_data=json.dumps({
            'type': 'progress',
            'progress': event['progress'],
            'message': event['message']
        }))
```

Update tasks.py to send WebSocket updates:

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_progress_update(statement_id, progress, message):
    """Send progress update via WebSocket."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'statement_{statement_id}',
        {
            'type': 'statement_progress',
            'progress': progress,
            'message': message
        }
    )
```

### Acceptance Criteria
- [ ] Django Channels configured
- [ ] WebSocket consumer implemented
- [ ] Real-time updates working
- [ ] Frontend JavaScript for WebSocket
- [ ] Tests added

---

## Summary Checklist

Phase 5 complete when:

- [ ] Django package created
- [ ] Models, views, tasks implemented
- [ ] REST API with DRF
- [ ] Admin interface complete
- [ ] WebSocket support (optional)
- [ ] Comprehensive tests
- [ ] Documentation for Django integration
- [ ] Example Django project

---

## Example Django Project Setup

```bash
# Create example project
django-admin startproject family_house_manager
cd family_house_manager

# Install estrattoconto-django
pip install estrattoconto-django

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'estrattoconto_django',
    'rest_framework',
    'celery',
]

# Configure Celery
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Celery worker
celery -A family_house_manager worker -l info

# Run server
python manage.py runserver
```

---

**Completion:** All phases documented and ready for implementation!
