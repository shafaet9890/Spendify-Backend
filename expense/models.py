from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=False)

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Expense(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='expenses_user')
    title = models.CharField(max_length=150, blank=False, null=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='expenses_category')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.amount}"

