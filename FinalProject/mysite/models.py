from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
