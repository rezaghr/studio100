from django.contrib import admin
from .models import user_data , price, Video # Import the model

# Register the user_data model with the admin site
@admin.register(user_data)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'username', 'number', 'remaining_days')  # Fields to display in the list
    search_field = 'username'  # Add search functionality
    
@admin.register(price)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ('option', 'price', 'days')  # Fields to display in the list
    search_field = 'option'  # Add search functionality

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at')
    search_fields = ('title',)
    list_filter = ('uploaded_at',)