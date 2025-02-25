from django.db import models

# Create your models here.

from django.db import models
from admin_panel.models import user_data
# Create your models here.

class invoices(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing ID field
    user_id = models.ForeignKey(user_data, on_delete=models.CASCADE)  # Set 'on_delete' to prevent errors
    amount = models.BigIntegerField()
    status = models.CharField(max_length=6)

