from django.db import models

# Create your models here.
class CommonDetails(models.Model):
    common_id=models.BigAutoField(primary_key=True)
    reschedule_limit=models.IntegerField()