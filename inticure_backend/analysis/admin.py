from django.contrib import admin

# Register your models here.
from analysis.models import Category,Questionnaire,Options,AppointmentHeader,Invoices,EmailOtpVerify,OtpVerify

admin.site.register(Category)
admin.site.register(Questionnaire)
admin.site.register(Options)
admin.site.register(AppointmentHeader)
admin.site.register(Invoices)
admin.site.register(EmailOtpVerify)
admin.site.register(OtpVerify)