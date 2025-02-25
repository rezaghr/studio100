from django.db import models

class user_data(models.Model):
    id = models.BigIntegerField(primary_key=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    number = models.BigIntegerField()
    remaining_days = models.IntegerField()
    def __str__(self):
        return str(self.id)
    
class price(models.Model):
    option = models.AutoField(primary_key=True)
    price = models.PositiveIntegerField()
    days = models.PositiveIntegerField()

class Video(models.Model):
    title = models.CharField(max_length=200)
    video_file = models.FileField(upload_to='videos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title