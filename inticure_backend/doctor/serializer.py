from dataclasses import fields
from sqlite3 import Time
from rest_framework import serializers,exceptions

from analysis.models import AppointmentHeader, AppointmentQuestions, AppointmentAnswers
from .models import CommonFileUploader, DoctorAvailableDates, DoctorAvailableTimeslots, Obeservations, Prescriptions, PrescriptionsDetail, AnalysisInfo, \
    DoctorProfiles, Timeslots, DoctorSpecializations, AppointmentTransferHistory, FollowUpReminder, \
    AppointmentDiscussion,Time,Medications,ConsumptionTime,DoctorCalenderUpdate,PatientMedicalHistory,\
    DoctorAddedTimeSlots,SeniorDoctorAvailableTimeSLots,JuniorDoctorSlots,EscalatedAppointment


class AppointmentHeaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentHeader
        fields = "__all__"


class AppointmentQuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentQuestions
        fields = "__all__"


class AppointmentAnswersSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentAnswers
        fields = "__all__"

class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
         model=Prescriptions
         fields="__all__"
class PrescriptionTextSerializer(serializers.ModelSerializer):
    class Meta:
        model=PrescriptionsDetail
        fields="__all__"
class ObservationsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Obeservations
        fields="__all__"
class AnalysisInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=AnalysisInfo
        fields="__all__"
class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorProfiles
        fields="__all__"
class CommonFileUploaderSerializer(serializers.ModelSerializer):
    class Meta:
        model=CommonFileUploader
        fields="__all__"
class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model=Timeslots
        fields="__all__"
class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorSpecializations
        fields="__all__"
class SeniorTransferLogSerializer(serializers.ModelSerializer):
    class Meta:
        model=AppointmentTransferHistory
        fields="__all__"
class FollowUpReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model=FollowUpReminder
        fields="__all__"

class AppointmentDiscissionSerializer(serializers.ModelSerializer):
    class Meta:
        model=AppointmentDiscussion
        fields="__all__"
class WorkingHourSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorAvailableTimeslots
        fields="__all__"
class WorkingDateSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorAvailableDates
        fields="__all__"
class WorkingCalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorCalenderUpdate
        fields="__all__"
class TimeSerializer(serializers.ModelSerializer):
    class Meta:
        model=Time
        fields="__all__"
class MedicationsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Medications
        fields="__all__"
class ConsumptionTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model=ConsumptionTime
        fields="__all__"

class PatientMedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model=PatientMedicalHistory
        fields="__all__"
    
class EscalatedAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EscalatedAppointment
        fields = '__all__'     

class DoctorAddedTimeSlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model=DoctorAddedTimeSlots
        fields="__all__"
    

class SeniorDoctorAvailableTimeSLotsSerializer(serializers.ModelSerializer):
    class Meta:
        model=SeniorDoctorAvailableTimeSLots
        fields="__all__"
        
class JuniorDoctorSlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model=JuniorDoctorSlots
        fields="__all__"
    