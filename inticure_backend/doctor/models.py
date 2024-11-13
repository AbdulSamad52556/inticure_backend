from django.db import models

# Create your models here.

class DoctorProfiles(models.Model):
    doctor_profile_id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField()
    location=models.CharField(max_length=30)
    department=models.CharField(max_length=20)
    specialization=models.CharField(max_length=20)
    doctor_flag=models.CharField(max_length=10)
    mobile_number=models.CharField(max_length=20)
    gender=models.CharField(max_length=10,null=True)
    working_date_frm=models.DateField(null=True)
    working_date_to=models.DateField(null=True)
    time_slot_from=models.IntegerField(null=True)
    time_slot_to=models.IntegerField(null=True)
    qualification=models.TextField(null=True)
    address=models.TextField(null=True)
    is_accepted=models.IntegerField(null=True)
    registration_certificate=models.TextField(null=True)
    address_proof=models.TextField(null=True)
    sign_file_name=models.TextField(null=True)
    sign_file_size=models.CharField(null=True,max_length=20)
    reg_file_name=models.TextField(null=True)
    reg_file_size=models.CharField(null=True,max_length=20)
    addr_file_name=models.TextField(null=True)
    addr_file_size=models.CharField(null=True,max_length=20)
    signature=models.TextField(null=True)
    certificate_no=models.TextField(null=True)
    profile_pic=models.TextField(null=True)
    profile_file_name=models.TextField(null=True)
    profile_file_size=models.TextField(null=True)
    doctor_bio=models.CharField(null=True,max_length=500)
    
class Obeservations(models.Model):
    appointment_id=models.BigIntegerField()
    doctor_id=models.BigIntegerField(null=True)
    uploaded_time=models.TimeField(auto_now=True)
    uploaded_date=models.DateField(auto_now=True)
    observe=models.TextField()
class AppointmentReshedule(models.Model):
    appointment_id=models.BigIntegerField()
    user_id=models.BigIntegerField()
    reschedule_count=models.IntegerField(default=0)
    time_slot=models.CharField(max_length=30,null=True)
    rescheduled_time=models.TimeField(null=True)
    rescheduled_date=models.DateField(null=True)
    doctor_id=models.BigIntegerField(null=True)
    sr_rescheduled_time=models.CharField(max_length=30,null=True)
    sr_rescheduled_date=models.DateField(null=True)
    
class RescheduleHistory(models.Model):
    appointment_id=models.BigIntegerField()
    user_id=models.BigIntegerField()
    time_slot=models.CharField(max_length=30,null=True)
    rescheduled_time=models.TimeField(null=True)
    doctor_id=models.CharField(max_length=100,null=True)
    rescheduled_date=models.DateField(null=True)
    sr_rescheduled_time=models.CharField(max_length=30,null=True)
    sr_rescheduled_date=models.DateField(null=True)

class Prescriptions(models.Model):
    appointment_id=models.BigIntegerField()
    uploaded_time=models.TimeField(auto_now=True,null=True)
    uploaded_date=models.DateField(auto_now=True,null=True)
    prescription=models.TextField(null=True)
    prescript_file_name=models.TextField(null=True)
    prescript_file_size=models.CharField(null=True,max_length=20)
class PrescriptionsDetail(models.Model):
    appointment_id=models.BigIntegerField()
    doctor_id=models.IntegerField(null=True)
    uploaded_time=models.TimeField(auto_now=True)
    uploaded_date=models.DateField(auto_now=True)
    prescriptions_text=models.TextField(null=True)
    tests_to_be_done=models.TextField(null=True)
class Medications(models.Model):
    medication_id=models.BigAutoField(primary_key=True)
    prescription_id=models.BigIntegerField()
    medication=models.TextField()
    duration_number=models.IntegerField()
    duration=models.TextField()
    side_effects=models.TextField()
    consumption_detail=models.TextField()
    can_substitute=models.IntegerField()
class ConsumptionTime(models.Model):
    medication_id=models.BigIntegerField()
    prescription_id=models.BigIntegerField(null=True)
    consumption_time=models.CharField(max_length=20)
class AnalysisInfo(models.Model):
    appointment_id=models.BigIntegerField()
    doctor_id=models.BigIntegerField(null=True)
    uploaded_time=models.TimeField(auto_now=True)
    uploaded_date=models.DateField(auto_now=True)
    analysis_info_text=models.TextField(null=True)
    analysis_info_path=models.TextField(null=True)
    file_name=models.TextField(null=True)
    file_size=models.CharField(null=True,max_length=20)
class CommonFileUploader(models.Model):
    # appointment_id=models.BigIntegerField()
    uploaded_time=models.TimeField(auto_now=True,null=True)
    uploaded_date=models.DateField(auto_now=True,null=True)
    common_file=models.FileField()
    # file_flag=models.CharField(max_length=20,null=True)

"""Model for Timeslots"""
class Timeslots(models.Model):
    time_slots=models.CharField(max_length=30)
    duration = models.IntegerField()
"""Senior doc engagement"""
class SrDoctorEngagement(models.Model):
    doc_id=models.BigAutoField(primary_key=True)
    appointment_id=models.BigIntegerField(null=True)
    user_id=models.BigIntegerField()
    date=models.DateField()
    time_slot=models.CharField(max_length=30)

"""Junior doc engagement"""
class JrDoctorEngagement(models.Model):
    doc_id=models.BigAutoField(primary_key=True)
    appointment_id=models.BigIntegerField(null=True)
    user_id=models.BigIntegerField()
    date=models.DateField()
    time_slot=models.CharField(max_length=30)

class DoctorSpecializations(models.Model):
    specialization=models.CharField(max_length=100)
    time_duration=models.IntegerField(null=True)
    description=models.TextField(null=True)
class AppointmentTransferHistory(models.Model):
    appointment_id=models.BigIntegerField(null=True)
    new_doctor=models.IntegerField(null=True)
    old_doctor=models.IntegerField(null=True)
    transfered_time=models.TimeField(auto_now=True)
    transfered_date=models.DateField(auto_now=True)

class DoctorMapping(models.Model):
    appointment_id=models.BigIntegerField(null=True)
    mapped_doctor=models.IntegerField(null=True)
    doctor_flag=models.CharField(max_length=10,null=True)
    added_doctor=models.IntegerField(default=0)

class DoctorLanguages(models.Model):
    doctor_id=models.BigIntegerField(null=True)
    languages=models.CharField(max_length=100,null=True)

class FollowUpReminder(models.Model):
    appointment_id=models.BigIntegerField(null=True)
    follow_up_for=models.CharField(max_length=100,null=True)
    remarks=models.TextField(null=True)
    duration=models.CharField(max_length=100,null=True)

class AppointmentDiscussion(models.Model):
    appointment_id=models.BigIntegerField(null=True)
    content=models.TextField(null=True)
    is_query=models.IntegerField(default=0)
    is_reply=models.IntegerField(default=0)
    created_date=models.DateField(auto_now=True)
    created_time=models.TimeField(auto_now=True)

class DoctorAvailableTimeslots(models.Model):
    doctor_id=models.BigIntegerField(null=True)
    day=models.CharField(null=True,max_length=30)
    time_slot_from=models.IntegerField(null=True)
    time_slot_to=models.IntegerField(null=True)
    slot_counter=models.IntegerField(null=True)
class DoctorAvailableDates(models.Model):
    doctor_id=models.BigIntegerField(null=True)
    date=models.DateField(null=True)
    day=models.CharField(null=True,max_length=30)
    
    '''store information if a doctor is available for particular date'''
class DoctorCalenderUpdate(models.Model):
    doctor_id=models.BigIntegerField(null=True)
    date=models.DateField(null=True)
    day=models.CharField(null=True,max_length=30)
    time_slot_from=models.IntegerField(null=True)
    time_slot_to=models.IntegerField(null=True)
    
class Time(models.Model):
    time=models.CharField(null=True,max_length=10)
class AppointmentCancellationLog(models.Model):
    appointment_id=models.BigIntegerField()
    cancelled_date=models.DateField(auto_now=True)
    cancelled_time=models.TimeField(auto_now=True)
    cancelled_by=models.CharField(max_length=20)


class PatientMedicalHistory(models.Model):
    patient_medical_history_id=models.BigAutoField(primary_key=True)
    doctor_id=models.IntegerField()
    doctor_flag=models.IntegerField()
    appointment_id=models.IntegerField()
    user_id=models.IntegerField()
    height=models.CharField(max_length=20)
    weight=models.CharField(max_length=20)
    is_allergic=models.CharField(max_length=200)
    medical_history=models.CharField(max_length=200)
    prescription_history=models.CharField(max_length=200)
    other_suppliments_history=models.CharField(max_length=200)
    height_unit = models.CharField(default='cm', max_length=10)
    weight_unit = models.CharField(default='Kg', max_length=10)
    
    
''' This model is used to store each slots of a doctor on adding working hours of each doctor  '''
class DoctorAddedTimeSlots(models.Model):
    doctor_time_slots_id=models.BigAutoField(primary_key=True)
    doctor_id=models.IntegerField()
    slot=models.IntegerField()
    date=models.DateField(null=True)

class SeniorDoctorAvailableTimeSLots(models.Model):
    senior_doctor_timeslot_id=models.BigAutoField(primary_key=True)
    doctor_id=models.IntegerField()
    date=models.DateField()
    time_slot=models.CharField(max_length=200)
    end_time=models.CharField(max_length=200,null=True)
    is_active=models.IntegerField(default=0)


class JuniorDoctorSlots(models.Model):
    junior_doctor_slot_id=models.BigAutoField(primary_key=True)
    doctor_id=models.IntegerField()
    date=models.DateField()
    time_slot=models.CharField(max_length=200)
    is_active=models.IntegerField(default=0)

class EscalatedAppointment(models.Model):
    appointment_id = models.IntegerField()
    appointment_status=models.IntegerField()
    appointment_date=models.DateField()
    time_slot=models.CharField(max_length=200)
    specialization = models.CharField(max_length=200)
    doctor_id = models.IntegerField()
    status = models.BooleanField()
    user_id = models.IntegerField()