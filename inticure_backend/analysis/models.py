from contextlib import nullcontext
from enum import auto
from statistics import mode
from django.db import models

# Create your models here.
"""Holds the catergory of medical issues"""


class Category(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=250, null=True)
    image = models.ImageField(upload_to="", null=True)


"""Holds the details  of analysis questions  that user submit before taking an appointment"""


class Questionnaire(models.Model):
    question = models.CharField(max_length=300)
    answer_type = models.CharField(max_length=50)
    category_id = models.IntegerField()
    customer_gender=models.CharField(max_length=30,null=True)

"""Holds the details  of options of  questions  that user submit before taking an appointment"""


class Options(models.Model):
    question_id = models.IntegerField()
    option = models.CharField(max_length=100)


"""Holds the details  of an appointment.here appointment_status 1= , 2= , 3= cancel, 4 = ,5 = , 6= completed, 7 =reschedule ,8= ,9= order marked no show"""


class AppointmentHeader(models.Model):
    appointment_id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField()
    category_id = models.IntegerField()
    appointment_status = models.IntegerField(default=0)
    appointment_date=models.DateField()
    appointment_time=models.TimeField(null=True)
    appointment_time_slot_id=models.CharField(null=True,max_length=40)
    escalated_date=models.DateField(null=True)
    escalated_time_slot=models.CharField(null=True,max_length=20)
    junior_doctor=models.IntegerField(null=True)
    senior_doctor=models.IntegerField(null=True)
    is_free=models.IntegerField(default=1)
    followup_id=models.IntegerField(null=True)
    booked_on = models.DateField(auto_now=True)
    booked_on_time=models.TimeField(auto_now=True,null=True)
    type_booking=models.CharField(max_length=20)
    followup_remark=models.TextField(null=True)
    followup_created_by=models.CharField(max_length=20,null=True)
    followup_created_doctor_id=models.IntegerField(null=True)
    language_pref=models.CharField(max_length=20,null=True)
    gender_pref=models.CharField(max_length=20,null=True)
    meeting_link=models.CharField(max_length=200,null=True)
    senior_meeting_link=models.CharField(max_length=200,null=True)
    customer_message=models.TextField(null=True)
    loc_id = models.IntegerField(default=0,null=True)
    payment_status = models.BooleanField(default=False, null=True)
    payment_gateway = models.CharField(max_length=20, null=True)
    session_type = models.CharField(default = 'single', max_length = 20,null=True)
    can_reschedule = models.BooleanField(default=False)
    refund = models.CharField(max_length=30, default='0')
    total = models.CharField(max_length=20, null=True)
    cancelled_date = models.DateTimeField(null=True)

"""Holds the details  of analysis questions user submitted before taking appointment"""


class AppointmentQuestions(models.Model):
    appointment_questions_id = models.BigAutoField(primary_key=True)
    appointment_id = models.IntegerField()
    question_id = models.IntegerField()
    question = models.TextField()


"""Holds the details  of analysis answers user submitted before taking appointment"""
class AppointmentAnswers(models.Model):
    appointment_answer_id = models.BigAutoField(primary_key=True)
    appointment_questions_id = models.IntegerField()
    option_id = models.IntegerField(null=True)
    answer = models.TextField(null=True)
"""Order Invoice Details"""
class Invoices(models.Model):
    invoice_id=models.BigAutoField(primary_key=True)
    appointment_id=models.IntegerField()
    user_id=models.IntegerField()
    bill_for=models.CharField(max_length=25)
    gender=models.CharField(max_length=15,null=True)
    age=models.IntegerField(null=True)
    mobile_number=models.CharField(max_length=20, null=True)
    date_of_birth=models.DateField(null=True)
    address=models.CharField(max_length=50,null=True)
    email=models.CharField(max_length=30,null=True)
    appointment_date=models.DateField(null=True)
    appointment_time=models.TextField(null=True)
    appointment_for=models.CharField(max_length=20,null=True)
    issue_date=models.DateField(auto_now=True)
    issue_time=models.TimeField(auto_now=True,null=True)
    service=models.CharField(max_length=60,null=True)
    due_date=models.DateField()
    vendor_fee=models.IntegerField(null=True)
    tax=models.IntegerField(null=True)
    discounts=models.IntegerField(null=True)
    total=models.IntegerField()
    status=models.IntegerField() 
    mode_of_pay=models.CharField(max_length=20,null=True)
    doctor_id=models.IntegerField(null=True)
    doctor_name=models.CharField(max_length=100,null=True)
    category_id=models.IntegerField(null=True)

"""Verify otp of user"""
class OtpVerify(models.Model):
    mobile_number=models.CharField(max_length=20, null=True)
    otp=models.CharField(max_length=10,null=True)
class EmailOtpVerify(models.Model):
    email=models.CharField(max_length=100)
    otp=models.CharField(max_length=10,null=True)
"""Answer type selection"""
class AnswerType(models.Model):
    answer_type=models.CharField(max_length=100,null=True)