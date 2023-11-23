from django.db import models


# Create your models here.
class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    current_price = models.FloatField()
    last_updated = models.DateTimeField()
    change_percent = models.CharField(max_length=20)

    def __str__(self):
        return self.symbol
