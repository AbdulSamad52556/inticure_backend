from django.contrib import admin

# Register your models here.
from .models import AppointmentReshedule, DoctorMapping, DoctorProfiles,Obeservations,\
     RescheduleHistory,Timeslots,AnalysisInfo,DoctorSpecializations,Time,DoctorAvailableDates,\
     DoctorAvailableTimeslots,DoctorLanguages,PrescriptionsDetail,Medications,ConsumptionTime,\
     Prescriptions,CommonFileUploader,SrDoctorEngagement,PatientMedicalHistory,DoctorAddedTimeSlots,\
     SeniorDoctorAvailableTimeSLots,DoctorCalenderUpdate

admin.site.register(DoctorProfiles)
admin.site.register(Obeservations)
admin.site.register(RescheduleHistory)
admin.site.register(AppointmentReshedule)
admin.site.register(Timeslots)
admin.site.register(Time)
admin.site.register(AnalysisInfo)
admin.site.register(DoctorSpecializations)
admin.site.register(DoctorMapping)
admin.site.register(DoctorLanguages)
admin.site.register(DoctorAvailableDates)
admin.site.register(DoctorAvailableTimeslots)
admin.site.register(PrescriptionsDetail)
admin.site.register(Medications)
admin.site.register(ConsumptionTime)
admin.site.register(Prescriptions)
admin.site.register(CommonFileUploader)
admin.site.register(SrDoctorEngagement)
admin.site.register(PatientMedicalHistory)
admin.site.register(DoctorAddedTimeSlots)
admin.site.register(SeniorDoctorAvailableTimeSLots)
admin.site.register(DoctorCalenderUpdate)
