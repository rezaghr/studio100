from django.contrib import admin
from .models import invoices # Import the model

# Register the user_data model with the admin site
@admin.register(invoices)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'amount', 'status')  # Fields to display in the list
    search_field = 'id'  # Add search functionality
    