from django.shortcuts import render
from analysis.models import Category
# Create your views here.
from cryptography.fernet import Fernet
from datetime import timedelta,datetime as dt
import datetime
from doctor.models import DoctorSpecializations
from administrator.models import Duration, Plans
# key for encryption and decryption

key = 'j-uNkGoA-ZZrVQtdyGk2l0r2SCuZNq2gY9lc4yZit-I='
print(key)
 
encryption_key = Fernet(key)
print(encryption_key)


def get_category_name(id):
    try:
        category=Category.objects.get(id=id).title
    except:
        category=None
    return category


    

def get_appointment_time(slots,date=None,specialization=None,doctor_flag=None,doctor_id=None):
    try:
        if specialization == 'no specialization':
            doctor_id = Plans.objects.filter(doc_name='Junior doctor').first().doctor_id
            duration = get_duration(doctor_id)
        else:
            duration =get_duration(doctor_id)
        # Assuming slots is in the format "04:00AM"
        start_time_str = str(date) + "T" + datetime.datetime.strptime(slots, '%I:%M%p').strftime('%H:%M')
        
        # Calculate end time by adding 10 minutes to start time
        end_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M") + datetime.timedelta(minutes=duration)
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")

        print(start_time_str, end_time_str)
        return start_time_str, end_time_str
    except Exception as e:
        print(e)
        return None, None

def get_duration(doctor_id):
    try:
        duration=Duration.objects.get(doctor_id=doctor_id).duration
    except:
        duration=60
    return duration
