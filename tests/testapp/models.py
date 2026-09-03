from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=100)


class ProtectedChild(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
