from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    current_price = models.FloatField()
    last_updated = models.DateTimeField()
    change_percent = models.CharField(max_length=20)

    def __str__(self):
        return self.symbol


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    funds = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)

