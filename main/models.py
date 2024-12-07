# Create your models here.

from django.db import models

class StoreLocation(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    rating = models.FloatField()
    density = models.FloatField(null=True)
    avg_neighbor_rating = models.FloatField(null=True)
    predicted_score = models.FloatField(null=True)

    def __str__(self):
        return self.name