from django.contrib import admin

from customer.models import CustomerProfile,Refund

# Register your models here.
admin.site.register(CustomerProfile)
admin.site.register(Refund)