from django.db import models


class Place(models.Model):
    address = models.CharField("адрес", max_length=200, unique=True)
    lon = models.FloatField("долгота", null=True)
    lat = models.FloatField("широта", null=True)
    updated_at = models.DateTimeField("дата последнего обновления", auto_now=True)

    class Meta:
        verbose_name = "место"
        verbose_name_plural = "места"
