from django.db import models


class SavedRoll(models.Model):
    group = models.CharField(max_length=63)
    user = models.CharField(max_length=63)
    name = models.CharField(max_length=63)
    content = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["group", "user", "name"]
