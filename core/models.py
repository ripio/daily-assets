from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_VIEWER = 'viewer'
    ROLE_CHOICES = [(ROLE_ADMIN, 'Admin'), (ROLE_VIEWER, 'Viewer')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_VIEWER)

    def __str__(self):
        return f'{self.user.username} ({self.role})'

    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.user.is_superuser


class DailyUpload(models.Model):
    date = models.DateField(unique=True)
    file = models.FileField(upload_to='uploads/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'Upload {self.date}'


class BalanceRow(models.Model):
    upload = models.ForeignKey(DailyUpload, on_delete=models.CASCADE, related_name='rows')
    workspace = models.CharField(max_length=100, blank=True)
    account_name = models.CharField(max_length=255, blank=True)
    account_id = models.CharField(max_length=100, blank=True)
    asset = models.CharField(max_length=50, blank=True)
    total_balance = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    from_field = models.CharField(max_length=50, blank=True, db_column='from_source')
    category = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=50, blank=True)
    asset_group = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    usd = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['upload', 'from_field', 'category']),
            models.Index(fields=['upload', 'asset_group']),
            models.Index(fields=['upload', 'type']),
        ]

    def __str__(self):
        return f'{self.asset_group} / {self.asset} ({self.upload.date})'
