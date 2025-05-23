from pyexpat import model
from django.db import models


# Create your models here.
class InticureEarnings(models.Model):
    net_profit=models.BigIntegerField(null=True)
    net_expense=models.BigIntegerField(null=True)
    net_income=models.BigIntegerField(null=True)
    net_amount=models.BigIntegerField(null=True)
    net_profit_usd=models.BigIntegerField(default=0)
    net_expense_usd=models.BigIntegerField(default=0)
    net_income_usd=models.BigIntegerField(default=0)
    net_amount_usd=models.BigIntegerField(default=0)
    currency=models.CharField(null=True,max_length=10)
    
class Plans(models.Model):
    price_for_single=models.FloatField(null=True)
    price_for_couple=models.FloatField(null=True)
    location_id=models.IntegerField(null=True)
    location_name = models.CharField(max_length=30, null=True)
    doctor_id=models.IntegerField(null=True)
    doc_name=models.CharField(max_length=50, null=True)
    speciality=models.CharField(max_length=50, null=True)
    
class Duration(models.Model):
    doctor_id = models.IntegerField(null=True)
    duration = models.IntegerField(null=True)

class Locations(models.Model):
    location_id=models.BigAutoField(primary_key=True)
    location=models.CharField(max_length=20)
    currency=models.CharField(max_length=20)

    country_code=models.CharField(max_length=10,null=True)
class LanguagesKnown(models.Model):
    language_id=models.BigAutoField(primary_key=True)
    language=models.TextField(null=True)
    
class Payouts(models.Model):
    payout_id=models.BigAutoField(primary_key=True)
    appointment_id=models.IntegerField(null=True)
    payout_date=models.DateField(auto_now=True)
    payout_time=models.TimeField(auto_now=True)
    accepted_date=models.DateField(null=True)
    accepted_time=models.TimeField(null=True)
    doctor_id=models.IntegerField(null=True)
    base_amount=models.IntegerField(null=True)
    inticure_fee=models.IntegerField(null=True)
    payout_status=models.IntegerField(default=0)
    payout_amount=models.IntegerField(null=True)
   
class TotalPayouts(models.Model):
    payout_date=models.DateField(auto_now=True)
    payout_time=models.TimeField(auto_now=True)
    doctor_id=models.IntegerField(null=True)
    total_payouts=models.IntegerField(null=True)

class TotalEarnings(models.Model): 
    doctor_id=models.BigIntegerField()
    accepted_date=models.DateField(null=True)
    accepted_time=models.TimeField(null=True)
    total_earnings=models.IntegerField(null=True)

class Transactions(models.Model):
    transaction_id=models.BigAutoField(primary_key=True)
    invoice_id=models.IntegerField(null=True)
    transaction_amount=models.IntegerField(null=True)
    transaction_date=models.DateField(auto_now=True)
    transaction_time=models.TimeField(auto_now=True)
    payment_status=models.IntegerField(default=0)


class ReportCustomer(models.Model):
    appointment_id=models.IntegerField(null=True)
    customer_id=models.IntegerField(null=True)
    doctor_id=models.IntegerField(null=True)
    report_remarks=models.TextField(null=True)
    report_count=models.IntegerField(null=True)
class SpecializationTimeDuration(models.Model):
    specialization_id=models.BigAutoField(primary_key=True)
    specialization=models.CharField(null=True,max_length=50)
    time_duration=models.IntegerField(null=True)
class DiscountCoupons(models.Model):
    coupon_code=models.CharField(null=True,max_length=60)
    discount_percentage=models.IntegerField(null=True)
    expiry_date=models.DateField(null=True)
class CouponRedeemLog(models.Model):
    user_id=models.IntegerField(null=True)
    coupon_id=models.IntegerField(null=True)
    
class Notification(models.Model):
    user_id = models.IntegerField(null=True)
    on_time=models.TimeField(auto_now=True,null=True)
    on_date = models.DateField(auto_now=True)
    description = models.CharField(max_length=400, null=True)
    did_open = models.BooleanField(default=False)