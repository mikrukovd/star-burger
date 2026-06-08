from django.db import models


class Place(models.Model):
    address = models.CharField(max_length=200, unique=True)
    lon = models.FloatField(null=True)
    lat = models.FloatField(null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "место"
        verbose_name_plural = "места"
