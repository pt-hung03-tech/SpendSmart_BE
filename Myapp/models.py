# myapp/models.py
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Thu nhập'),
        ('expense', 'Chi tiêu'),
    )

    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#2ecc71')
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='expense')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Thu nhập'),
        ('expense', 'Chi tiêu'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.type} - {self.amount}"