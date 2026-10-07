from django.db import models
from django.contrib.auth.models import User


class Prediction(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=20)

    age = models.IntegerField()

    gender = models.CharField(max_length=1)

    neighbourhood = models.CharField(max_length=100)

    scholarship = models.IntegerField()
    hypertension = models.IntegerField()
    diabetes = models.IntegerField()
    alcoholism = models.IntegerField()
    handicap = models.IntegerField()
    sms_received = models.IntegerField()

    scheduled_day = models.DateTimeField()
    appointment_day = models.DateField()

    probability = models.FloatField()

    risk_level = models.CharField(max_length=20)

    recommendation = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.risk_level} - {self.probability}%"
