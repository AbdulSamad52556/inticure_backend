from django.db import models

# Create your models here.
class CustomerProfile(models.Model):
    customer_profile_id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField()
    age=models.IntegerField(blank=True, null=True)
    address=models.TextField(null=True)
    gender=models.CharField(max_length=20,blank=True, null=True)
    other_gender=models.CharField(max_length=20,blank=True, null=True)
    address=models.CharField(max_length=50,blank=True, null=True)
    date_of_birth=models.DateField(blank=True, null=True,auto_now_add=False)
    mobile_number=models.CharField(max_length=20, null=True)
    location=models.IntegerField(null=True)
    profile_pic=models.TextField(null=True)
    residence_location = models.CharField(max_length = 30, null = True)
    whatsapp_contact = models.CharField(max_length=20, null=True)
    confirmation_choice = models.CharField(max_length= 30, null=True)
    confirmation_email = models.CharField(max_length=255, default='', blank=True)
    
class AppointmentRatings(models.Model):
    appointment_id=models.BigIntegerField(null=True)
    doctor_id=models.BigIntegerField(null=True)
    user_id=models.BigIntegerField(null=True)
    rating_comments=models.TextField(null=True)
    rating=models.IntegerField(null=True)
    app_rating=models.IntegerField(null=True)
    added_by=models.CharField(max_length=25)

class StripeCustomer(models.Model):
    stripe_customer_id = models.BigAutoField(primary_key=True)
    stripe_customer_token_id = models.TextField()
    customer_id = models.IntegerField()

class RazorpayCustomer(models.Model):
    razorpay_customer_id = models.BigAutoField(primary_key=True)
    razorpay_customer_token_id = models.TextField()
    customer_id = models.IntegerField()

class TemporaryTransactionData(models.Model):
    temp_id=models.BigAutoField(primary_key=True)
    user_id=models.IntegerField()
    currency=models.CharField(max_length=10,null=True)
    total_amount=models.IntegerField(null=True)
    appointment_id=models.IntegerField(null=True)
    discount=models.IntegerField(null=True)
    coupon_id=models.IntegerField(null=True)
    tax=models.IntegerField(null=True)
    vendor_fee=models.IntegerField(null=True)

class Refund(models.Model):
    refund_id=models.CharField(max_length=50)
    customer_id=models.IntegerField()
    refund_status=models.IntegerField(default=0)
    refund_requested_date=models.DateField()
    refund_processed_date=models.DateField(null=True)
    appointment_id=models.IntegerField()
    appointment_date=models.DateField()
    refund_amount=models.IntegerField(default=0)
    
    