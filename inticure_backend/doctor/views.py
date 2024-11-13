from calendar import weekday
from heapq import merge
import calendar
import random
from tempfile import TemporaryFile
from time import strptime, time
from unicodedata import category
from unittest import result
from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render
from django.db.models import Q
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import F  
from django.utils import timezone
# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, status, permissions, views
import datetime
from datetime import timedelta,datetime as dt
from django.db import IntegrityError
from analysis.models import AppointmentHeader, AppointmentQuestions, AppointmentAnswers,Invoices
from common.filter import custom_filter
from conf_files.google_meet import generate_google_meet
from .serializer import AppointmentHeaderSerializer, AppointmentQuestionsSerializer, \
    AppointmentAnswersSerializer, PrescriptionSerializer, ObservationsSerializer, PrescriptionTextSerializer, \
    AnalysisInfoSerializer, DoctorProfileSerializer, CommonFileUploaderSerializer, TimeSlotSerializer, \
    SpecializationSerializer, SeniorTransferLogSerializer, FollowUpReminderSerializer, AppointmentDiscissionSerializer,\
    WorkingHourSerializer,WorkingDateSerializer,TimeSerializer,MedicationsSerializer,ConsumptionTimeSerializer,PatientMedicalHistorySerializer,\
        WorkingDateSerializer,DoctorAddedTimeSlotsSerializer,SeniorDoctorAvailableTimeSLotsSerializer,\
    JuniorDoctorSlotsSerializer,EscalatedAppointmentSerializer
from administrator.serializer import PayoutsSerializer,UserSerializer,LocationSerializer

from django.contrib.auth.models import User

from customer.models import CustomerProfile,Refund
from .models import AnalysisInfo, AppointmentTransferHistory, DoctorAvailableDates, DoctorAvailableTimeslots, DoctorMapping, DoctorProfiles, \
    DoctorSpecializations, Obeservations, AppointmentReshedule, Prescriptions, \
    RescheduleHistory, PrescriptionsDetail, CommonFileUploader, Timeslots, JrDoctorEngagement,Time,\
    SrDoctorEngagement, DoctorLanguages, FollowUpReminder, AppointmentDiscussion,ConsumptionTime,Medications,\
    DoctorCalenderUpdate,PatientMedicalHistory,DoctorAddedTimeSlots,SeniorDoctorAvailableTimeSLots,\
    JuniorDoctorSlots, EscalatedAppointment
from administrator.models import Payouts, Plans, TotalPayouts, Transactions, ReportCustomer,\
    SpecializationTimeDuration,InticureEarnings, Locations, Duration
import json
from common.views import get_category_name,get_appointment_time

# from common.models import CommonDetails
from common.common import MEET
from common.views import encryption_key
from common.twilio_test import MessageClient
sms_service=MessageClient()


def get_patient_medical_details(user_id,appointment_id):
    try:
        patient_history= PatientMedicalHistorySerializer(
                        PatientMedicalHistory.objects.get(user_id=user_id, appointment_id = appointment_id)).data
        # print(patient_history,"1")
    except Exception as e:
        # print("Exception",e)
        patient_history=None
    return patient_history
    

''' Function to Assign appointment for senior doctor'''

def assign_senior_doctor(request):
    filter={}
    if "language_pref" in request.data and request.data['language_pref'] != "":
        filter['user_id__in']=DoctorLanguages.objects.filter(
            languages=request.data['language_pref']).values_list('doctor_id',flat=True)
    if "gender_pref" in request.data and request.data['gender_pref'] != "":
        filter['gender']=request.data['gender_pref']
    if "specialization" in request.data and request.data['specialization'] != "":
        filter['specialization']=request.data['specialization']
    #if "doctor_flag" in request.data and request.data['doctor_flag'] == 1:
    filter['doctor_flag']="senior"
    #doctor_id_list = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
    # if request.data['doctor_id'] :
    #     print("doctor id is available",request.data['doctor_id'])
    #     doctor_id = custom_filter(DoctorProfiles, filter)
    #     doctor_id_list=doctor_id.exclude(user_id=request.data['doctor_id']).values_list('user_id',flat=True)
    # else:
    if 'doctor_id' in request.data and request.data['doctor_id']:
        # print("doctor_id in request",request.data['doctor_id'])
        doctor_id_list = custom_filter(DoctorProfiles, filter).exclude(user_id=request.data['doctor_id']).values_list('user_id',flat=True)
    else:
        doctor_id_list = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
    # print("first-filtered",doctor_id_list)
    appointment_date_=dt.strptime(request.data['appointment_date'],"%Y-%m-%d")
    weekday=appointment_date_.strftime("%A")
    try:
        # time_slot_from=DoctorAvailableTimeslots.objects.filter(day=weekday).values_list(
        #             "time_slot_from",flat=True)
        # time_slot_to=DoctorAvailableTimeslots.objects.filter(day=weekday).values_list(
        #             "time_slot_to",flat=True)
        # print(weekday,time_slot_from,time_slot_to,max(time_slot_to),min(time_slot_from))
        # time_from=Timeslots.objects.get(id=min(time_slot_from))
        # time_to=Timeslots.objects.get(id=max(time_slot_to))
        # print("time from", time_from.time_slots,"time to",time_to.time_slots)
        # start=dt.strptime(time_from.time_slots.split('-')[0].strip(), '%I%p').time()
        # end=dt.strptime(time_to.time_slots.split('-')[1].strip(), '%I%p').time()
        # print(start,"start",end,"end")
        # print("time in range ",time_in_range(start, end, 
        # dt.strptime(request.data['time_slot'].split('-')[1].strip(), '%I:%M%p').time()))
        end_time = None
        if '-' in request.data['time_slot']:
            start_time = request.data['time_slot'].split(' - ')[0]
            end_time = request.data['time_slot'].split(' - ')[1]
        else:
            start_time = request.data['time_slot']
        if SeniorDoctorAvailableTimeSLots.objects.filter(date=appointment_date_,time_slot=start_time).count() > 0:
        # if time_in_range(start, end,
        #     dt.strptime(request.data['time_slot'].split('-')[1].strip(), '%I:%M%p').time())==True:
            # print("Timeslot-api")
            # doctor_id_time_slots=DoctorAvailableTimeslots.objects.filter(
            # doctor_id__in=doctor_id_list,day=weekday,date=appointment_date_).values_list("doctor_id",flat=True)
            # print(doctor_id_time_slots)
            if end_time:
                doctor_id_time_slots=SeniorDoctorAvailableTimeSLots.objects.filter(date=appointment_date_,time_slot=start_time,end_time = end_time).values_list("doctor_id",flat=True)
            else:
                doctor_id_time_slots=SeniorDoctorAvailableTimeSLots.objects.filter(date=appointment_date_,time_slot=start_time).values_list("doctor_id",flat=True)

            # print(doctor_id_time_slots,"doctor_id_time_slots")
            filter['user_id__in']=doctor_id_time_slots
            doc_id = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
            # print(doc_id)
            if doc_id:
                random_id=doc_id[0]
                return random_id
    except Exception as e:
        print(e)
        return 0

    else:
        return 0


@csrf_exempt  # Disables CSRF protection for this endpoint (only if necessary)
def block_doctor(request, doctor_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action', '')

            if action == 'block':
                doctor = DoctorProfiles.objects.get(doctor_profile_id=doctor_id)
                doctor.is_blocked = True
                doctor.save() 

                return JsonResponse({'status': 'success', 'message': 'Doctor blocked successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action specified.'}, status=400)
        except DoctorProfiles.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Doctor not found.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@csrf_exempt  # Disables CSRF protection for this endpoint (only if necessary)
def block_doctor(request, doctor_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action', '')

            if action == 'block':
                doctor = DoctorProfiles.objects.get(doctor_profile_id=doctor_id)
                doctor.is_blocked = True
                doctor.save() 

                return JsonResponse({'status': 'success', 'message': 'Doctor blocked successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action specified.'}, status=400)
        except DoctorProfiles.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Doctor not found.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@csrf_exempt  # Disables CSRF protection for this endpoint (only if necessary)
def unblock_doctor(request, doctor_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action', '')

            if action == 'block':
                doctor = DoctorProfiles.objects.get(doctor_profile_id=doctor_id)
                doctor.is_blocked = False
                doctor.save() 

                return JsonResponse({'status': 'success', 'message': 'Doctor blocked successfully.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action specified.'}, status=400)
        except DoctorProfiles.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Doctor not found.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
"""View to list appointments"""
@api_view(['POST'])
def appointment_list_view(request):
    print("###########appointment list view#####################")
    filter = {}
    doctor_appointments=[]
    """Filtering Appointment list"""
    # print(request.data)
    # print(request.data['doctor_flag'])
    if 'doctor_flag' in request.data and request.data['doctor_flag'] != '':
    #    print("doctor_flag")
       doctor_flag=request.data['doctor_flag']

       if doctor_flag==0:
            # print("user_list")
            if 'user_id' in request.data and request.data['user_id'] !='':
               filter['user_id']=request.data['user_id']

       if doctor_flag==1:
            # print("sen_list")
            # print(request.data)
            doctor_appointments=DoctorMapping.objects.filter(mapped_doctor=request.data['user_id']).values_list('appointment_id', flat=True)
            # print(doctor_appointments,"IDIDIDID")
            filter['appointment_id__in']=doctor_appointments

       if doctor_flag==2:
            # print('jr_list')
            doctor_appointments=DoctorMapping.objects.filter(
            mapped_doctor=request.data['user_id'])
            # print("doctor appointments",doctor_appointments)
            appointment_list=doctor_appointments.values_list('appointment_id', flat=True)
            # print(appointment_list,"IDIDIDID")
            filter['appointment_id__in']=appointment_list
            filter['junior_doctor']=request.data['user_id']

    if 'appointment_status' in request.data and request.data['appointment_status']:
            filter['appointment_status__in'] = request.data['appointment_status']
    if 'category_id' in request.data and request.data["category_id"]!='':
            filter['category_id'] = request.data['category_id']
    if 'appointment_month' in request.data and request.data['appointment_month'] !='':
            filter['appointment_date__month']=request.data['appointment_month']

    queryset1 = custom_filter(AppointmentHeader, filter).order_by('-appointment_id')

    appointment_data = AppointmentHeaderSerializer(queryset1, many=True).data
    # print('178 ', appointment_data)
    # print(appointment_data)
    for user in appointment_data:
         user_id=user['user_id']
         appointment_id=user['appointment_id']
         junior_doc_id=DoctorMapping.objects.filter(appointment_id=appointment_id,
         doctor_flag="junior").values_list('mapped_doctor',flat=True)
         senior_doc_id=DoctorMapping.objects.filter(appointment_id=appointment_id,
         doctor_flag="senior").values_list('mapped_doctor',flat=True)
        #  print(user_id)
         cat_id=user['category_id']
         user['time_slot']=user['appointment_time_slot_id']
         user['escalate_time_slots']=user['escalated_time_slot']
       
         user['category']=get_category_name(cat_id)
        
         try:
           queryset_user=User.objects.get(id=user_id)
           's'
           customer = CustomerProfile.objects.get(user_id = queryset_user.id)
        #    print(queryset_user)
           user['user_fname']=queryset_user.first_name
           user['user_lname']=queryset_user.last_name
           user['user_mail']=queryset_user.email
           user['user_phone']=customer.mobile_number
         except:
            user['user_fname']=""
            user['user_lname']=""
            user['user_mail']=""
         try:
           queryset_user=User.objects.get(id=user['junior_doctor'])
        #    print(queryset_user)
           user['junior_doc_id']=queryset_user.id
           user['junior_doc_name']=queryset_user.first_name+queryset_user.last_name
           user['jr_email']=queryset_user.username
           user['specialization']=get_doctor_specialization(user['junior_doctor'])
         except Exception as e:
            user['junior_doc_name']=""
         try:
           queryset_user=User.objects.get(id=user['senior_doctor'])
        #    print(queryset_user)
           user['senior_doc_id']=queryset_user.id
           user['senior_doc_name']=queryset_user.first_name+queryset_user.last_name
           user['specialization']=get_doctor_specialization(user['senior_doctor'])
           user['sr_email']=queryset_user.username
           try:
              
              doctor_id=DoctorMapping.objects.get(added_doctor=1,appointment_id=appointment_id).mapped_doctor
              user["added_doctor"]=get_users_name(doctor_id)
              user['added_doctor_id']=doctor_id
           except Exception as e:
              user["added_doctor"]=None
              user['added_doctor_id']=None
         except Exception as e:
            user['senior_doc_name']=""
         try:
            queryset_invoice=Invoices.objects.get(appointment_id=appointment_id)
            user['invoice_status']=queryset_invoice.status
            user['invoice_id']=queryset_invoice.invoice_id
         except:
            user['invoice_status']=""
            user['invoice_id']=""
         user['patient_medical_history']=get_patient_medical_details(user_id, appointment_id)
         try:
            reschedule=AppointmentReshedule.objects.get(appointment_id=appointment_id)
            user['rescheduled_time']=reschedule.time_slot
            user['rescheduled_date']=reschedule.rescheduled_date
            user['rescheduled_count']=reschedule.reschedule_count
            user['sr_rescheduled_time']=reschedule.sr_rescheduled_time
            user['sr_rescheduled_date']=reschedule.sr_rescheduled_date
         except Exception as e:
           user['rescheduled_time']=''
           user['rescheduled_date']=''
           user['rescheduled_count']=''
           user['sr_rescheduled_time']=''
           user['sr_rescheduled_date']=''
    for appointment in appointment_data:
        prescript= PrescriptionSerializer(Prescriptions.objects.filter(
            appointment_id=appointment['appointment_id']),
            many=True).data
        appointment['prescriptions']=prescript
        appointment_question_data = AppointmentQuestionsSerializer(
            AppointmentQuestions.objects.filter(appointment_id=appointment['appointment_id']), many=True).data
        for question in appointment_question_data:
            question['answers'] = AppointmentAnswersSerializer(
                AppointmentAnswers.objects.filter(appointment_questions_id=question['appointment_questions_id']),
                many=True).data
        appointment['questions'] = appointment_question_data
        try:
            transfered_doctor=AppointmentTransferHistory.objects.get(old_doctor=appointment['doctor_id'],
            appointment_id=appointment['appointment_id'])
        except Exception as e :
            transfered_doctor=None
        # print("appointment transfer history",transfered_doctor)
        if transfered_doctor:
           prescript_text=PrescriptionTextSerializer(
           PrescriptionsDetail.objects.filter(
               appointment_id=appointment_data['appointment_id'],doctor_id=appointment['doctor_id']),many=True).data
           
           for prescriptions in prescript_text:
                medicines=MedicationsSerializer(Medications.objects.filter(
                prescription_id=prescriptions['id']),many=True).data
                prescriptions['medicines']=medicines
                try:

                   prescriptions['qualification']=DoctorProfiles.objects.filter(
                    user_id=prescriptions['doctor_id']).qualification
                   prescriptions['address']=DoctorProfiles.objects.filter(
                    user_id=prescriptions['doctor_id']).address
                except Exception as e:
                    prescriptions['qualification']=""
                    prescriptions['address']=""
                for consumption in medicines:
                    consumption['consumption_time']=ConsumptionTime.objects.filter(
                        medication_id=consumption['medication_id']).values_list('consumption_time',flat=True)
           appointment_data['prescript_text']=prescript_text
        else:
            
            prescript_text=PrescriptionTextSerializer(
            PrescriptionsDetail.objects.filter(appointment_id=appointment['appointment_id']),many=True).data
            for prescriptions in prescript_text:
                medicines=MedicationsSerializer(Medications.objects.filter(
                prescription_id=prescriptions['id']),many=True).data
                prescriptions['medicines']=medicines
                try:
                    prescriptions['qualification']=DoctorProfiles.objects.filter(
                    user_id=prescriptions['doctor_id']).qualification
                    prescriptions['address']=DoctorProfiles.objects.filter(
                    user_id=prescriptions['doctor_id']).address
                except Exception as e:
                    prescriptions['qualification']=""
                    prescriptions['address']=""
                for consumption in medicines:
                    consumption['consumption_time']=ConsumptionTime.objects.filter(
                        medication_id=consumption['medication_id']).values_list('consumption_time',flat=True)
            appointment['prescript_text']=prescript_text
           
        for doctor in prescript_text:
            print("prescription_detail")
            try:
               doctor['doctor_name']=get_users_name(doctor['doctor_id'])
            except Exception as e:
               doctor['doctor_name']=""
    # print('323  ',appointment_data)
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': appointment_data})
    
    
def get_refund_id():
    today = datetime.datetime.today().date()
    latest_refund = Refund.objects.filter(refund_requested_date=today).order_by('-id').first()
    new_id = f'{today.year}-{today.day:02d}-{today.month:02d}-{latest_refund.pk if latest_refund else 1:04d}'
    refund_id = new_id
    print("refund id",refund_id)
    return refund_id

def create_refund(appointment_id):
    print("%@@@@@Refunf@@@@@")
    try:
        try:
            appointment=AppointmentHeader.objects.get(appointment_id=appointment_id)
            date=appointment.appointment_date
            invoice_status=Invoices.objects.get(appointment_id=appointment_id).status
        except Exception as e:
            print("refund exception",e)
            date=datetime.datetime.today().date()
            invoice_status=0
        print("date",date)
        days_since_appointment = (date-datetime.datetime.now().date() ).days
        print("days_since_appointment",days_since_appointment,invoice_status)
        if days_since_appointment < 3 and invoice_status==1:
            print("no refund")
            refund_amount = 0
        elif (days_since_appointment >= 3 and  days_since_appointment <7 ) and invoice_status == 1:
            print("3 to 7 days")
            try:
                invoice = Invoices.objects.get(appointment_id=appointment_id)
                refund_amount = invoice.total * 0.5
            except Invoices.DoesNotExist:
                refund_amount = 0
            refund, created = Refund.objects.update_or_create(
                                appointment_id=appointment_id,
                                defaults={
                                'customer_id': get_user_id(appointment_id),
                                'refund_amount': refund_amount,
                                'refund_requested_date': datetime.datetime.today().date(),
                                'appointment_date': date
                                }
                            )
            try:
                
                if Refund.objects.get(appointment_id=appointment_id).refund_id == "":
                    Refund.objects.filter(appointment_id=appointment_id).update(refund_id=get_refund_id()) 
            except Exception as e:
                print(e)       
        elif (days_since_appointment > 7 and invoice_status==1):
            print("here")
            try:
                invoice = Invoices.objects.get(appointment_id=appointment_id)
                refund_amount = invoice.total
            except Invoices.DoesNotExist:
                refund_amount = 0
            print("refund amout",refund_amount)
            refund, created = Refund.objects.update_or_create(
                                appointment_id=appointment_id,
                                defaults={
                                'customer_id': get_user_id(appointment_id),
                                'refund_amount': refund_amount,
                                'refund_requested_date': datetime.datetime.today().date(),
                                'appointment_date': date
                                }
                            )
            try:
                
                if Refund.objects.get(appointment_id=appointment_id).refund_id == "":
                    Refund.objects.filter(appointment_id=appointment_id).update(refund_id=get_refund_id()) 
            except Exception as e:
                print(e)     
    except Exception as e:
        print("******refund exception********",e)
        
@api_view(['GET'])
def doctors_list_view(request):
    try:
        doctor = DoctorProfiles.objects.filter(doctor_flag = 'senior', is_accepted = 1)
        doctors = DoctorProfileSerializer(doctor, many=True).data
        print(doctors[0]['doctor_profile_id'])      
        for doctor in doctors:
            user_id=doctor['user_id']
            try:  
                queryset_user=User.objects.get(id=user_id)
                doctor['doc_name']=queryset_user.first_name+' '+queryset_user.last_name
                doctor['user_mail']=queryset_user.email   

            except:
                pass
        return Response({
            'response_code': 200,
            'status': 'Ok',
            'data': doctors})
    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Ok',
            'data': []})


@api_view(['POST'])
def escalated_one(request):
    try:
        print(request.data)
        appointment = AppointmentHeader.objects.get(appointment_id = request.data['appointment_id'])
        appointments = AppointmentHeaderSerializer(appointment,many=False).data
        queryset_doctor = DoctorProfiles.objects.get(user_id = appointment.senior_doctor).specialization
        appointments['specialization'] = queryset_doctor
        return Response({
            'response_code': 200,
            'status': 'Ok',
            'data': appointments})
    except Exception as e:
        print(e)
        return Response({
            'response_code':400,
            'status': 'error',
            'data': str(e)
        })

@api_view(['POST'])
def appointment_completed(request):
    data = request.data
    print(data)
    try:
        appointment = AppointmentHeader.objects.filter(appointment_id = data['appointment_id']).update(appointment_status=13)
        return Response({
            'response_code': 200,
            'status': 'Ok',
            'data': data})
    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Ok',
            'data': data})


@api_view(['POST'])
def timeslots(request):
    data = request.data
    print(data)
    filter ={}
   
    doctors = SeniorDoctorAvailableTimeSLots.objects.filter(date = request.data['date'], time_slot = data['time_slot'], is_active = 0, end_time = request.data['end_time']).values_list('doctor_id',flat=True)
    print(doctors)
    matching_user_ids = DoctorLanguages.objects.filter(doctor_id__in=doctors, languages = request.data['language']).values_list('doctor_id', flat=True)
    if len(matching_user_ids) == 0:
        matching_user_ids = DoctorLanguages.objects.filter(doctor_id__in=doctors).values_list('doctor_id', flat=True)

    matching_user_ids = list(matching_user_ids)
    print(matching_user_ids)
    doctor_profiles = DoctorProfiles.objects.filter(user_id__in = matching_user_ids, gender = request.data['gender'])
    if len(doctor_profiles) == 0:
        doctor_profiles = DoctorProfiles.objects.filter(user_id__in = matching_user_ids)
    available_dr = doctor_profiles[0]
    print(available_dr)
    user = User.objects.get(id = available_dr.user_id)
    dr_details = {}
    dr_details['fullname'] = user.first_name+' '+user.last_name
    dr_details['flag'] = available_dr.doctor_flag
    dr_details['specialization'] = available_dr.specialization
    dr_details['bio'] = available_dr.doctor_bio
    try:
        location = Locations.objects.get(location = request.data['user_location'])
    except Exception as e:
        location = Locations.objects.get(location = 'USA')
    print(location)

    try:
        plan = Plans.objects.get(doctor_id = available_dr.doctor_profile_id, location_id = location.location_id)
    except Exception as e:
        print(e)
        location = Locations.objects.get(location = 'USA')
        plan = Plans.objects.get(doctor_id = available_dr.doctor_profile_id, location_id = location.location_id)
    
    dr_details['currency'] = location.currency
    if request.data['session_type'] == 'couple':
        dr_details['price'] = plan.price_for_couple
    else:
        dr_details['price'] = plan.price_for_single

    return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': dr_details})

"""View to update appointment status"""
@api_view(['POST'])
def appointment_status_update_view(request):
    appointment_id=request.data['appointment_id']
    appointment_status=request.data['appointment_status']
    print('appointtment_id: ',appointment_id,'   appointment_status: ',appointment_status)
    
    AppointmentHeader.objects.filter(pk=appointment_id).update(
        appointment_status=appointment_status)
    if appointment_status==3:
        create_refund(appointment_id)
        subject = 'Order Cancelled'
        html_message = render_to_string('order_cancellation.html', {
        'is_doctor':0,
        'email':get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        cc = "nextbighealthcare@inticure.com"
        to = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
        mail.send_mail(subject,plain_message, from_email, [to], [cc], html_message=html_message)
        try:
              sms_service.send_message(
           "Hi There, Your Appointment #%s has been cancelled Please refer email for more information"
            %(appointment_id),
                "+91" + str(CustomerProfile.objects.get(user_id=request.data['user_id']).mobile_number))
        except Exception as e:
              print(e)
              print("MESSAGE SENT ERROR")
    if appointment_status=="9":
        subject = 'Order Marked No Show'
        html_message = render_to_string('order_no_show.html', {
        'is_doctor':0,
        'email':get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        to = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
        cc = 'nextbighealthcare@inticure.com'
        mail.send_mail(subject,plain_message, from_email, [to], [cc], html_message=html_message)
        try:
              sms_service.send_message(
           "Hi There, Your Appointment #%s has been marked as no show please reschedule your appointment"
            %(appointment_id),
                "+91" + str(CustomerProfile.objects.get(user_id=request.data['user_id']).mobile_number))
        except Exception as e:
              print(e)
              print("MESSAGE SENT ERROR")
    try:
        junior_doctor_id=AppointmentHeader.objects.get(appointment_id=appointment_id).junior_doctor
    except Exception as e:
        print(e)
        junior_doctor_id=None
    # location=request.data['location_id']
    if appointment_status=="6":
        print("here")
        subject = 'Order Completed'
        encrypted_id=encryption_key.encrypt(str(appointment_id).encode())
        html_message = render_to_string('order_complete.html', {"appointment_id":encrypted_id.decode(),
        'email':get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        to = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
        print(to,"email")
        cc = "nextbighealthcare@inticure.com"
        mail.send_mail(subject,plain_message, from_email, [to], [cc], html_message=html_message)
        doctor=request.data['doctor_id']
        specialization=DoctorProfiles.objects.get(user_id=doctor).specialization
        try:
              sms_service.send_message(
            "Hi There, Your Appointment #%s has been closed! Please refer mail for more details"
            %(appointment_id),
                "+91" + str(CustomerProfile.objects.get(user_id=request.data['user_id']).mobile_number))
        except Exception as e:
              print(e)
              print("MESSAGE SENT ERROR")
        try:
            location=DoctorProfiles.objects.get(user_id=request.data['doctor_id']).location
        except Exception as e :
            print("location exception",e)
            location=1
        print("location",location)
        try:
            pricing=Plans.objects.get(specialization=specialization,location_id=location).price
            doctor_fee=pricing*75/100
            doctor_fee_junior=pricing*5/100
            inticure_fee=pricing*20/100
            expense=pricing*80/100
        except:
            pricing=0
            doctor_fee=0
            doctor_fee_junior=0
            inticure_fee=0
            expense=0
            return Response({
                'response_code': 400,
                'status': 'Ok',
                'message':'Invalid Specialization' })
        try:
            net_total=0
            print("location",type(location))
            if int(location) == 1:
                currency='inr'
            else:
                currency='usd'
            print("id in earnings ",location,currency)
            inticure_earnings=InticureEarnings.objects.get(currency=currency)
           # inticure_earnings=InticureEarnings.objects.get(id=1)
            
            if int(location) == 1 :
                updated_expense=inticure_earnings.net_expense+expense
                updated_net_income=inticure_earnings.net_income+pricing
                updated_net_profit=updated_net_income-updated_expense
                net_total=inticure_earnings.net_amount+pricing
                InticureEarnings.objects.filter(currency=currency).update(
                net_expense=updated_expense,net_income=updated_net_income,net_profit=updated_net_profit,net_amount=net_total)
            else:
                updated_expense=inticure_earnings.net_expense_usd+expense
                updated_net_income=inticure_earnings.net_income_usd+pricing
                updated_net_profit=updated_net_income-updated_expense
                net_total=inticure_earnings.net_amount_usd+pricing
                InticureEarnings.objects.filter(currency=currency).update(
                net_expense_usd=updated_expense,net_income_usd=updated_net_income,net_profit_usd=updated_net_profit,net_amount_usd=net_total)
        except Exception as e:
            
            if int(location) == 1:
                InticureEarnings.objects.create(currency='inr',
                net_expense=expense,net_income=pricing,net_profit=pricing-expense,net_amount=pricing)
            else:
                print
                try:
                    print('here')
                    InticureEarnings.objects.create(currency=currency,
                                net_expense_usd=expense,
                                net_income_usd=pricing,
                                net_profit_usd=pricing - expense,
                                net_amount_usd=pricing)
                    print("earnings")
                except Exception as e :
                    print(e)
                    print("earnigs exception",e)
        try:
           doctor_id=User.objects.get(id=doctor)
           doctor_name=doctor_id.first_name+doctor_id.last_name
        except:
           doctor_name=""
           
        try:
            total=TotalPayouts.objects.get(doctor_id=doctor)
            total_payouts=doctor_fee+total.total_payouts
            TotalPayouts.objects.filter(doctor_id=doctor).update(
            doctor_id=doctor,total_payouts=total_payouts)
            print("totalpayouts",total,total_payouts)
            try:
             print("juniort try block",junior_doctor_id)
             if junior_doctor_id:
               total=TotalPayouts.objects.get(doctor_id=junior_doctor_id)
               total_payouts=doctor_fee_junior+total.total_payouts
               TotalPayouts.objects.filter(doctor_id=junior_doctor_id).update(
                 doctor_id=doctor,total_payouts=total_payouts)
            except Exception as e:
                print(e,"junior doctor exception") 
        except:
            print("except block")
            total_payouts=doctor_fee
            TotalPayouts.objects.create(
            doctor_id=doctor,total_payouts=total_payouts)
            print("total payoout for jr doc",total_payouts,"created")
            if junior_doctor_id:
              total_payouts=doctor_fee_junior
              TotalPayouts.objects.create(doctor_id=doctor,total_payouts=total_payouts)

        Payouts.objects.create(
            doctor_id=doctor,
            payout_amount=doctor_fee,
            inticure_fee=inticure_fee,
            base_amount=pricing,
            appointment_id=appointment_id)
        
        if junior_doctor_id:
            Payouts.objects.create(
               doctor_id=junior_doctor_id,
               payout_amount=doctor_fee_junior,
               appointment_id=appointment_id)
        
        AppointmentHeader.objects.filter(appointment_id=appointment_id).update(appointment_status=appointment_status)
        Invoices.objects.filter(appointment_id=appointment_id).update(doctor_id=doctor,doctor_name=doctor_name)
        
        
    """Jr Doc Mapping Deletion when transfering an order"""
    if request.data['appointment_status']==10:
        JrDoctorEngagement.objects.filter(appointment_id=appointment_id).delete()
        AppointmentHeader.objects.filter(appointment_id=appointment_id).update(junior_doctor=None)
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Appointment Status Updated"
    })

def get_users_name(user_id):
    try:
        print(user_id)
        doc = User.objects.get(id=user_id)
        users_name = doc.first_name + doc.last_name
    except Exception as e:
        # print("except", e)
        users_name = ""
    return users_name

def get_users_email(user_id):
    try:
        mail = User.objects.get(id=user_id)
        users_mail = mail.email
    except Exception as e:
        print("except", e)
        users_mail = ""
    return users_mail

def get_doc_flag(appointment_id):
    try:
        appointmet_qs=AppointmentHeaderSerializer(
            AppointmentHeader.objects.get(appointment_id=appointment_id)).data
        if appointmet_qs['senior_doctor']:
            doctor_id=appointmet_qs['senior_doctor']
            flag="senior"
        else:
            doctor_id=appointmet_qs['junior_doctor']
            flag="junior"
    except Exception as e:
        print(e)
        flag=0
        doctor_id=None
    print("flag",flag,"doctor",doctor_id)
    return flag,doctor_id

"""Rescheduling an appointment"""
@api_view(['POST'])
def appointment_schedule_view_copy(request):
    doctor_id=request.data['doctor_id']
    doc_flag=request.data['doctor_flag']
    rescheduled_date=request.data['appointment_date']
    appointment_id=request.data['appointment_id']
    flag=0
    time_slot=request.data['appointment_time']

    """ get doctor flag is doc_flag is 0"""
    if doc_flag == 0:
        doc_flag=get_doc_flag(doctor_id)
    if flag==0:
        print(doc_flag,"doctor_flag")
        if doc_flag == 1 or doc_flag=="senior" :
            print("here")
            #senior doctor
            RescheduleHistory.objects.create(
            appointment_id=appointment_id,
            user_id=request.data['user_id'],
            sr_rescheduled_date=rescheduled_date,
            sr_rescheduled_time=time_slot,
            #time_slot=time_slot,
            doctor_id=doctor_id )
            print("----------")
        else:
            print( "create else")
            RescheduleHistory.objects.create(
            appointment_id=appointment_id,
            user_id=request.data['user_id'],
            rescheduled_date=rescheduled_date,
            time_slot=time_slot,
            doctor_id=doctor_id )

        try:

            appointment_id_schedule=AppointmentReshedule.objects.get(appointment_id=appointment_id)
            count=appointment_id_schedule.reschedule_count
            print(appointment_id_schedule.reschedule_count)
        except Exception as e:
            # print("Exception",e)
            appointment_id_schedule=None
            count=0
        if appointment_id_schedule:
            count=count+1
            if doc_flag == 1 or doc_flag=="senior" :
                print("flag is 1 ")
                AppointmentReshedule.objects.filter(appointment_id=appointment_id).update(
                user_id=request.data['user_id'],appointment_id=appointment_id,
                sr_rescheduled_date=rescheduled_date,sr_rescheduled_time=time_slot,reschedule_count=count)
                SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=rescheduled_date,time_slot=time_slot).update(is_active=1)
            else:
                print("jr flag")
                AppointmentReshedule.objects.filter(appointment_id=appointment_id).update(
                user_id=request.data['user_id'],appointment_id=appointment_id,
                rescheduled_date=rescheduled_date,time_slot=time_slot,reschedule_count=count)
            AppointmentHeader.objects.filter(
        appointment_id=appointment_id).update(appointment_status=request.data['appointment_status'])
        else:
            count+=1
            if doc_flag == 1 or doc_flag=="senior":
                print("sr flag")
                AppointmentReshedule.objects.create(
                appointment_id=appointment_id,user_id=request.data['user_id'],
                sr_rescheduled_date=rescheduled_date,time_slot=time_slot,reschedule_count=count)
                SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=rescheduled_date,time_slot=time_slot).update(is_active=1)
            else:
                print("jr flag")
                AppointmentReshedule.objects.create(
                appointment_id=appointment_id,user_id=request.data['user_id'],
                rescheduled_date=rescheduled_date,time_slot=time_slot,reschedule_count=count)
        AppointmentHeader.objects.filter(
        appointment_id=appointment_id).update(appointment_status=request.data['appointment_status'])
        try:
            specialization=DoctorProfiles.objects.get(user_id=doctor_id).specialization
            doc_id=DoctorProfiles.objects.get(user_id=doctor_id).doctor_profile_id
        except:
            doc_id = None
            specialization=None
        doctor_email = get_user_mail(doctor_id)
        user_email = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
        start_time, end_time = get_appointment_time(request.data['appointment_time'],rescheduled_date,specialization,doc_flag,doctor_id=doc_id)
        meet_link = generate_google_meet("Inticure,Doctor Appointment", "",
                                         [{"email": user_email}, {"email": doctor_email}], start_time,
                                         end_time)
        print( "Meeting link="+meet_link)
        if doc_flag=='senior':
            AppointmentHeader.objects.filter(appointment_id=appointment_id).update(senior_meeting_link=meet_link)
        else:
            AppointmentHeader.objects.filter(appointment_id=appointment_id).update(meeting_link=meet_link)
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Appointment Re-Scheduled"
    })
    return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Time Slot not Available"
    })

"""Adding required Observartions"""
@api_view(['POST'])
def observations_view(request):
        AppointmentHeader.objects.filter(appointment_id=request.data['appointment_id']).update(is_free=0)
        appointment_id=request.data['appointment_id']
        observations=request.data['observations']
        doctor_id=request.data['doctor_id']
        data={
        "appointment_id":appointment_id,
        "observe":observations,
        "doctor_id":doctor_id }

        serializer = ObservationsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
        #    AppointmentHeader.objects.filter(appointment_id=request.data['appointment_id']).update(appointment_status=request.data['appointment_status'])
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Observations added Booking Closed"
        })

"""Uploading Prescription Files"""
@api_view(['POST'])
def prescriptions_view(request):
    print("FILE UPLOADINGG HIT API")
    appointment_id=request.data['appointment_id']
    prescription = request.data['prescription']
    file_name=request.data['file_name']
    file_size=request.data['file_size']
    data={
        "appointment_id":appointment_id,
        "prescription":prescription,
        "prescript_file_name":file_name,
        "prescript_file_size":file_size
    }
    serializer = PrescriptionSerializer(data=data)
    if serializer.is_valid():
            print("FILE UPLOADINGG>>>>> SUCCESS")
            serializer.save()
    # AppointmentHeader.objects.filter(appointment_id=request.data['appointment_id']).update(appointment_status=request.data['appointment_status'])
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Prescriptions added Booking Closed"
        })

"""Adding Prescriptions"""
@api_view(['POST'])
def prescriptions_text_view(request):
        appointment_id=request.data['appointment_id']
        prescriptions_text=request.data['prescriptions_text']
        doctor_id=request.data['doctor_id']
        tests_to_be_done=request.data['tests_to_be_done']
        data={
        "appointment_id":appointment_id,
        "prescriptions_text":prescriptions_text,
        "doctor_id":doctor_id,
        "tests_to_be_done":tests_to_be_done
    }
        serializer=PrescriptionTextSerializer(data=data)
        #  print(serializer.id)
        if serializer.is_valid():
            instance=serializer.save()
            print(instance.id)
            for datas in request.data['medications']:
                 data_medication={
                "prescription_id":instance.id,
                "medication":datas['medicine'],
                "duration_number":datas['duration_number'],
                "duration":datas['duration'],
                "side_effects":datas['side_effects'],
                "consumption_detail":datas['consumption_detail'],
                "can_substitute":datas["can_substitute"]
                }
                 medicine_serializer=MedicationsSerializer(data=data_medication)
                 print(medicine_serializer.is_valid(),"yo",medicine_serializer.errors)
                 if medicine_serializer.is_valid():
                     medicine_instance=medicine_serializer.save()
                     print(medicine_instance.medication_id)
                     for options in datas['consumption_time']:
                        ConsumptionTime.objects.create(prescription_id=instance.id,
                        medication_id=medicine_instance.medication_id,consumption_time=options)
            subject = 'Your Appointment Prescriptions'
            html_message = render_to_string('prescriptions.html', {"doctor_flag":0,
                'email':get_user_mail(AppointmentHeader.objects.get(
            appointment_id=appointment_id).user_id)})
            plain_message = strip_tags(html_message)
            from_email = 'wecare@inticure.com'
            to =  get_user_mail(AppointmentHeader.objects.get(
                appointment_id=appointment_id).user_id)
            cc = 'nextbighealthcare@inticure.com'

            mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)
        #AppointmentHeader.objects.filter(appointment_id=request.data['appointment_id']).update(appointment_status=request.data['appointment_status'])
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Prescriptions added Booking Closed"
        })
"""Analysis Info Text Field"""
@api_view(['POST'])
def analysis_info_view(request):
    print("analysis_info hit")
    if "operation_flag" in request.data and request.data['operation_flag']!="":
         print("file_p=ath")
         appointment_id=request.data['appointment_id']
         analysis_info_path=request.data['analysis_path']
         doctor_id=request.data['doctor_id']
         AnalysisInfo.objects.create(appointment_id=appointment_id,analysis_info_path=analysis_info_path,
           doctor_id=doctor_id,file_name=request.data['file_name'],file_size=request.data['file_size'])
         return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Analysis File Info added"
        })
    else:
        print("else-analysis_info")
        appointment_id=request.data['appointment_id']
        analysis_info_text=request.data['analysis_text']
        doctor_id=request.data['doctor_id']
        # data={
        # "appointment_id":appointment_id,
        # "analysis_info_text":analysis_info_text,
        # "doctor_id":doctor_id
        #   }

        AnalysisInfo.objects.create(appointment_id=appointment_id,analysis_info_text=analysis_info_text,
           doctor_id=doctor_id)
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Analysis Informations Added"
        })
"""VIEW SETS"""
class PrescriptionsTextViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionsDetail.objects.all()
    serializer_class = PrescriptionTextSerializer
    def update(self,request,*args,**kwargs):
        PrescriptionsDetail.objects.filter(pk=self.kwargs['pk']).update(
        prescriptions_text=request.data['prescriptions_text'],
        tests_to_be_done=request.data['tests_to_be_done'])
        for datas in request.data['medications']:
            if "medication_id" in datas and datas['medication_id']!="":
                  Medications.objects.filter(medication_id=datas['medication_id']).update(
                  medication=datas['medicine'],
                  duration_number=datas['duration_number'],
                  duration=datas['duration'],
                  side_effects=datas['side_effects'],
                  consumption_detail=datas['consumption_detail'],can_substitute=datas['can_substitute'])
                  for options in datas['consumption_time']:
                    ConsumptionTime.objects.filter(
                        medication_id=datas['medication_id']).update(consumption_time=options)
            else:
                  for datas in request.data['medications']:
                    medicine_id=Medications.objects.create(
                    prescription_id=self.kwargs['pk'],
                    medication=datas['medicine'],
                    duration_number=datas['duration_number'],
                    duration=datas['duration'],
                    side_effects=datas['side_effects'],
                    consumption_detail=datas['consumption_detail'],can_substitute=datas['can_substitute'])
                    for options in datas['consumption_time']:
                        ConsumptionTime.objects.create(prescription_id=self.kwargs['pk'],
                        medication_id=medicine_id.medication_id,consumption_time=options)

        return Response(
            {'response_code': 200,
             'status': 'Ok',
             'message': 'Prescriptions Updated'},
            status=status.HTTP_200_OK
        )
    def destroy(self, request, *args, **kwargs):
        PrescriptionsDetail.objects.filter(pk=self.kwargs['pk']).delete()
        Medications.objects.filter(prescription_id=self.kwargs['pk']).delete()
        ConsumptionTime.objects.filter(prescription_id=self.kwargs['pk']).delete()
        return Response(
            {'response_code': 200,
             'status': 'Ok',
             'message': 'Prescriptions Deleted'},
            status=status.HTTP_200_OK
        )
class ObservationsViewSet(viewsets.ModelViewSet):
    queryset=Obeservations.objects.all()
    serializer_class=ObservationsSerializer
class CommonFileUploaderViewset(viewsets.ModelViewSet):
    # print("FILE UPLOADINGGG>>>>")
    queryset=CommonFileUploader.objects.all()
    serializer_class=CommonFileUploaderSerializer
    # def create(self, request, *args, **kwargs):
    #     print("FILE UPLOADINGG>>>>>")
    #     serializer = self.serializer_class(data=request.data)
    #     if serializer.is_valid(raise_exception=True):
    #         # if serializer.is_valid():
    #         print("FILE UPLOADINGG>>>>>")
    #         se = serializer.save()
    #         return Response({
    #             'response_code': 200,
    #             'status': 'Ok',
    #             'message': 'File Uploaded',
    #             "data":serializer.data},
    #             status=status.HTTP_201_CREATED
    #         )

    #     return Response({
    #         'response_code': 400,
    #         'status': 'Bad request',
    #         'message': 'File could not be uploaded with received data.'
    #     }, status=status.HTTP_400_BAD_REQUEST)
# class SpecializationViewset(viewsets.ModelViewSet):
#     queryset=Specialization.objects.all()
#     serializer_class=SpecializationSerializer
"""Specialization Viewset"""
class SpecializationViewset(viewsets.ModelViewSet):
   queryset=DoctorSpecializations.objects.all()
   serializer_class=SpecializationSerializer
   print(serializer_class)
   def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # if serializer.is_valid():
            se = serializer.save()
            return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': 'Specialization created'},
                status=status.HTTP_201_CREATED
            )

        return Response({
            'response_code': 400,
            'status': 'Bad request',
            'message': 'Specialization could not be created with received data.'
        }, status=status.HTTP_400_BAD_REQUEST)

   def list(self, request, *args, **kwargs):
        queryset=DoctorSpecializations.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Specialization list',
                 'data':serializer.data},
                  status=status.HTTP_201_CREATED)
   def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            specialization = DoctorSpecializations.objects.filter(
                pk=self.kwargs['pk']).update(**serializer.validated_data)
            return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Specialization Updated'},
                status=status.HTTP_201_CREATED
            )

   def destroy(self, request, *args, **kwargs):
        # serializer = self.serializer_class(data=request.data)
        # if serializer.is_valid(raise_exception=True):
        specialization = DoctorSpecializations.objects.filter(pk=self.kwargs['pk'])
        specialization.delete()
        return Response(
            {'response_code': 200,
             'status': 'Ok',
             'message': 'Specialization Deleted'},
            status=status.HTTP_201_CREATED
        )

def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end



"""Doctor Filters required for escalate new and followup orders"""
@api_view(['POST'])
def doctor_specialization_view(request):
        print("doctor_select")
        filter={}
        doctor_id_list=[]
        if "specialization" in request.data and request.data['specialization'] != "":
          filter['specialization']=request.data['specialization']

        if "language_pref" in request.data and request.data['language_pref'] != "":
          filter['user_id__in']=DoctorLanguages.objects.filter(languages=request.data['language_pref']).values_list('doctor_id',flat=True)

        if "gender_pref" in request.data and request.data['gender_pref'] != "":
          filter['gender']=request.data['gender_pref']

        if "doctor" in request.data and request.data['doctor'] != "":
            filter['doctor_flag']=request.data['doctor']
        doc_id_list= custom_filter(DoctorProfiles, filter).values_list("user_id",flat=True)
        print(doc_id_list)
        if "appointment_date" in request.data and request.data['appointment_date'] !="":
            appointment_date=request.data['appointment_date']
            appointment_date_=datetime.datetime.strptime(appointment_date,"%Y-%m-%d")
            doctor_id_list=DoctorAvailableDates.objects.filter(date=appointment_date
            ).values_list("doctor_id",flat=True)
            print(doc_id_list,"DOCTOR_ID_LIST")
            filter['user_id__in']=doctor_id_list
        # if "appointment_time" in request.data and request.data['appointment_time'] !="":
            appointment_time=request.data['appointment_time']
            # appointment_date=request.data['appointment_date']
            weekday=appointment_date_.strftime("%A")
            print("weekday",weekday)
            try:
                time_slot_from=DoctorAvailableTimeslots.objects.filter(
                    doctor_id__in=doctor_id_list,day=weekday).values_list("time_slot_from",flat=True)
                time_slot_to=DoctorAvailableTimeslots.objects.filter(
                    doctor_id__in=doctor_id_list,day=weekday).values_list("time_slot_to",flat=True)
                print(weekday,time_slot_from,time_slot_to)
                time_from=Timeslots.objects.get(id=min(time_slot_from))
                time_to=Timeslots.objects.get(id=max(time_slot_to))
                start=datetime.datetime.strptime(time_from.time_slots.split('-')[0].strip(), '%I%p').time()
                end=datetime.datetime.strptime(time_to.time_slots.split('-')[1].strip(), '%I%p').time()
                print(time_in_range(start, end,
                datetime.datetime.strptime(appointment_time.split('-')[1].strip(), '%I:%M%p').time()))
                if time_in_range(start, end,
                datetime.datetime.strptime(appointment_time.split('-')[1].strip(), '%I:%M%p').time())==True:
                    doctor_id_list_time=DoctorAvailableTimeslots.objects.filter(
                        doctor_id__in=doctor_id_list,day=weekday).values_list("doctor_id",flat=True)
                filter['user_id__in']=doctor_id_list_time

            except Exception as e:
                print(e)
                return Response({
                    'response_code': 400,
                    'status': 'Ok',
                    'message': "No Available Doctors",
        })
        queryset = custom_filter(DoctorProfiles, filter)
        specialization=DoctorProfileSerializer(queryset,many=True).data
        for user in specialization:
            user_id=user['user_id']
            print(user_id)
            # if "appointment_date" in request.data and request.data['appointment_date'] !="":
            #     doc_flag=request.data['doctor_flag']
            #     appointment_date=request.data['appointment_date']
            #     try:
            #         time_slot_query=Timeslots.objects.get(
            #         id=request.data['appointment_time'])
            #         time_slot=time_slot_query.time_slots
            #         print(time_slot)
            #     except Exception as e:
            #         print("except",e)
            #         return Response({
            #         'response_code': 400,
            #             'status': 'Ok',
            #               'message': "Invalid Time Slot"})
            #     if doc_flag==1:
            #         time_slot_querysets=SrDoctorEngagement.objects.filter(user_id=user_id,
            #         time_slot=time_slot,date=appointment_date)
            #     if time_slot_querysets.exists():
            #         user=user_id
            #     if doc_flag==2:
            #         time_slot_queryset=JrDoctorEngagement.objects.filter(user_id=user_id,
            #         time_slot=time_slot,date=appointment_date)
            #     if time_slot_queryset.exists():
            #         user=user_id
            try:
              queryset_user=User.objects.get(id=user_id)
              print(queryset_user)
              user['user_fname']=queryset_user.first_name
              user['user_lname']=queryset_user.last_name
              user['user_mail']=queryset_user.email
            except:
               user['user_fname']=""
               user['user_lname']=""
               user['user_mail']=""

        return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Available Doctors",
        'doctor':specialization,
        })


def get_user_mail(user_id):
    try:
        email = User.objects.get(pk=user_id).email
    except:
        email = ""
    return email

def get_first_name(user_id):
    try:
        first_name = User.objects.get(pk=user_id).first_name
    except:
        first_name = ""
    return first_name

def get_doctor_specialization(doctor_id):
    try:
        specialization=DoctorProfiles.objects.get(user_id=doctor_id).specialization
    except:
        specialization=""
    return specialization

def get_slot_time(slots,date= None,doctor_flag= None):
    try:
        # time_slots = Timeslots.objects.get(id=slot_id)
      if doctor_flag=="junior":
        start_time = str(date)+"T"+str(datetime.datetime.strptime(slots.split('-')[0].strip(), '%I%p').time())
        end_time = str(date)+"T"+str(datetime.datetime.strptime(slots.split('-')[1].strip(), '%I%p').time())
        return  start_time,end_time
      else:
        start_time = str(date)+"T"+str(datetime.datetime.strptime(slots.split('-')[0].strip(), '%I:%M%p').time())
        end_time = str(date)+"T"+str(datetime.datetime.strptime(slots.split('-')[1].strip(), '%I:%M%p').time())
        return  start_time,end_time
    except Exception as e:
        return None,None

@api_view(['POST'])
def escalate_appointment_view(request):
    print('1148 ', request.data)
    doctor_id=assign_senior_doctor(request)

    if doctor_id == 0:
        return Response({
            'response_code': 404,
            'status': 'Failed'},
            status=status.HTTP_404_NOT_FOUND
        )
    appointment_status=request.data['appointment_status']
    
    appointment_id=request.data['appointment_id']
    appointment_date=request.data['appointment_date']
    time_slot=request.data['time_slot']
    specialization = request.data['specialization']
    session_type = request.data['session_type']
    if '-' in request.data['time_slot']:
        start_time = request.data['time_slot'].split(' - ')[0]
    else:
        start_time = request.data['time_slot']

    appoint = AppointmentHeader.objects.get(appointment_id=appointment_id)
    JuniorDoctorSlots.objects.filter(doctor_id = appoint.junior_doctor,date = appoint.appointment_date, time_slot = appoint.appointment_time_slot_id).update(is_active = 0)

    AppointmentHeader.objects.filter(appointment_id=appointment_id).update(
        appointment_status=appointment_status,
        escalated_time_slot=start_time,
        escalated_date=appointment_date,senior_doctor=doctor_id, session_type = session_type, payment_status = False)
    
    SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id = doctor_id, date = appointment_date, time_slot = start_time).update(is_active = 1)
    
    subject = 'Payment for consultation'
    html_message = render_to_string('payment_mail.html', {'appointment_id': appointment_id,
        "doctor_name":get_users_name(doctor_id),"name":get_users_name(request.data['user_id']),
        "specialization":get_doctor_specialization(doctor_id),'date':appointment_date,
        "time":time_slot})
    
    user_mail_id=get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
    # try:
    #     sms_service.send_message(
    #     "Hi There, Your Appointment #%s has been escalated on %s,%s Please refer mail for more details"
    #     %(appointment_id,appointment_date,time_slot),
    #         "+91" + str(CustomerProfile.objects.get(user_id=AppointmentHeader.objects.get(
    #             appointment_id=appointment_id).user_id).mobile_number))
    # except Exception as e:
    #     print(e)
    #     print("MESSAGE SENT ERROR")

    plain_message = strip_tags(html_message)
    from_email = 'Inticure <hello@inticure.com>'
    to = user_mail_id
    cc = 'nextbighealthcare@inticure.com'
    mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)

    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Order Escalated",
        "doctor":get_users_name(doctor_id)
        })

# @api_view(['POST'])
# def escalate_appointment_list_view(request):
#     try:
#         print('Request Data:', request.data)

#         escalated_data = EscalatedAppointment.objects.filter(
#             user_id=request.data['user_id'],
#             appointment_status=2,
#             status=False,
#             appointment_date__gt=datetime.datetime.today().date()
#         )

#         serialized_data = EscalatedAppointmentSerializer(escalated_data, many=True).data

#         return Response({
#             'response_code': 200,
#             'status': 'Ok',
#             'message': "Order Escalated",
#             'escalated_list': serialized_data
#         }, status=status.HTTP_200_OK)

#     except Exception as e:
#         print('Error:', str(e))
        
#         return Response({
#             'response_code': 500,
#             'status': 'Error',
#             'message': "An error occurred while processing your request."
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# @api_view(['POST'])
# def escalated_one_view(request):
#     print('1238',request.data)
#     appointment_data = AppointmentHeader.objects.get(
#             appointment_id = request.data['appointment_id']
#         )
#     escalated_data = EscalatedAppointment.objects.get(
#             appointment_id = request.data['appointment_id']
#         )
#     print('asdfasdf')
#     serialized_data = AppointmentHeaderSerializer(appointment_data, many=False).data
#     serialized_data2 = EscalatedAppointmentSerializer(escalated_data, many=False).data
#     print(serialized_data)
#     print(serialized_data2)
#     return Response({
#             'response_code': 200,
#             'status': 'Ok',
#             'message': "Order Escalated",
#             'escalated_list': serialized_data2,
#             'appointment_list':serialized_data
#         }, status=status.HTTP_200_OK)

"""Order escalation api"""
@api_view(['POST'])
def order_escalate_view(request):
    #doctor=assign_senior_doctor(request)
    #print(doctor,"doc")
    print('1149 ',request.data)
    #doctor_id=request.data['doctor_id']
    doctor_id=assign_senior_doctor(request)
    # print("doctor_id",doctor_id)
    if doctor_id == 0:
        return Response({
            'response_code': 404,
            'status': 'Failed'},
            status=status.HTTP_404_NOT_FOUND
        )

    appointment_status=request.data['appointment_status']
    appointment_id=request.data['appointment_id']
    appointment_date=request.data['appointment_date']
    time_slot=request.data['time_slot']
   
    AppointmentHeader.objects.filter(appointment_id=appointment_id).update(
        appointment_status=appointment_status,
        escalated_time_slot=request.data['time_slot'],
        escalated_date=appointment_date,senior_doctor=doctor_id)
    if "gender_pref" in request.data and request.data['gender_pref']!="":
        gender=request.data['gender_pref']

    else:
        try:
            appointment_header = AppointmentHeader.objects.get(appointment_id=appointment_id)
            gender= appointment_header.gender_pref
        except:
            gender = ''
    if "language_pref" in request.data and request.data['language_pref']!="":
        language=request.data['language_pref']
    else:
        try:
            appointment_data = AppointmentHeader.objects.get(appointment_id=appointment_id)
            language = appointment_data.language_pref
        except:
            language = 'English'
    try:
            user=AppointmentHeader.objects.get(appointment_id=appointment_id)
            user_id=user.user_id
    except:
            user_id=""
    DoctorMapping.objects.create(appointment_id=appointment_id,mapped_doctor=doctor_id,doctor_flag="senior")
    if  SrDoctorEngagement.objects.filter(appointment_id=appointment_id).count() == 0:
        print("create engagement")
        SrDoctorEngagement.objects.create(
            appointment_id=appointment_id,date=appointment_date,user_id=doctor_id,time_slot=time_slot )
    else:
        print("update engagement")
        SrDoctorEngagement.objects.filter(appointment_id=appointment_id).update(
        appointment_id=appointment_id,date=appointment_date,user_id=doctor_id,time_slot=time_slot)
    print(" here")

    try:
        specialization=DoctorProfiles.objects.get(user_id=doctor_id).specialization
    except:
        specialization=None

    SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=appointment_date,time_slot=request.data['time_slot']).update(is_active=1)
    user_mail_id=get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
    doctor_email = get_user_mail(doctor_id)
    user_email = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
    doc_id = DoctorProfiles.objects.get(user_id = doctor_id).doctor_profile_id
    start_time, end_time = get_appointment_time(request.data['time_slot'],appointment_date,specialization,doctor_flag='senior',doctor_id=doc_id)
    meet_link = generate_google_meet("Inticure,Doctor Appointment", "",
                                         [{"email": user_email}, {"email": doctor_email}], start_time,
                                         end_time)
    AppointmentHeader.objects.filter(appointment_id=appointment_id).update(senior_meeting_link=meet_link,gender_pref=gender,language_pref=language)
    # try:
    #         sms_service.send_message(
    #         "Hi There, Your Appointment #%s has been confirmed on %s,%s Please refer mail for more details"
    #         %(appointment_id,appointment_date,time_slot),
    #             "+91" + str(CustomerProfile.objects.get(user_id=AppointmentHeader.objects.get(
    #                 appointment_id=appointment_id).user_id).mobile_number))
    # except Exception as e:
    #           print(e)
    #           print("MESSAGE SENT ERROR")

    subject = 'Yes! Your consultation is confirmed'
    html_message = render_to_string('order_escalate.html', {'doctor_name': get_users_name(doctor_id),
    'date':appointment_date,'time':time_slot,"specialization":get_doctor_specialization(doctor_id),
    'name':get_users_name(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id),
    "meet_link":meet_link })

    plain_message = strip_tags(html_message)
    from_email = 'wecare@inticure.com'
    to = user_mail_id
    cc = "nextbighealthcare@inticure.com"
    mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)

    subject = 'Appointment confirmed'
    html_message = render_to_string('order_confirmation_doctor.html', {'doctor_name': get_users_name(doctor_id),
    'date':appointment_date,'time':time_slot,"doctor_flag":2,"meet_link":meet_link,
    'name':get_users_name(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id) })

    plain_message = strip_tags(html_message)
    from_email = 'wecare@inticure.com'
    to = doctor_email
    cc = "nextbighealthcare@inticure.com"
    mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Order Escalated",
        "doctor":get_users_name(doctor_id)
        })

"""Accept Order API"""
@api_view(['POST'])
def order_accept_view(request):
    doctor_id=request.data['doctor_id']
    appointment_status=request.data['appointment_status']
    appointment_id=request.data['appointment_id']
    try:
        date_time=AppointmentHeader.objects.get(appointment_id=appointment_id)
        date=date_time.appointment_date
        time_slot_id=Timeslots.objects.get(id=date_time.appointment_time_slot_id)
        time_slot=time_slot_id.time_slots
    except Exception as e:
        print('except',e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message': "Invalid Appointment ID"
        })
    # time_slot_queryset=JrDoctorEngagement.objects.filter(user_id=doctor_id,
    #     time_slot=time_slot,date=date)
    # if time_slot_queryset.exists():
    #     return Response({
    #     'response_code': 400,
    #     'status': 'Ok',
    #     'message': "Time Slot not Available"})
    # else:
    AppointmentHeader.objects.filter(appointment_id=appointment_id).update(
        appointment_status=appointment_status)
    DoctorMapping.objects.create(mapped_doctor=doctor_id,appointment_id=appointment_id)
    JrDoctorEngagement.objects.create(
        appointment_id=appointment_id,
        date=date,
        user_id=doctor_id,
        time_slot=time_slot
        )
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Order Accepted"})

"""Senior Doctor Transfer Appointment API"""
@api_view(['POST'])
def senior_doctor_transfer_view(request):
    print("senior_doc_trnsfr")
    new_doctor_id=assign_senior_doctor(request)
    if new_doctor_id == 0:
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    doctor_id=request.data['doctor_id']
    appointment_status=request.data['appointment_status']
    appointment_id=request.data['appointment_id']
    appointment_date=request.data['appointment_date']
    data={
        "new_doctor":new_doctor_id,
        "old_doctor":doctor_id,
        "appointment_id":appointment_id }
    # try:
    #    time_slot_query=Timeslots.objects.get(
    #     id=request.data['time_slot'])
    #    time_slot=time_slot_query.time_slots
    # except Exception as e:
    #     print("except",e)
    #     return Response({
    #     'response_code': 400,
    #     'status': 'Ok',
    #     'message': "Invalid Time Slot"})
    # time_slot_queryset=SrDoctorEngagement.objects.filter(user_id=doctor_id,
    #     time_slot=time_slot,date=appointment_date)
    # if time_slot_queryset.exists():
    #     return Response({
    #     'response_code': 400,
    #     'status': 'Ok',
    #     'message': "Time Slot not Available"})
    # else:
    AppointmentHeader.objects.filter(appointment_id=appointment_id).update(
        appointment_status=appointment_status,
        escalated_time_slot=request.data['time_slot'],
        escalated_date=appointment_date,senior_doctor=new_doctor_id)
    DoctorMapping.objects.create(appointment_id=appointment_id,mapped_doctor=new_doctor_id,doctor_flag="senior")
    DoctorMapping.objects.create(appointment_id=appointment_id,mapped_doctor=doctor_id,doctor_flag="senior")
        # SrDoctorEngagement.objects.filter(appointment_id=appointment_id).update_or_create(
        # appointment_id=appointment_id,
        # date=appointment_date,
        # user_id=new_doctor_id,
        # time_slot=time_slot)
    serializer = SeniorTransferLogSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
    try:
        specialization=DoctorProfiles.objects.get(user_id=new_doctor_id).specialization
    except:
        specialization=None

    doctor_email = get_user_mail(new_doctor_id)
    user_email = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
    doc_id = DoctorProfiles.objects.get(user_id = new_doctor_id).doctor_profile_id
    start_time, end_time = get_appointment_time(request.data['time_slot'],appointment_date,specialization,doctor_flag='senior',doctor_id=doc_id)
    meet_link = generate_google_meet("Inticure,Doctor Appointment", "",
                                         [{"email": user_email}, {"email": doctor_email}], start_time,
                                         end_time)
    AppointmentHeader.objects.filter(appointment_id=appointment_id).update(senior_meeting_link=meet_link)
    # try:
    #         sms_service.send_message(
    #         "Hi There, Your Appointment #%s has been transfered to another date %s,%s Please refer mail for more details"
    #         %(appointment_id,appointment_date,start_time),
    #             "+91" + str(CustomerProfile.objects.get(user_id=AppointmentHeader.objects.get(
    #                 appointment_id=appointment_id).user_id).mobile_number))
    # except Exception as e:
    #           print(e)
    #           print("MESSAGE SENT ERROR")
    subject = 'Order Transfer Update'
    html_message = render_to_string('order_transfer.html', {'appointment_id': appointment_id,
    'doctor':get_users_name(new_doctor_id),"doctor_flag":0,
    'email':get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id),
    "meet_link":meet_link})
    plain_message = strip_tags(html_message)
    from_email = 'wecare@inticure.com'
    cc = 'nextbighealthcare@inticure.com'
    to =  get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)

    mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)

    subject = 'Appointment Confirmed'
    html_message = render_to_string('order_confirmation_doctor.html', {'date': appointment_date,"doctor_flag":2,
    'name':get_users_name(new_doctor_id),"time":request.data['time_slot'],"meet_link":meet_link})
    plain_message = strip_tags(html_message)
    from_email = 'wecare@inticure.com'
    to =  get_user_mail(new_doctor_id)

    mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)

    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Order Transfered"
        })

"""Doctor Earnings API"""
@api_view(['POST'])
def doctor_earnings_view(request):
    print('doc_earn')
    filter={}
    try:
        filter['payout_status']=1
        filter['doctor_id']=request.data['doctor_id']
        queryset = custom_filter(Payouts, filter)
        earnings=PayoutsSerializer(queryset,many=True).data
        print(earnings)
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': earnings
    })
    except Exception as e:
        print("payout_exception",e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Earnings List None"
    })

"""Appointment Count api for Doctor Dashboard"""
@api_view(['POST'])
def dashboard_view(request):
    doctor_id=request.data['doctor_id']
    doctor_flag=request.data['doctor_flag']
    appointment_count=0
    followup_count=0
    completed_count=0
    escalated_count=0
    dash_data={}
    if doctor_flag==2:
        appointment_count=AppointmentHeader.objects.filter(appointment_status__in=[0,10],user_id = request.data['doctor_id'], payment_status=1).count()
        followup_count=AppointmentHeader.objects.filter(appointment_status=8,junior_doctor=doctor_id).count()
        completed_count=AppointmentHeader.objects.filter(appointment_status=6,junior_doctor=doctor_id).count()
        dash_data={
        "appointment_count":appointment_count,
        "followup_count":followup_count,
        "completed_count":completed_count}

    if doctor_flag==1:
        followup_count=AppointmentHeader.objects.filter(appointment_status=8,senior_doctor=doctor_id).count()
        completed_count=AppointmentHeader.objects.filter(appointment_status=6,senior_doctor=doctor_id).count()
        escalated_count=AppointmentHeader.objects.filter(appointment_status__in=[2,11,12] ,senior_doctor=doctor_id,payment_status=True).count()
        dash_data={
        "appointment_count":escalated_count,
        "followup_count":followup_count,
        "completed_count":completed_count}

    return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': dash_data
    })

"""Profile details of Doctors"""
@api_view(['POST'])
def doctor_profile_view(request):
    print(request.data)
    doctor_id=request.data['doctor_id']
    try:
        doctor=DoctorProfiles.objects.get(user_id=doctor_id)
        user=User.objects.get(id=doctor_id)
        user_profile=UserSerializer(user).data
        doctor_profile=DoctorProfileSerializer(doctor).data
        location=Locations.objects.all()
        locations={}
        for i in location:
            locations[i.location_id]=i.currency
        doctor_profile['language_known'] = DoctorLanguages.objects.filter(doctor_id=doctor_id).values_list('languages',flat=True)
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data1': user_profile,
        'data2':doctor_profile,
        'locations':locations
    })

    except Exception as e:
          print("doc_profile_except",e)
          return Response({
        'response_code': 400,
        'status': 'Failed',
        'message':'Doctor doesnot Exist',
        'data': None })

@api_view(['POST'])
def doctor_time_slots(request):
    try:
        print('doctor_time_slots_request')
        data = request.data
        print(data)
        if data['doctor_flag'] == 1:
            time_slots = SeniorDoctorAvailableTimeSLotsSerializer( SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id = data['user_id'],date__gte = datetime.date.today()), many = True).data
        else:
            time_slots = JuniorDoctorSlotsSerializer( JuniorDoctorSlots.objects.filter(doctor_id = data['user_id'],date__gte = datetime.date.today()), many = True).data
        return Response({
            'response_code': 200,
            'status':'success',
            'data': time_slots,
        })
    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Failed',
            'message':'timeslots doesnot Exist',
            'data': None
        })

@api_view(['POST'])
def junior_doctor_transfer_view(request):
    doctor_id=request.data['doctor_id']
    appointment_status=request.data['appointment_status']
    appointment_id=request.data['appointment_id']
    appointment_date=request.data['appointment_date']
    appointment_time=request.data['appointment_time']
    try:
       doctor=DoctorMapping.objects.get(mapped_doctor=doctor_id)
    except:
        doctor=None
    filter={}
    if "language_pref" in request.data and request.data['language_pref'] != "":
        
            user_ids=DoctorLanguages.objects.filter(
                languages=request.data['language_pref']).values_list('doctor_id',flat=True)
            if len(user_ids)==0:
                user_ids=DoctorLanguages.objects.filter(
                languages='English').values_list('doctor_id',flat=True)
            filter['user_id__in']=user_ids
          

    if "gender_pref" in request.data and request.data['gender_pref'] != "":
          filter['gender']=request.data['gender_pref']

    if "doctor_flag" in request.data and request.data['doctor_flag'] != "":
        filter['doctor_flag']=request.data['doctor_flag']
    filter['doctor_flag'] = 'junior'
    print(filter)
    doctor_id_list=custom_filter(DoctorProfiles, filter).exclude(user_id=doctor_id).values_list("user_id",flat=True)
    print(doctor_id_list,"doctor_ids")
    appointment_date_=datetime.datetime.strptime(appointment_date,"%Y-%m-%d")
    weekday=appointment_date_.strftime("%A")
    try:
        if JuniorDoctorSlots.objects.filter(time_slot=appointment_time,date=appointment_date_,is_active=0).count() > 0:
                # time_slot_from=DoctorAvailableTimeslots.objects.filter(day=weekday).values_list(
                #     "time_slot_from",flat=True)
                # time_slot_to=DoctorAvailableTimeslots.objects.filter(day=weekday).values_list(
                #     "time_slot_to",flat=True)
                # print(weekday,time_slot_from,time_slot_to)
                # time_from=Timeslots.objects.get(id=min(time_slot_from))
                # time_to=Timeslots.objects.get(id=max(time_slot_to))
                # start=datetime.datetime.strptime(time_from.time_slots.split('-')[0].strip(), '%I%p').time()
                # end=datetime.datetime.strptime(time_to.time_slots.split('-')[1].strip(), '%I%p').time()
                # print(time_in_range(start, end,
                # datetime.datetime.strptime(appointment_time.split('-')[1].strip(), '%I%p').time()))
                # if time_in_range(start, end,
                # datetime.datetime.strptime(appointment_time.split('-')[1].strip(), '%I%p').time())==True:
            doctor_id_time_filter=DoctorAvailableTimeslots.objects.filter(
                doctor_id__in=doctor_id_list,day=weekday).values_list("doctor_id",flat=True)
            print(doctor_id_time_filter,"doctor_ids")
            filter['user_id__in']=doctor_id_time_filter
    except Exception as e:
                print(e)
                return Response({
                    'response_code': 400,
                    'status': 'Ok',
                    'message': "No Available Doctors",
        })
    if doctor:
        doc_id=custom_filter(DoctorProfiles, filter).exclude(user_id=doctor).values_list('user_id',flat=True)

    else:
        doc_id=custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)

    if doc_id:
       random_id=random.choice(doc_id)
       if random_id:
           JuniorDoctorSlots.objects.filter(doctor_id=random_id,time_slot=appointment_time,date=appointment_date_).update(is_active=1)
       DoctorMapping.objects.filter(appointment_id=appointment_id).update(mapped_doctor=random_id,doctor_flag="junior")
       AppointmentHeader.objects.filter(
        appointment_id=appointment_id).update(appointment_status=appointment_status,junior_doctor=random_id)

       doctor_email = get_user_mail(random_id)
       user_email = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
       start_time, end_time = get_appointment_time(appointment_time,appointment_date,"no specialization",doctor_flag='junior',doctor_id=random_id)
       print(start_time, end_time,"start_time, end_timestart_time, end_time")
       meet_link = generate_google_meet("Inticure,Doctor Appointment", "",
                                         [{"email": user_email}, {"email": doctor_email}], start_time,
                                         end_time)
       AppointmentHeader.objects.filter(appointment_id=appointment_id).update(meeting_link=meet_link)

       subject = 'Order Transfer Update'
       html_message = render_to_string('order_transfer.html', {'appointment_id': appointment_id,
       'doctor':get_users_name(random_id),
       'email':get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)})
       plain_message = strip_tags(html_message)
       from_email = 'wecare@inticure.com'
       cc = 'nextbighealthcare@inticure.com'
       to =  get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
       mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)

       subject = 'Appointment Confirmed'
       html_message = render_to_string('order_confirmation_doctor.html', {'date': appointment_date,"doctor_flag":1,
       'doctor_name':get_users_name(random_id),"time":appointment_time,"meet_link":meet_link,
       "name":get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)})
       plain_message = strip_tags(html_message)
       from_email = 'wecare@inticure.com'
       to =  get_user_mail(random_id)
        
       mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)

       return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':'Order Transfered',
        'doctor':get_users_name(random_id)
    })

    else:
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':'No Doctors Available'
    })

@api_view(['POST'])
def create_followup_reminder_view(request):
    reminder_serilazer = FollowUpReminderSerializer(data=request.data)
    if reminder_serilazer.is_valid():
        reminder_serilazer.save()
        subject = 'Followup Booking Reminder'
        html_message = render_to_string('followup_reminder.html', {
        "specialization":get_doctor_specialization(
            AppointmentHeader.objects.get(appointment_id=request.data['appointment_id']).senior_doctor),
        'name':get_users_name(AppointmentHeader.objects.get(
        appointment_id=request.data['appointment_id']).user_id)})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        cc = 'nextbighealthcare@inticure.com'
        to = get_user_mail(AppointmentHeader.objects.get(appointment_id=request.data['appointment_id']).user_id)

        mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)
        return Response({
            'response_code': 200,
            'status': 'Ok',
            'message': 'Created Successfully'
        })
    return Response({
        'response_code': 400,
        'status': 'Ok',
        'message': 'Failed to create reminder'
    })


@api_view(['POST'])
def followup_reminder_list_view(request):
    reminder_serilazed_data = FollowUpReminderSerializer(FollowUpReminder.objects.filter(appointment_id=request.data['appointment_id']),many=True).data
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': reminder_serilazed_data
    })


@api_view(['POST'])
def create_discussion_view(request):
    discussion_serializer = AppointmentDiscissionSerializer(data=request.data)
    if discussion_serializer.is_valid():
        discussion_serializer.save()
        if request.data['is_query']==1:
             subject = 'Your patient needs your help'
             html_message = render_to_string('order_discussion.html', {"doctor_flag":1,
                'doctor_name':get_users_name(request.data['doctor_id']),
                'name': get_users_name(AppointmentHeader.objects.get(
                appointment_id=request.data['appointment_id']).user_id) })
             plain_message = strip_tags(html_message)
             from_email = 'wecare@inticure.com>'
             to =  get_user_mail(request.data['doctor_id'])
             cc = 'nextbighealthcare@inticure.com'

             mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)
        if request.data['is_reply']==1:
             subject = 'You received a response!'
             html_message = render_to_string('order_discussion.html', {"doctor_flag":0,
                'name':get_users_name(AppointmentHeader.objects.get(
             appointment_id=request.data['appointment_id']).user_id)})
             plain_message = strip_tags(html_message)
             from_email = 'wecare@inticure.com'
             to =  get_user_mail(AppointmentHeader.objects.get(
                appointment_id=request.data['appointment_id']).user_id)
             cc = "nextbighealthcare@inticure.com"
             mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)
        # try:
        #         sms_service.send_message(
        #        "Hi There, Your Discussion on Appointment #%s has received a response! Please refer mail for more info"%(request.data['appointment_id']),
        #         "+91" + str(CustomerProfile.objects.get(user_id=AppointmentHeader.objects.get(
        #             appointment_id=request.data['appointment_id']).user_id).mobile_number))
        # except Exception as e:
        #       print(e)
        #       print("MESSAGE SENT ERROR")
        return Response({
            'response_code': 200,
            'status': 'Ok',
            'message': 'Created Successfully'
        })
    return Response({
        'response_code': 400,
        'status': 'Ok',
        'message': 'Failed to create discussion'
    })


@api_view(['POST'])
def discussion_list_view(request):
    objects_filter = AppointmentDiscussion.objects.filter(appointment_id=request.data['appointment_id'])
    discussion_serialized_data = AppointmentDiscissionSerializer(objects_filter, many=True).data
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': discussion_serialized_data,
        'discussion_count':objects_filter.filter(is_query=1).count()
    })

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

def slot_update(doctor_id,slot_from,slot_to,weekday):
    try:
        slot_exist=DoctorAvailableTimeslots.objects.get(doctor_id=doctor_id,day=weekday)
        if slot_exist:
            DoctorAvailableTimeslots.objects.filter(doctor_id=doctor_id,day=weekday).update(
                time_slot_from=slot_from,time_slot_to=slot_to
            )
    except:
        slot_exist=None
        DoctorAvailableTimeslots.objects.create(doctor_id=doctor_id,day=weekday,
        time_slot_from=slot_from,time_slot_to=slot_to)
    # return slot_exist
    
@api_view(['POST'])
def working_hour_calender_update(request):
    print("UPDATE CAL>>")

@api_view(['POST'])
def working_hour_list_view(request):
   objects_filter=DoctorAvailableTimeslots.objects.filter(doctor_id=request.data['doctor_id'])
   working_hour_serializer=WorkingHourSerializer(objects_filter,many=True).data
   print(working_hour_serializer)
   for time_slot in working_hour_serializer:
       timeslots=TimeSlotSerializer(Timeslots.objects.filter(
        id__gte=time_slot['time_slot_from'],id__lte=time_slot['time_slot_to']),many=True).data
    #    timeslots_to=TimeSerializer(Time.objects.filter(id=time_slot['time_slot_to']),many=True).data
       time_slot['timeslots']=timeslots
   return Response({
       'response_code': 200,
        'status': 'Ok',
        'data': working_hour_serializer
   })


@api_view(['POST'])
def calender_view(request):
    print("calender-view")
    timeslots=[]
    print(request.data)
    objects_filter=DoctorAvailableDates.objects.filter(doctor_id=request.data['doctor_id'])
    working_dates_serializer=WorkingDateSerializer(objects_filter,many=True).data
    print(working_dates_serializer)
    for working_hour in working_dates_serializer:
        try:
           calender_date=DoctorCalenderUpdate.objects.get(doctor_id=request.data['doctor_id'],
            date=working_hour['date'])
           print(calender_date)
           print("exe")
        except :
           calender_date=None
        if calender_date:
            
            objects_filter2=DoctorCalenderUpdate.objects.filter(doctor_id=request.data['doctor_id'],
                date=working_hour['date'])
            print(objects_filter2)
            timeslot_added=DoctorAddedTimeSlots.objects.filter(doctor_id=request.data['doctor_id'],
                        date=working_hour['date']).values_list('slot',flat=True)
            print(timeslot_added)
        else:
           objects_filter2=DoctorAvailableTimeslots.objects.filter(doctor_id=working_hour['doctor_id']
           ,day=working_hour['day'])
           timeslot_added=[]
           print(objects_filter2)
        working_time_slots_serializer=WorkingHourSerializer(objects_filter2,many=True).data
        print(working_time_slots_serializer)
        for time_slot in working_time_slots_serializer:
          timeslots=TimeSlotSerializer(Timeslots.objects.filter(
           id__in=timeslot_added),many=True).data
        working_hour['time_slots']=timeslots
    return Response({
       'response_code': 200,
        'status': 'Ok',
        'data': working_dates_serializer
    })

@api_view(['POST'])
def timeslot_list_view(request):
    print("time-slot-list")
    print(request.data)
    if request.data['doctor_flag'] == 2:
        flag = 'jr'
    else:
        flag = 'sr'
    try:
        if flag == 'sr':
            doctor = DoctorProfiles.objects.get(user_id = request.data['doctor_id']).doctor_profile_id
            duration = Duration.objects.get(doctor_id = doctor).duration
            timeslots=TimeSlotSerializer(Timeslots.objects.filter(duration = duration),many=True).data
        else:
            user = User.objects.get(first_name = 'junior',last_name = 'doctor').id
            doctor = DoctorProfiles.objects.get(user_id = user).doctor_profile_id
            duration = Duration.objects.get(doctor_id = doctor).duration
            timeslots=TimeSlotSerializer(Timeslots.objects.filter(duration = duration),many=True).data
        print(timeslots)
    except Exception as e:
        print(e)
        timeslots = None
    return Response({
          'response_code': 200,
          'status': 'Ok',
          'data': timeslots,
          'weekday':[{"day1":"Sunday","day2":"Monday","day3":"Tuesday","day4":"Wednesday",
          "day5":"Thursday","day6":"Friday","day7":"Saturday"}]
    })

def time_slots(start_time, end_time, duration):
    start = datetime.datetime.strptime(str(start_time), "%H:%M:%S")
    end = datetime.datetime.strptime(str(end_time), "%H:%M:%S")
    delta = timedelta(minutes=duration)
    slots = []
    while start + delta <= end:
        slot = start.strftime("%I:%M%p") + '-' + (start + delta).strftime("%I:%M%p")
        slots.append(slot)
        start += delta
    return slots


def get_timeslots_for_date(date, time_slots_available):
    timeslot = []
    for data in time_slots_available:
        if data['date'] == date:
            start_time=datetime.datetime.strptime(data['timeslot'].split('-')[0].strip(), '%I:%M%p').time()
            end_time=datetime.datetime.strptime(data['timeslot'].split('-')[1].strip(), '%I:%M%p').time()
            start_datetime = datetime.datetime.combine(datetime.datetime.strptime(date, '%Y-%m-%d').date(), start_time)
            end_datetime = datetime.datetime.combine(datetime.datetime.strptime(date, '%Y-%m-%d').date(), end_time)
            duration_seconds = (end_datetime - start_datetime).seconds
            duration_minutes = duration_seconds // 60
            num_hours = duration_minutes // 60
            if duration_seconds == (end_datetime - start_datetime).seconds:
                timeslot.append({'date':date,'timeslot': f"{start_time.strftime('%I:%M%p')}-{end_time.strftime('%I:%M%p')}"})
            else:
                for i in range(num_hours):
                    start_slot = start_datetime + datetime.timedelta(hours=i)
                    end_slot = start_slot + datetime.timedelta(hours=1)
                    time_slot_str = start_slot.strftime('%H:%M') + '-' + end_slot.strftime('%H:%M')
                    timeslot.append({'date':date,'timeslot': time_slot_str})
    return timeslot

@api_view(['POST'])
def specialization_timeslot_view(request):
    print("*************time-slot-list*****************")
    print(request.data)
    filter={}
    count=0
    timeslot=list()
    no_time_slots = False
    preferred = True
    calculated_list=[]
    duration=60
    if 'doctor' in request.data:
        request.data['doctor_flag'] = request.data['doctor']
  
    if 'doctor_id' in request.data and request.data['doctor_id']!="":
            doctor_id = request.data['doctor_id']
            print("doctor_id","doctor_id",doctor_id)
    if request.data['language_pref'] != 'No Preference' and request.data['language_pref'] != "":
        user_ids=DoctorLanguages.objects.filter(languages=request.data['language_pref']).values_list('doctor_id',flat=True)
        print('2107 ',user_ids)
        if len(user_ids) == 0:
            user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
        filter['user_id__in']=user_ids
        #   filter['user_id__in']=DoctorLanguages.objects.filter(languages=request.data['language_pref']).values_list('doctor_id',flat=True)
    if 'gender' in request.data and request.data['gender'] != ""  :
        if request.data['gender'] == 'female' or request.data['gender'] == 'male':
            filter['gender']=request.data['gender']
            print('gender_')

    if "doctor_flag" in request.data and request.data['doctor_flag'] != "":
            filter['doctor_flag']=request.data['doctor_flag']

    if "specialization" in request.data and request.data['specialization'] != "":
            filter['specialization']=request.data['specialization']
            # try:
            #     duration=DoctorSpecializations.objects.get(specialization=specialization).time_duration
            # except:
            #     duration=60
    if "location" in request.data and request.data['location'] != "" :
        try:
            try:
                location = Locations.objects.get(location = request.data['location']).location_id
            except Exception as e:
                print(e)
                location = Locations.objects.get(location = 'USA').location_id
        except:
            try:
                location = int(request.data['location'])
            except Exception as e:
                location = Locations.objects.get(location = request.data['location']).location_id
        filter['location'] = location
    if  "appointment_id" not in request.data or request.data['appointment_id'] == "":
        print("appointment id is null")
        if 'language_pref' in request.data and request.data['language_pref'] != "":
            user_ids=DoctorLanguages.objects.filter(languages=request.data['language_pref']).values_list('doctor_id',flat=True)
        else:
            user_ids=DoctorLanguages.objects.all().values_list('doctor_id',flat=True)
            preferred = False

        print('2140 ',user_ids)
        filter['user_id__in']=user_ids
        print(filter)
        doctor_id = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
        if len(doctor_id) == 0:
            del filter['location']
            doctor_id = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
        print("here",doctor_id)
        if len(doctor_id) == 0:
            filter2 = {}
            user_ids=DoctorLanguages.objects.all().values_list('doctor_id',flat=True)
            preferred = False
            filter2['user_id__in']=user_ids
            print(user_ids)
            if 'gender' in request.data and request.data['gender'] != "":
                if request.data['gender'] == 'female' or request.data['gender'] == 'male':
                    filter2['gender']=request.data['gender']

            if "doctor_flag" in request.data and request.data['doctor_flag'] != "":
                    filter2['doctor_flag']=request.data['doctor_flag']

            if "specialization" in request.data and request.data['specialization'] != "":
                    filter2['specialization']=request.data['specialization']
                    # try:
                    #     duration=DoctorSpecializations.objects.get(specialization=specialization).time_duration
                    # except:
                    #     duration=60
            if "location" in request.data and request.data['location'] != "" :
                try:
                    try:
                        location = Locations.objects.get(location = request.data['location']).location_id
                    except Exception as e:
                        print(e)
                        location = Locations.objects.get(location = 'USA').location_id
                except:
                    try:
                        location = int(request.data['location'])
                    except Exception as e:
                        location = Locations.objects.get(location = request.data['location']).location_id
                filter2['location'] = location
            if  "appointment_id" not in request.data or request.data['appointment_id'] == "":
                print("appointment id is null")
                if 'language_pref' in request.data and request.data['language_pref'] != "":
                    user_ids=DoctorLanguages.objects.filter(languages=request.data['language_pref']).values_list('doctor_id',flat=True)
                else:
                    user_ids=DoctorLanguages.objects.all().values_list('doctor_id',flat=True)
                    preferred = False
                print('2173 ',user_ids)
                filter2['user_id__in']=user_ids
                print(filter2)
                doctor_id = custom_filter(DoctorProfiles, filter2).values_list('user_id',flat=True)
                print("here2",doctor_id)
                if len(doctor_id) == 0:
                    del filter2['location']
                    doctor_id = custom_filter(DoctorProfiles, filter2).values_list('user_id',flat=True)
                    print("here22",doctor_id)
                    if len(doctor_id) == 0:
                        user_ids=DoctorLanguages.objects.all().values_list('doctor_id',flat=True)
                        preferred = False
                        filter2['user_id__in']=user_ids
                        doctor_id = custom_filter(DoctorProfiles, filter2).values_list('user_id',flat=True)
                print("here23",doctor_id)
            no_time_slots = True
        objects_filter=DoctorAvailableDates.objects.filter(doctor_id__in=doctor_id,
                        date__gte=datetime.datetime.now().date() + timedelta(days=1))
                        
    else:
        if "is_transfer" in request.data and request.data['is_transfer'] == 1:
            # print("is_transfer is 1")
            #print("senior doctor",doctor_id)
            doctor_qset=AppointmentHeader.objects.get(appointment_id=request.data['appointment_id'])
            doctor_id=doctor_qset.senior_doctor
            
            doctor_ids = custom_filter(DoctorProfiles, filter).exclude(user_id=doctor_id).values_list('user_id',flat=True)
            # print("excluded doc id",doctor_ids)
            objects_filter=DoctorAvailableDates.objects.filter(doctor_id__in=doctor_ids,
                        date__gte=datetime.datetime.now().date() + timedelta(days=1))
        else:
            if "appointment_id" in request.data and request.data['appointment_id'] != "":
                print(filter)
                if 'location' in filter:
                    del filter['location']
                try:
                    # print("Appoint-id")
                    doctor_qset=AppointmentHeader.objects.get(appointment_id=request.data['appointment_id'])
                    doctor_id=doctor_qset.senior_doctor
                    specialization=DoctorProfiles.objects.get(user_id=doctor_id).specialization
                    # duration=DoctorSpecializations.objects.get(specialization=specialization).time_duration
                    filter['specialization']=specialization
                    user_ids=DoctorLanguages.objects.filter(languages=doctor_qset.language_pref).values_list('doctor_id',flat=True)
                    print(user_ids)
                    if len(user_ids) == 0:
                            user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
                            preferred = False
                    print(user_ids)
                    filter['user_id__in']=user_ids
                    # if doctor_qset.gender_pref:
                    #     filter['gender']=doctor_qset.gender_pref
                except Exception as e:
                    print("Except exception as e",e)
                  
            # print("is_transfer is o")
            print(filter)
            doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
            if len(doctor_ids) == 0:
                preferred = False
                user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
                filter['user_id__in']=user_ids
                doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
            print(doctor_ids)
            objects_filter=DoctorAvailableDates.objects.filter(doctor_id__in=doctor_ids,
                        date__gte=datetime.datetime.now().date() + timedelta(days=1))
            print(objects_filter)
    working_dates_serializer=WorkingDateSerializer(objects_filter,many=True).data
    slot_list=[]
    print('asdgsdafg$#########################')
    print(working_dates_serializer)
    print('asdgsdafg$#########################')
    print(timeslot)
    for working_hour in working_dates_serializer:
        print(working_hour)
        appointment_date_=datetime.datetime.strptime(working_hour['date'],"%Y-%m-%d")
        print(appointment_date_)
        slots_available=SeniorDoctorAvailableTimeSLotsSerializer(SeniorDoctorAvailableTimeSLots.objects.filter(
                date=appointment_date_,doctor_id=working_hour['doctor_id'],is_active=0),many=True).data
        print(slots_available)
        time_solt_data = {'date':working_hour['date'],'timeslot': slots_available}
        print(time_solt_data)

        if time_solt_data:
            if len(timeslot) > 0:
                print("here")
                found_date = False
                for i, date in enumerate(timeslot):
                    print("for loop")
                    if date["date"] == working_hour['date']:
                        print("date",date['date'])
                        print(date['timeslot'])
                        found_date = True
                        print('fghj',date['timeslot'])
                        print('asdf',time_solt_data['timeslot'])

                        for slot in time_solt_data['timeslot']:
                            duplicate_found = False  
                            for slot2 in date['timeslot']:
                                if slot['time_slot'] == slot2['time_slot'] and slot['end_time'] == slot2['end_time']:
                                    duplicate_found = True
                            
                            if not duplicate_found:
                                date['timeslot'].append(slot)                                                 

                        if len(date['timeslot']) < len(time_solt_data['timeslot']) :
                            print("i",i)
                            timeslot.pop(i)
                            print("poped timeslot",timeslot)
                            if len(time_solt_data['timeslot']) > 0 :
                                timeslot.append(time_solt_data)
                        
                            print("affed timeslot",timeslot)
                            break
                if not found_date:
                    # print("append",time_solt_data)
                    print("time slot",timeslot)
                    if len(time_solt_data['timeslot'])>0:
                        timeslot.append(time_solt_data)
            else:
                print("else")
                if len(time_solt_data['timeslot']) > 0 :
                    timeslot.append(time_solt_data)
        # else:
        #     return Response({
        #     'response_code': 400,
        #     'status': 'Ok',
        #     'message':'No Doctors Available'})
    print(timeslot)
    message=""
    if duration:
        message="This appointment may take upto %s minutes" % (duration)

    sorted_timeslot= sorted(timeslot, key=lambda k: k['date'])
    print("sorted_timeslot",sorted_timeslot)
    for data in sorted_timeslot:
        if 'timeslot' in data and isinstance(data['timeslot'], list):
            data['timeslot'] = sorted(data['timeslot'], key=lambda k: k['senior_doctor_timeslot_id'])

    return Response({
        'response_code': 200,
        'status': 'Ok',
        'slots':sorted_timeslot,
        "Message":message,
        "no_timeslots":no_time_slots,
        "preferred":preferred
    })

@api_view(['POST'])
def specialization_timeslot_view_reschedule(request):
    print(request.data)
    timeslot=list()
    try:
        appointment = AppointmentHeader.objects.get(appointment_id = request.data['appointment_id']).senior_doctor
        objects_filter=DoctorAvailableDates.objects.filter(doctor_id=appointment,
                        date__gte=datetime.datetime.now().date() + timedelta(days=1))
        working_dates_serializer=WorkingDateSerializer(objects_filter,many=True).data
        for slot in working_dates_serializer:
            appointment_date_=datetime.datetime.strptime(slot['date'],"%Y-%m-%d")
            slots_available=SeniorDoctorAvailableTimeSLotsSerializer(SeniorDoctorAvailableTimeSLots.objects.filter(
                    date= appointment_date_, doctor_id=appointment, is_active=0),many=True).data
            time_solt_data = {'date':slot['date'], 'timeslot': slots_available}
            if time_solt_data:
                if len(timeslot) > 0:
                    print("here")
                    found_date = False
                    for i, date in enumerate(timeslot):
                        print("for loop")
                        if date["date"] == slot['date']:
                            print("date",date['date'])
                            print(date['timeslot'])
                            found_date = True
                            print('fghj',date['timeslot'])
                            print('asdf',time_solt_data['timeslot'])

                            for slot in time_solt_data['timeslot']:
                                duplicate_found = False  
                                for slot2 in date['timeslot']:
                                    if slot['time_slot'] == slot2['time_slot'] and slot['end_time'] == slot2['end_time']:
                                        duplicate_found = True
                                
                                if not duplicate_found:
                                    date['timeslot'].append(slot)                                                 

                            if len(date['timeslot']) < len(time_solt_data['timeslot']) :
                                print("i",i)
                                timeslot.pop(i)
                                print("poped timeslot",timeslot)
                                if len(time_solt_data['timeslot']) > 0 :
                                    timeslot.append(time_solt_data)
                            
                                print("affed timeslot",timeslot)
                                break
                    if not found_date:
                        # print("append",time_solt_data)
                        print("time slot",timeslot)
                        if len(time_solt_data['timeslot'])>0:
                            timeslot.append(time_solt_data)
                else:
                    print("else")
                    if len(time_solt_data['timeslot']) > 0 :
                        timeslot.append(time_solt_data)
        print(timeslot)
        message=""
        sorted_timeslot= sorted(timeslot, key=lambda k: k['date'])
        print("sorted_timeslot",sorted_timeslot)
        for data in sorted_timeslot:
            if 'timeslot' in data and isinstance(data['timeslot'], list):
                data['timeslot'] = sorted(data['timeslot'], key=lambda k: k['senior_doctor_timeslot_id'])

        return Response({
            'response_code': 200,
            'status': 'Ok',
            'slots':sorted_timeslot,
            'preferred':True
        })
    except Exception as e:
        print(e)
        return Response({
            'response_code': 404,
            'status': 'No Data Available',
            "slots":''

            })

@api_view(['POST'])
def available_slots_view(request):
        print('entered')
        filter={}
        time_slot=[]
        time_solt_data={}
        preferred_one = True
        preferred_gender = True
        both_preference = True
        print(request.data)
        if "language" in request.data and request.data['language'] != "":
            user_ids=DoctorLanguages.objects.filter(languages=request.data['language']).values_list('doctor_id',flat=True)
            print(user_ids)
            if len(user_ids) == 0:
                user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
                preferred_one = False
            filter['user_id__in']=user_ids
        print('filter',filter)
        if "gender" in request.data and request.data['gender'] != "":
          filter['gender']=request.data['gender']
        else:
            filter['gender__in']=['male,female']
        if "doctor" in request.data and request.data['doctor'] != "":
            filter['doctor_flag']=request.data['doctor']

        print('filter',filter)
        
        if "appointment_id" in request.data and request.data['appointment_id'] != "":
            try:
                print("Appoint-id")
                doctor_qset=AppointmentHeader.objects.get(appointment_id=request.data['appointment_id'])
                doctor_id=doctor_qset.junior_doctor
            except Exception as e:
                print("EXcept",e)
                doctor_id=None
            print(doctor_id,"doc id")
            objects_filter=DoctorAvailableDates.objects.filter(doctor_id=doctor_id,
                        date__gte=datetime.datetime.now().date() + timedelta(days=1))
        else:
            doctor_id = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
            print(doctor_id,"@@@@@@@@@@@@@@@@@@@@@@@@@@@@doctors available")
            objects_filter=DoctorAvailableDates.objects.filter(doctor_id__in=doctor_id,
                        date__gte=datetime.datetime.now().date() + timedelta(days=1))
        working_dates_serializer=WorkingDateSerializer(objects_filter,many=True).data
        print('lasdjkf ',objects_filter)
        if len(objects_filter) == 0:
            preferred_one = False
            filter2 = {}
            print(filter2)
            user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
            filter2['user_id__in']=user_ids
            if "gender" in request.data and request.data['gender'] != "":
                filter2['gender']=request.data['gender']
            if "doctor" in request.data and request.data['doctor'] != "":
                filter2['doctor_flag']=request.data['doctor']

            print('filter',filter2)
            
            if "appointment_id" in request.data and request.data['appointment_id'] != "":
                try:
                    print("Appoint-id")
                    doctor_qset=AppointmentHeader.objects.get(appointment_id=request.data['appointment_id'])
                    doctor_id=doctor_qset.junior_doctor
                except Exception as e:
                    print("EXcept",e)
                    doctor_id=None
                print(doctor_id,"doc id")
                objects_filter=DoctorAvailableDates.objects.filter(doctor_id=doctor_id,
                            date__gte=datetime.datetime.now().date() + timedelta(days=1))
            else:
                doctor_id = custom_filter(DoctorProfiles, filter2).values_list('user_id',flat=True)
                print(doctor_id,"@@@@@@@@@@@@@@@@@@@@@@@@@@@@doctors available2")
                objects_filter=DoctorAvailableDates.objects.filter(doctor_id__in=doctor_id,
                            date__gte=datetime.datetime.now().date() + timedelta(days=1))
            working_dates_serializer=WorkingDateSerializer(objects_filter,many=True).data

            if len(objects_filter) == 0:
                preferred_one = False
                preferred_gender = False
                filter3 = {}
                print(filter3)
                user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
                filter3['user_id__in']=user_ids
                if "doctor" in request.data and request.data['doctor'] != "":
                    filter3['doctor_flag']=request.data['doctor']
               
                print('filter',filter3)
                
                if "appointment_id" in request.data and request.data['appointment_id'] != "":
                    try:
                        print("Appoint-id")
                        doctor_qset=AppointmentHeader.objects.get(appointment_id=request.data['appointment_id'])
                        doctor_id=doctor_qset.junior_doctor
                    except Exception as e:
                        print("EXcept",e)
                        doctor_id=None
                    print(doctor_id,"doc id")
                    objects_filter=DoctorAvailableDates.objects.filter(doctor_id=doctor_id,
                                date__gte=datetime.datetime.now().date() + timedelta(days=1))
                else:
                    doctor_id = custom_filter(DoctorProfiles, filter3).values_list('user_id',flat=True)
                    print(doctor_id,"@@@@@@@@@@@@@@@@@@@@@@@@@@@@doctors available3")
                    objects_filter=DoctorAvailableDates.objects.filter(doctor_id__in=doctor_id,
                                date__gte=datetime.datetime.now().date() + timedelta(days=1))
                working_dates_serializer=WorkingDateSerializer(objects_filter,many=True).data

        print('objects_filter ',objects_filter)
        print('working_dates_serializer ',working_dates_serializer)
        print("date____________________",objects_filter.values_list('date'))
        for working_hour in working_dates_serializer:
            print(working_hour['date'],"working hour date")
            try:
                doctor_calender=DoctorCalenderUpdate.objects.values_list('doctor_id',flat=True)
                print(doctor_calender)
            except:
                doctor_calender=None
            #print("doctor_calendeer",doctor_calender)
            if doctor_calender:
                print("calender-")
                working_times_from=DoctorCalenderUpdate.objects.filter(
                        doctor_id__in=doctor_calender)
                timeslot_added=DoctorAddedTimeSlots.objects.filter(doctor_id=working_hour['doctor_id'],
                        date=working_hour['date']).values_list('slot',flat=True)
            else:
                working_times_from=[]
                timeslot_added=[]
            print('2148 ', working_hour)
            jr_doc_added_slots=JuniorDoctorSlotsSerializer(JuniorDoctorSlots.objects.filter(
                doctor_id=working_hour['doctor_id'],date=working_hour['date'],is_active=0),many=True).data
            print ("compare date",working_hour['date'],working_hour['doctor_id'])
            # print("jr_doc_added_slots",jr_doc_added_slots)
            # time_solt_data = {"date": working_hour['date'],"time_slots": TimeSlotSerializer(
            #         Timeslots.objects.filter(id__in=timeslot_added), many=True ).data}
            time_solt_data = {"date": working_hour['date'],"time_slots":jr_doc_added_slots}
            # print('2144',time_solt_data)
            if len(time_slot) > 0:
                print("here")
                found_date = False
                for i, date in enumerate(time_slot):
                    print("for loop")
                    print ("compare date",date['date'],working_hour['date'])
                    if date["date"] == working_hour['date']:
                        print("date",date['date'])
                        print(date['time_slots'])
                        found_date = True
                        for slot in time_solt_data['time_slots']:
                            duplicate_found = False  
                            for slot2 in date['time_slots']:
                                if slot['time_slot'] == slot2['time_slot'] and slot['end_time'] == slot2['end_time']:
                                    duplicate_found = True
                            
                            if not duplicate_found:
                                date['time_slots'].append(slot)

                        if  len(date['time_slots']) < len(time_solt_data['time_slots']) :
                            print("i",i)
                            time_slot.pop(i)
                            print("poped timeslot",time_slot)
                            if len(time_solt_data['time_slots']) > 0 :
                                time_slot.append(time_solt_data)
                            #time_slot.append(time_solt_data)
                            print("affed timeslot",time_slot)
                            break
                if not found_date:
                    print("append",time_solt_data)
                    print("time slot",time_slot)
                    if len(time_solt_data['time_slots'])>0:
                        time_slot.append(time_solt_data)
            else:
                print("else")
                if len(time_solt_data['time_slots']) > 0 :
                    # print(time_solt_data)
                    time_slot.append(time_solt_data)
        print("time_solt_data",time_solt_data)
        print("time",time_slot)
        if len(time_slot) == 0:
            print(time_slot)
            print('2187 time slots are not available it is showing zero')
            return Response({
            'response_code': 404,
            'status': 'No Data Available',
            "slots":time_slot

            })
        else:
            print('  2140  ')

            def sort_time_slots(data):
                for day_data in data:
                    day_data['time_slots'] = sorted(
                        day_data['time_slots'],
                        key=lambda slot: datetime.datetime.strptime(slot['time_slot'], '%I:%M%p')
                    )
                return data
            
            sorted_timeslot= sorted(time_slot, key=lambda k: k['date'])
            for data in sorted_timeslot:
                data['time_slots'] = sorted(
                data['time_slots'],
                key=lambda k: k['junior_doctor_slot_id']
                )
            sorted_data = sort_time_slots(sorted_timeslot)
            print('2643', sorted_data)
            print('2197 ', sorted_timeslot)
            return Response({
            'response_code': 200,
            'status': 'Ok',
            "slots":time_slot,
            "Message":"The appointment may take upto 10 minutes",
            'preferred_one':preferred_one,
            'preferred_gender':preferred_gender
        })

'''This view is for listing slots of junior doctor based on the dates they have added timeslots. '''

@api_view(['POST'])
def available_slots_view_Copy(request):
        filter={}
        time_slot=[]
        time_solt_data={}
        if "language" in request.data and request.data['language'] != "":
          filter['user_id__in']=DoctorLanguages.objects.filter(languages=request.data['language']).values_list('doctor_id',flat=True)
        if "gender" in request.data and request.data['gender'] != "":
          filter['gender']=request.data['gender']
        if "doctor" in request.data and request.data['doctor'] != "":
            filter['doctor_flag']=request.data['doctor']

        if "location" in request.data and request.data['location']:
            if request.data['location'] == "IN":
                filter['location']=1
            else:
                filter['location']=2
        if "appointment_id" in request.data and request.data['appointment_id'] != "":
            try:
                print("Appoint-id")
                doctor_qset=AppointmentHeader.objects.get(appointment_id=request.data['appointment_id'])
                doctor_id=doctor_qset.junior_doctor
            except Exception as e:
                print("EXcept",e)
                doctor_id=None
            print(doctor_id,"doc id")
            objects_filter=DoctorAvailableDates.objects.filter(doctor_id=doctor_id,
                        date__gte=datetime.datetime.now().date() + timedelta(days=1))
        else:
            print("filter items",filter)
            doctor_id = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
            print(doctor_id,"doctors available")

            objects_filter=DoctorAvailableDates.objects.filter(doctor_id__in=doctor_id,
                        date__gte=datetime.datetime.now().date() + timedelta(days=1))
        working_dates_serializer=WorkingDateSerializer(objects_filter,many=True).data
        print("date____________________",objects_filter.values_list('date'))
        for working_hour in working_dates_serializer:
            print(working_hour['date'],"working hour date")
            try:
                doctor_calender=DoctorCalenderUpdate.objects.values_list('doctor_id',flat=True)

            except:
                doctor_calender=None
            #print("doctor_calendeer",doctor_calender)
            if doctor_calender:
                print("calender-")
                working_times_from=DoctorCalenderUpdate.objects.filter(
                        doctor_id__in=doctor_calender)
                timeslot_added=DoctorAddedTimeSlots.objects.filter(doctor_id=working_hour['doctor_id'],
                        date=working_hour['date']).values_list('slot',flat=True)
            else:
                working_times_from=[]
                timeslot_added=[]
            jr_doc_added_slots=JuniorDoctorSlotsSerializer(JuniorDoctorSlots.objects.filter(doctor_id=working_hour['doctor_id'],date=working_hour['date']),many=True).data
            print ("compare date",working_hour['date'],working_hour['doctor_id'])
            print("jr_doc_added_slots",jr_doc_added_slots)
            # time_solt_data = {"date": working_hour['date'],"time_slots": TimeSlotSerializer(
            #         Timeslots.objects.filter(id__in=timeslot_added), many=True ).data}
            time_solt_data = {"date": working_hour['date'],"time_slots":jr_doc_added_slots}

            if len(time_slot) > 0:
                print("here")
                found_date = False
                for i, date in enumerate(time_slot):
                    print("for loop")
                    print ("compare date",date['date'],working_hour['date'])
                    if date["date"] == working_hour['date']:
                        print("date",date['date'])
                        print(date['time_slots'])
                        found_date = True
                        if  len(date['time_slots']) < len(time_solt_data['time_slots']) :
                            print("i",i)
                            time_slot.pop(i)
                            print("poped timeslot",time_slot)
                            if len(time_solt_data['time_slots']) > 0 :
                                time_slot.append(time_solt_data)
                            #time_slot.append(time_solt_data)
                            print("affed timeslot",time_slot)
                            break
                if not found_date:
                    print("append",time_solt_data)
                    print("time slot",time_slot)
                    if len(time_solt_data['time_slots'])>0:
                        time_slot.append(time_solt_data)
            else:
                print("else")
                if len(time_solt_data['time_slots']) > 0 :
                    print(time_solt_data)
                    time_slot.append(time_solt_data)

        if len(time_slot) == 0:
            return Response({
            'response_code': 404,
            'status': 'No Data Available',
            "slots":time_slot

            })
        else:
            sorted_timeslot= sorted(time_slot, key=lambda k: k['date'])
            for data in sorted_timeslot:
                data['time_slots'] = sorted(
                data['time_slots'],
                key=lambda k: k['time_slot'], reverse=True
                )
            return Response({
            'response_code': 200,
            'status': 'Ok',
            "slots":sorted_timeslot,
            "Message":"The appointment may take upto 10 minutes"
        })

def add_Senior_timeslots(request):
    print('2262 adding senior doctor timeslots')
    print(request.data)
    if len(request.data['slots']) !=0:
        try:
            duration=DoctorSpecializations.objects.get(specialization=request.data['specialization']).time_duration
        except:
            duration=60
        time_slots_available= TimeSlotSerializer(
        Timeslots.objects.filter(id__in=request.data['slots']), many=True ).data
        print(time_slots_available,"slots available",duration)
        all_timeslots=[]
        for data in time_slots_available:
            print(data['time_slots'])
            start_time=datetime.datetime.strptime(data['time_slots'].split('-')[0].strip(), '%I:%M %p').time()
            end_time=datetime.datetime.strptime(data['time_slots'].split('-')[1].strip(), '%I:%M %p').time()
            print("starttime",start_time,"endtime",end_time,duration)
            print("duration",duration)
            calculated_list=list(time_slots(start_time, end_time, duration))
            all_timeslots.extend(calculated_list)
            print(all_timeslots)
        print(all_timeslots)
        for time_slot in list(set(all_timeslots)):
            print("senior doc timeslot")
            print(time_slot)
            doctor = DoctorProfiles.objects.get(user_id = request.data['doctor_id']).doctor_profile_id
            duration = Duration.objects.get(doctor_id = doctor).duration
            start_time = datetime.datetime.strptime(time_slot, "%I:%M%p")
            end_time = start_time + timedelta(minutes=int(duration))
            end_time_str = end_time.strftime("%I:%M%p")
            SeniorDoctorAvailableTimeSLots.objects.create(doctor_id=request.data['doctor_id'],\
                            time_slot=time_slot,date=request.data['date'],end_time=end_time_str)

@api_view(['POST'])
def calender_edit_view(request):
    print("calender-edit")
    print(request.data)
    slots=request.data['slots']
    doctor_id=request.data['doctor_id']
    dates=request.data['date']
    flag,specialization=get_doctor_flag(request)
    print(flag, specialization)
    request.data['specialization']=specialization
    weekday=(datetime.datetime.strptime(dates,"%Y-%m-%d")).strftime("%A")
    print('weekday',weekday)
    try:
       doctor=DoctorCalenderUpdate.objects.get(doctor_id=doctor_id,date=dates)
    except:
        doctor=None
    print(slots)
    if slots!="" and slots!=[]:
        print(min(slots),max(slots))
        if doctor==None:
            DoctorCalenderUpdate.objects.create(doctor_id=doctor_id,day=weekday,date=dates,
                 time_slot_from=min(slots),time_slot_to=max(slots))
        else:
            slots_available=DoctorCalenderUpdate.objects.filter(doctor_id=doctor_id,date=dates)
            DoctorCalenderUpdate.objects.filter(doctor_id=doctor_id,date=dates).update(
                 time_slot_from=min(slots),time_slot_to=max(slots))
        if flag =="junior":
            if DoctorAddedTimeSlots.objects.filter(doctor_id=doctor_id,date=dates).count() > 0:
                print("doctor slots > 0 ")
                data=DoctorAddedTimeSlotsSerializer(DoctorAddedTimeSlots.objects.filter(doctor_id=doctor_id,date=dates),many=True).data
                for itm in data:
                    print("dlete")
                    removed_data = DoctorAddedTimeSlots.objects.filter(doctor_id = itm['doctor_id'], date = itm['date']).exclude(slot__in = request.data['slots']).values_list('slot', flat=True)
                    for remove in removed_data:
                        time_slot = Timeslots.objects.get(id = remove).time_slots.split(" - ")[0].replace(" ", "")
                        JuniorDoctorSlots.objects.get(doctor_id = doctor_id,date = dates,time_slot = time_slot).delete()
                    DoctorAddedTimeSlots.objects.filter(doctor_id=itm['doctor_id'],date=itm['date']).delete()
                    print("deleted")
            
            for slot in slots:
                print("slots")
                DoctorAddedTimeSlots.objects.create(doctor_id=doctor_id,slot=slot,date=dates)
                time_slot = Timeslots.objects.get(id = slot).time_slots.split(" - ")[0].replace(" ", "")
                try:
                    JuniorDoctorSlots.objects.get(doctor_id = doctor_id,date = dates,time_slot = time_slot)
                except Exception as e:
                    print(e)
                    JuniorDoctorSlots.objects.create(doctor_id = doctor_id, date = dates, time_slot = time_slot)
        else:
            if DoctorAddedTimeSlots.objects.filter(doctor_id=doctor_id,date=dates).count() > 0:
                print("doctor slots > 0 ")
                data=DoctorAddedTimeSlotsSerializer(DoctorAddedTimeSlots.objects.filter(doctor_id=doctor_id,date=dates),many=True).data
                for itm in data:
                    print("dlete")
                    DoctorAddedTimeSlots.objects.filter(doctor_id=itm['doctor_id'],date=itm['date']).delete()
                    print("deleted")
            for slot in slots:
                print("slots")
                DoctorAddedTimeSlots.objects.create(doctor_id=doctor_id,slot=slot,date=dates)

            if SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=dates).count() >0:
                SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=dates).delete()

            
            for slot in slots:
                print("slots")
                DoctorAddedTimeSlots.objects.create(doctor_id=doctor_id,slot=slot,date=dates)
                time_slot = Timeslots.objects.get(id = slot).time_slots.split(" - ")[0].replace(" ", "")
                try:
                    SeniorDoctorAvailableTimeSLots.objects.get(doctor_id = doctor_id,date = dates,time_slot = time_slot)
                except Exception as e:
                    print(e)
                    doctor = DoctorProfiles.objects.get(user_id = doctor_id).doctor_profile_id
                    duration = Duration.objects.get(doctor_id = doctor).duration
                    start_time = datetime.datetime.strptime(time_slot, "%I:%M%p")
                    end_time = start_time + timedelta(minutes=int(duration))
                    end_time_str = end_time.strftime("%I:%M%p")
                    SeniorDoctorAvailableTimeSLots.objects.create(doctor_id=doctor_id,\
                                                                time_slot=time_slot,date=dates,end_time=end_time_str)

    else:

        DoctorCalenderUpdate.objects.filter(doctor_id=doctor_id,date=dates).delete()
        DoctorAvailableDates.objects.filter(doctor_id=doctor_id,date=dates).delete()
        if flag =="junior":
            if DoctorAddedTimeSlots.objects.filter(doctor_id=doctor_id,date=dates).count() > 0:
                print("doctor slots > 0 ")
                data=DoctorAddedTimeSlotsSerializer(DoctorAddedTimeSlots.objects.filter(doctor_id=doctor_id,date=dates),many=True).data
                for itm in data:
                    print("dlete")
                    DoctorAddedTimeSlots.objects.filter(doctor_id=itm['doctor_id'],date=itm['date']).delete()
                    print("deleted")
        else:
            if DoctorAddedTimeSlots.objects.filter(doctor_id=doctor_id,date=dates).count() > 0:
                print("doctor slots > 0 ")
                data=DoctorAddedTimeSlotsSerializer(DoctorAddedTimeSlots.objects.filter(doctor_id=doctor_id,date=dates),many=True).data
                for itm in data:
                    print("dlete")
                    DoctorAddedTimeSlots.objects.filter(doctor_id=itm['doctor_id'],date=itm['date']).delete()
                    print("deleted")
            print("delete previously added timeslots")
            if SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=dates).count() >0:
                SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=dates).delete()
                add_Senior_timeslots(request)

    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':'Doctor Calender Updated',
        'data':weekday
    })



@api_view(['POST'])
def working_hour_view(request):
    doctor_weekdays=request.data['days']
    slots=request.data['slots']
    doctor_id=request.data['doctor_id']
    current_date=datetime.datetime.today().date()
    four_weeks_date=current_date+timedelta(weeks=4)
    print("4 weeks date",four_weeks_date)
    print("current_date",current_date)
    for single_date in daterange(current_date,four_weeks_date):
        date=single_date.strftime("%Y-%m-%d-%A")
        print("dates-weekday",date)
        for d in doctor_weekdays:
            find=date.find(d)
            if find != -1:
                dates=single_date.strftime("%Y-%m-%d")
                weekday=single_date.strftime("%A")
                print("DATES & WEEKDAY",dates,weekday)
                doctor=DoctorAvailableDates.objects.filter(doctor_id=doctor_id,date=dates)
                if doctor:
                    DoctorAvailableDates.objects.filter(doctor_id=doctor_id,date=dates).update(doctor_id=doctor_id,date=dates,day=weekday)
                else:
                    DoctorAvailableDates.objects.create(doctor_id=doctor_id,date=dates,day=weekday)
    for item in slots :
        if item['timeslots']!="" and item["timeslots"]!=[]:
            print(min(item['timeslots']),max(item['timeslots']))
            slot_update(doctor_id,weekday=item['day'],
            slot_from=min(item['timeslots']),slot_to=max(item['timeslots']))

    return Response({
        "response_code":200,
        "status":"OK",
        'message':"Working Hours Updated"
    })

def get_doctor_flag(request):
    try:
        doctor=DoctorProfiles.objects.get(user_id=request.data['doctor_id'])
        flag=doctor.doctor_flag
        specialization=doctor.specialization
    except Exception as e:
        print(e)
        flag=None
        specialization=None
    return flag,specialization

def starting_time_slots(start_time, end_time, duration):
    start = datetime.datetime.strptime(str(start_time), "%H:%M:%S")
    end = datetime.datetime.strptime(str(end_time), "%H:%M:%S")
    delta = timedelta(minutes=duration)
    slots = []
    while start + delta <= end:
        slot = start.strftime("%I:%M%p") 
        slots.append(slot)
        start += delta
    return slots

def convert_time(time_str):
    # Add a space before the AM/PM marker if necessary
    if 'AM' in time_str or 'PM' in time_str:
        time_str = time_str[:-2] + ':00 ' + time_str[-2:]

    # Convert the time string to a datetime object
    

    # Format the time as 'HH:MM:SS'
    return time_str

def add_duration_timeslots(specialization,slots,doctor_id,date,flag):
    print('2431 ')
    print(specialization,slots,doctor_id,date,flag)
    try:
        try:
            doctor = DoctorProfiles.objects.get(user_id = doctor_id).doctor_profile_id
            duration = Duration.objects.get(doctor_id=doctor).duration
        except:
            duration=60
        time_slots_available= TimeSlotSerializer(
        Timeslots.objects.filter(id__in=slots), many=True ).data
        print(time_slots_available,"slots available",duration)
        all_timeslots=[]
        for data in time_slots_available:
            print(data['time_slots'])
            start_time_str = data['time_slots'].split('-')[0].strip()
            end_time_str = data['time_slots'].split('-')[1].strip()
            print(start_time_str)
            print(end_time_str)
            start_time = datetime.datetime.strptime(start_time_str, '%I:%M %p').time()
            end_time=datetime.datetime.strptime(end_time_str, '%I:%M %p').time()
            print("starttime",start_time,"endtime",end_time,duration)
            print("duration",duration)
            calculated_list=list(starting_time_slots(start_time, end_time, duration))
            print(calculated_list)
            all_timeslots.extend(calculated_list)
        print(all_timeslots)
 
        for time_slot in all_timeslots:
            print("JUnior doc timeslot")
            print(time_slot)
            if flag == 'junior':
                JuniorDoctorSlots.objects.create(doctor_id=doctor_id,\
                                                            time_slot=time_slot,date=date)
            else:
                doctor = DoctorProfiles.objects.get(user_id = doctor_id).doctor_profile_id
                duration = Duration.objects.get(doctor_id = doctor).duration
                start_time = datetime.datetime.strptime(time_slot, "%I:%M%p")
                end_time = start_time + timedelta(minutes=int(duration))
                end_time_str = end_time.strftime("%I:%M%p")
                SeniorDoctorAvailableTimeSLots.objects.create(doctor_id=doctor_id,\
                                                            time_slot=time_slot,date=date,end_time=end_time_str)
    except Exception as e:
        print(e)

def add_duration_timeslots2(specialization,slots,doctor_id,date,flag):
    print('2541 ')
    print(specialization,slots,doctor_id,date,flag)
    try:
        try:
            if flag == 'junior':
                user = User.objects.get(first_name = 'junior', last_name = 'doctor').id
                doctor = DoctorProfiles.objects.get(user_id = user).doctor_profile_id
                duration=Duration.objects.get(doctor_id=doctor).duration
            else:
                doctor = DoctorProfiles.objects.get(user_id = doctor_id).doctor_profile_id
                duration=Duration.objects.get(doctor_id=doctor).duration
        except Exception as e:
            print(e)
            duration=60
        time_slots_available= TimeSlotSerializer(
        Timeslots.objects.filter(id__in=slots), many=True ).data
        print(time_slots_available,"slots available",duration)
        all_timeslots=[]
        for data in time_slots_available:
            print(data['time_slots'])
            start_time_str = data['time_slots'].split('-')[0].strip()
            end_time_str = data['time_slots'].split('-')[1].strip()
            print(start_time_str)
            print(end_time_str)
            start_time = datetime.datetime.strptime(start_time_str, '%I:%M %p').time()
            end_time=datetime.datetime.strptime(end_time_str, '%I:%M %p').time()
            print("starttime",start_time,"endtime",end_time,duration)
            print("duration",duration)
            calculated_list=list(starting_time_slots(start_time, end_time, duration))
            print(calculated_list)
            all_timeslots.extend(calculated_list)
        print(all_timeslots)
 
        for time_slot in all_timeslots:
            print("JUnior doc timeslot")
            print(time_slot)
            if flag == 'junior':
                JuniorDoctorSlots.objects.create(doctor_id=doctor_id,\
                                                            time_slot=time_slot,date=date)
            else:
                doctor = DoctorProfiles.objects.get(user_id = doctor_id).doctor_profile_id
                duration = Duration.objects.get(doctor_id = doctor).duration
                start_time = datetime.datetime.strptime(time_slot, "%I:%M%p")
                end_time = start_time + timedelta(minutes=int(duration))
                end_time_str = end_time.strftime("%I:%M%p")
                SeniorDoctorAvailableTimeSLots.objects.create(doctor_id=doctor_id,\
                                                            time_slot=time_slot,date=date, end_time = end_time_str)
    except Exception as e:
        print(e)


@api_view(['POST'])
def calender_add_view(request):
    print("*******calender-add slots function*******")
    slots=request.data['slots']
    doctor_id=request.data['doctor_id']
    flag,specialization=get_doctor_flag(request)
    dates=request.data['date']
    calculated_list=[]
    print("data",request.data,flag,specialization)
    weekday=(datetime.datetime.strptime(dates,"%Y-%m-%d")).strftime("%A")
    print('2499 ',dates)
    print("weekday", weekday)
    try:
        print("try block")
        doctor=DoctorCalenderUpdate.objects.get(doctor_id=doctor_id,date=dates)
    except Exception as e :
        print(e,"except doctorcalender except block")
        doctor=None
    if slots!="" and slots!=[] :
        print(min(slots),max(slots))
        if doctor==None:
            print("doctor does not exist")
            DoctorCalenderUpdate.objects.create(doctor_id=doctor_id,day=weekday,date=dates,
                 time_slot_from=min(slots),time_slot_to=max(slots))
            DoctorAvailableDates.objects.create(doctor_id=doctor_id,date=dates,day=weekday)
            if flag == "junior":
                print("junior")
                for slot in slots:
                    print('slots',slot,dates)
                    DoctorAddedTimeSlots.objects.create(doctor_id=doctor_id,slot=slot,date=dates)
                add_duration_timeslots2("no specialization",slots,doctor_id,dates,flag)
            else:
                print("senior doctor")
                for slot in slots:
                    DoctorAddedTimeSlots.objects.create(doctor_id=doctor_id,slot=slot,date=dates)
                if len(slots) !=0:
                    
                    add_duration_timeslots(specialization,slots,doctor_id,dates,flag)
                    
    if slots!="" and slots!=[] :
        print(min(slots),max(slots))
        slot_update(doctor_id,weekday=weekday,slot_from=min(slots),slot_to=max(slots))

    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':'Doctor Calender Updated',
        'data':weekday
    })



@api_view(['POST'])
def appointment_close_view(request):
    """"Payouts Calculation"""
    appointment_id=request.data['appointment_id']
    appointment_status=request.data['appointment_status']
    specialization=request.data['specialization']
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':'Booking Closed, Payout Added',
    })

"""View for Detailed Api"""
@api_view(['POST'])
def appointment_detail_view(request):
    print('2824 ',request.data)
    try:
       queryset=[]
       if 'appointment_id' in request.data and request.data['appointment_id'] !="":
           queryset=AppointmentHeader.objects.get(pk=request.data['appointment_id'])
       if 'encrypted_appointment_id' in request.data and request.data['encrypted_appointment_id'] !="":
           appointment_id=encryption_key.decrypt(request.data['encrypted_appointment_id']).decode()
           queryset=AppointmentHeader.objects.get(pk=appointment_id)
       appointment_data = AppointmentHeaderSerializer(queryset).data
       common_detail=3
       transfered_doctor=None
    #    print(common_detail)
       print(appointment_data,"try")
       if 'doctor_id' in request.data and request.data['doctor_id']!="":
           try:
              transfered_doctor=AppointmentTransferHistory.objects.get(old_doctor=request.data['doctor_id'],
              appointment_id=appointment_data['appointment_id'])
           except Exception as e :
               print(e)
               transfered_doctor=None
        #    print("appointment transfer history",transfered_doctor)
           appointment_data['specialization']=get_doctor_specialization(request.data['doctor_id'])
       user_id=appointment_data['user_id']
       cat_id=appointment_data['category_id']
       appointment_data['is_free']=appointment_data['is_free']
       appointment_data['followup_id']=appointment_data['followup_id']
       appointment_data['type_booking']=appointment_data['type_booking']
       appoint_status=appointment_data['appointment_status']
       appointment_data['time_slot']=appointment_data['appointment_time_slot_id']
       print("here")
    #    print(appointment_data)
       junior_doc_id=DoctorMapping.objects.filter(appointment_id=appointment_data['appointment_id'],
         doctor_flag="junior").values_list('mapped_doctor',flat=True)
       senior_doc_id=DoctorMapping.objects.filter(appointment_id=appointment_data['appointment_id'],
         doctor_flag="senior").values_list('mapped_doctor',flat=True)
       print(junior_doc_id,senior_doc_id)
       try:
        appointment_data['invoice_id'] = Invoices.objects.filter(
                appointment_id=appointment_data['appointment_id']
            ).first().invoice_id
        print('2861 ',appointment_data['invoice_id'])
       except Exception as e:
           print("invoice_id_except",e)
           appointment_data['invoice_id']=""
       try:
           print(appointment_data['junior_doctor'])
           appointment_data['doc_name_junior']=get_users_name(appointment_data['junior_doctor'])
           'ss'
       except Exception as e:
            print("doc-name-",e)
            appointment_data['doc_name_junior']=""
       try:
            appointment_data['doc_name_senior']=get_users_name(appointment_data['senior_doctor'])
            print('2874 ',appointment_data['doc_name_senior'])
            try:
              added_doc_id = DoctorMapping.objects.filter(
                    added_doctor=0,
                    appointment_id=appointment_data['appointment_id']
                ).last()

              if added_doc_id:
                  mapped_doctor = added_doc_id.mapped_doctor
              else:
                  mapped_doctor = None
              print('2778',mapped_doctor)
              appointment_data["added_doctor"]=get_users_name(mapped_doctor)
            except Exception as e:
              print("added_doc",e)
              appointment_data["added_doctor"]=None
       except:
            appointment_data['doc_name_senior']=""
       appointment_data['category']=get_category_name(cat_id)
       'ss'
     
       appointment_data['appointment_status']= appoint_status
       print('2787', user_id)
    #    print(appointment_data)
       queryset_user=User.objects.get(id=user_id)
       print(vars(queryset_user),"user")
       if user_id !=1:
          queryset_customer=CustomerProfile.objects.get(user_id=user_id)
          appointment_data['cust_dob']=queryset_customer.date_of_birth
          appointment_data['cust_mobile_num']=queryset_customer.mobile_number
          appointment_data['cust_gender']=queryset_customer.gender
          appointment_data['cust_oth_gender']=queryset_customer.other_gender
          appointment_data['cust_age']=queryset_customer.age
          appointment_data['location'] = queryset_customer.location
       else:
          appointment_data['cust_dob']="1998-12-25"
          appointment_data['cust_mobile_num']="9099882200"
       appointment_data['user_mail']=queryset_user.email
       appointment_data['user_fname']=queryset_user.first_name
       appointment_data['user_lname']=queryset_user.last_name
       appointment_question_data = AppointmentQuestionsSerializer(
            AppointmentQuestions.objects.filter(appointment_id=appointment_data['appointment_id']), many=True).data
       for question in appointment_question_data:
            question['answers'] = AppointmentAnswersSerializer(
                AppointmentAnswers.objects.filter(appointment_questions_id=question['appointment_questions_id']),
                many=True).data
       appointment_data['questions'] = appointment_question_data
    #    print(appointment_data,appointment_question_data)
       try:
        reschedule=AppointmentReshedule.objects.get(appointment_id=appointment_data['appointment_id'])
        appointment_data['rescheduled_time']=reschedule.time_slot
        appointment_data['rescheduled_date']=reschedule.rescheduled_date
        appointment_data['rescheduled_count']=reschedule.reschedule_count
        appointment_data['reschedule_limit']=common_detail
        appointment_data['sr_rescheduled_time']=reschedule.sr_rescheduled_time
        appointment_data['sr_rescheduled_date']=reschedule.sr_rescheduled_date
       except Exception as e:
           print('except',e)
           appointment_data['rescheduled_time']=''
           appointment_data['rescheduled_date']=''
           appointment_data['rescheduled_count']=''
           appointment_data['reschedule_limit']=common_detail
           appointment_data['sr_rescheduled_time']=''
           appointment_data['sr_rescheduled_date']=''
       if transfered_doctor:
          print(transfered_doctor)
          observations= ObservationsSerializer(
            Obeservations.objects.filter(
            appointment_id=appointment_data['appointment_id'],doctor_id=request.data['doctor_id']),
            many=True).data
          appointment_data['observations']=observations
       else:
          observations= ObservationsSerializer(
            Obeservations.objects.filter(appointment_id=appointment_data['appointment_id']),
            many=True).data
          appointment_data['observations']=observations

       for doctor in observations:
           print("observation_detail")
           try:
               doctor['doctor_name']=get_users_name(doctor['doctor_id'])
           except Exception as e:
               print(e)
               doctor['doctor_name']=""

      
       analysis_information=AnalysisInfoSerializer(
        AnalysisInfo.objects.filter(appointment_id=appointment_data['appointment_id']),
        many=True).data
       appointment_data['analysis_info']=analysis_information
       for doctor in analysis_information:
           print("analysis_detail")
           try:
               doctor['doctor_name']=get_users_name(doctor['doctor_id'])
           except Exception as e:
               print("doc_user_except",e)
               doctor['doctor_name']=""

       prescript= PrescriptionSerializer(
        Prescriptions.objects.filter(appointment_id=appointment_data['appointment_id']),
        many=True).data
       appointment_data['prescriptions']=prescript

       if transfered_doctor:
           prescript_text=PrescriptionTextSerializer(
           PrescriptionsDetail.objects.filter(
               appointment_id=appointment_data['appointment_id'],doctor_id=request.data['doctor_id']),many=True).data

           for prescriptions in prescript_text:
                medicines=MedicationsSerializer(Medications.objects.filter(
                prescription_id=prescriptions['id']),many=True).data
                prescriptions['medicines']=medicines
                try:

                   prescriptions['qualification']=DoctorProfiles.objects.filter(
                    user_id=prescriptions['doctor_id']).qualification
                   prescriptions['address']=DoctorProfiles.objects.filter(
                    user_id=prescriptions['doctor_id']).address
                except Exception as e:
                    print(e)
                    prescriptions['qualification']=""
                    prescriptions['address']=""
                for consumption in medicines:
                    consumption['consumption_time']=ConsumptionTime.objects.filter(
                        medication_id=consumption['medication_id']).values_list('consumption_time',flat=True)
           appointment_data['prescript_text']=prescript_text
       else:
           print("else")
           prescript_text=PrescriptionTextSerializer(
           PrescriptionsDetail.objects.filter(appointment_id=appointment_data['appointment_id']),many=True).data
           for prescriptions in prescript_text:
                medicines=MedicationsSerializer(Medications.objects.filter(
                prescription_id=prescriptions['id']),many=True).data
                prescriptions['medicines']=medicines
                try:

                   prescriptions['qualification']=DoctorProfiles.objects.filter(
                    user_id=prescriptions['doctor_id']).qualification
                   prescriptions['address']=DoctorProfiles.objects.filter(
                    user_id=prescriptions['doctor_id']).address
                except Exception as e:
                    print(e)
                    prescriptions['qualification']=""
                    prescriptions['address']=""

                for consumption in medicines:
                    consumption['consumption_time']=ConsumptionTime.objects.filter(
                        medication_id=consumption['medication_id']).values_list('consumption_time',flat=True)
           appointment_data['prescript_text']=prescript_text

       for doctor in prescript_text:
        #    appointment_id=doctor['appointment_id']
           print("prescription_detail")
           try:
               doctor['doctor_name']=get_users_name(doctor['doctor_id'])
           except Exception as e:
               print("except",e)
               doctor['doctor_name']=""
        #    try:
        #       prescription=PrescriptionsDetail.objects.get(appointment_id=appointment_data['appointment_id'])
        #       doctor['prescription_create_time']=prescription.uploaded_time
        #       doctor['prescription_create_date']=prescription.uploaded_date
        #    except Exception as e:
        #        print("except",e)
        #        doctor['prescription_create_time']=""
        #        doctor['prescription_create_date']=""
       followup=AppointmentHeaderSerializer(
            AppointmentHeader.objects.filter(followup_id=appointment_data['appointment_id']),many=True).data

       for users in followup:
           print("followup_detail")
           doctors_names = []
           doctors_names.append(get_users_name(users['senior_doctor']))
           follow_up_doc_ids = DoctorMapping.objects.filter(
            appointment_id=appointment_data['appointment_id']).values_list('mapped_doctor',flat=True)
           for followup_doc in follow_up_doc_ids:
                doctors_names.append(get_users_name(followup_doc))
        #    print(doctors_names)
           users['doctors_names'] = doctors_names
           if users['followup_created_by'] == 'user':
                users['create_by_user_name'] = get_users_name(user_id)
           elif users['followup_created_by'] == 'doctor':
                users['create_by_user_name'] = get_users_name(users['senior_doctor'])
           else:
                users['create_by_user_name'] = ""

           try:
               invoice_followup=Invoices.objects.get(appointment_id=appointment_data['appointment_id'])
               users['invoice_id_followup']=invoice_followup.invoice_id
               users['invoice_status_followup']=invoice_followup.status
           except Exception as e:
                print("followup_invoice_except",e)
                users['invoice_id_followup']=""
                users['invoice_status_followup']=""
           users['time_slot']=users['appointment_time_slot_id']

       appointment_data['followup'] = followup
    #    common_files=CommonFileUploaderSerializer(CommonFileUploader.objects.filter(
    #     appointment_id=request.data['appointment_id'],file_flag=request.data['file_flag']),many=True).data
    #    appointment_data['common_files']=common_files
       try:
            queryset_invoice=Invoices.objects.get(appointment_id=appointment_data['appointment_id'])
            appointment_data['invoice_status']=queryset_invoice.status
       except:
            appointment_data['invoice_status']=""
    #    time_slot=TimeSlotSerializer(
    #         Timeslots.objects.all(),many=True).data
       if ReportCustomer.objects.filter(appointment_id=appointment_data['appointment_id']).exists():
           appointment_data['is_reported'] = 1
       else:
           appointment_data['is_reported'] = 0
       try:
        appointment_data["reported_count"]=ReportCustomer.objects.get(appointment_id=appointment_data['appointment_id']).report_count
       except:
        appointment_data["reported_count"]=0
        appointment_data['patient_medical_history']=get_patient_medical_details(user_id,appointment_data['appointment_id'])
    except Exception as e:
        print('except_detail',e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Appointment id doesnot exist"
    })
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'data':appointment_data,
    })

def get_user_id(appointment_id):
    try:
        user_id=AppointmentHeader.objects.get(appointment_id=appointment_id).user_id
    except Exception as e :
        print("exception in getting user id",e)
        user_id=0
    return user_id

@api_view(['POST'])
def appointment_patient_history(request):
    print('3005')
    print(request.data)
    if int(request.data['height']) < 20:
        request.data['height_unit'] = 'ft'
    else:
        request.data['height_unit'] = 'cm'
    user_id=get_user_id(request.data['appointment_id'])
    data={"doctor_id":request.data['doctor_id'],"doctor_flag":request.data['doctor_flag'],"appointment_id":request.data['appointment_id'],
            "user_id":get_user_id(request.data['appointment_id']),"height":request.data['height'],
            "weight":request.data['weight'],"is_allergic":request.data['is_allergic'], "medical_history":request.data['medical_history'],
            "prescription_history":request.data['prescription_history'],"other_suppliments_history":request.data['other_suppliments_history'],
            'height_unit':request.data['height_unit']
            }
    try:
        PatientMedicalHistory.objects.update_or_create(user_id=user_id,defaults=data)
    except Exception as e:
        # print("exception occured",e)
        pass
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':"Patient History Saved",
    })

"""Rescheduling an appointment"""
@api_view(['POST'])
def appointment_schedule_view(request):
    print("HITTTTT")
    print(request.data)
    # print(request.data['appointment_status'])

    request.data['appointment_status'] = AppointmentHeader.objects.get(pk=request.data['appointment_id']).appointment_status
    doctor_id = request.data['doctor_id']
    doc_flag = request.data['doctor_flag']
    rescheduled_date = request.data['appointment_date']
    appointment_id = request.data['appointment_id']
    if AppointmentHeader.objects.get(pk = request.data['appointment_id']).escalated_date == None and AppointmentHeader.objects.get(pk = request.data['appointment_id']).escalated_time_slot == None:
        oldest_data = AppointmentHeader.objects.get(pk = request.data['appointment_id']).appointment_date
        oldest_time = AppointmentHeader.objects.get(pk = request.data['appointment_id']).appointment_time_slot_id
    else:
        oldest_data = AppointmentHeader.objects.get(pk = request.data['appointment_id']).escalated_date
        oldest_time = AppointmentHeader.objects.get(pk = request.data['appointment_id']).escalated_time_slot
    
    flag = 0
    time_slot = request.data['appointment_time']

    """ get doctor flag if doc_flag is 0"""
    if doc_flag == 0:
        doc_flag, doctor_id = get_doc_flag(appointment_id)
        print("customer request", doc_flag, doctor_id)
    if flag == 0:
        print(doc_flag, "doctor_flag")
        if doc_flag == "senior":
            RescheduleHistory.objects.create(
                appointment_id=appointment_id,
                user_id=request.data['user_id'],
                doctor_id=doctor_id,
                sr_rescheduled_date=rescheduled_date,
                sr_rescheduled_time=time_slot)
            print("----------")
        if doc_flag == "junior":
            print("create else")
            RescheduleHistory.objects.create(
                appointment_id=appointment_id,
                user_id=request.data['user_id'],
                rescheduled_date=rescheduled_date,
                time_slot=time_slot,
                doctor_id=doctor_id)
        try:
            appointment_id_schedule = AppointmentReshedule.objects.get(appointment_id=appointment_id)
            count = appointment_id_schedule.reschedule_count
            print(appointment_id_schedule.reschedule_count)
        except Exception as e:
            # print("Exception", e)
            appointment_id_schedule = None
            count = 0
        if appointment_id_schedule:
            count += 1
            if doc_flag == "senior":
                print("flag is 1")
                AppointmentReshedule.objects.filter(appointment_id=appointment_id).update(
                    user_id=request.data['user_id'], appointment_id=appointment_id,
                    sr_rescheduled_date=rescheduled_date, sr_rescheduled_time=time_slot, reschedule_count=count)
            if doc_flag == "junior":
                print("jr flag")
                AppointmentReshedule.objects.filter(appointment_id=appointment_id).update(
                    user_id=request.data['user_id'], appointment_id=appointment_id,
                    rescheduled_date=rescheduled_date, time_slot=time_slot, reschedule_count=count)
            AppointmentHeader.objects.filter(
                appointment_id=appointment_id).update(appointment_status=request.data['appointment_status'])
        else:
            count += 1
            if doc_flag == "senior":
                print("sr flag")
                AppointmentReshedule.objects.create(
                    appointment_id=appointment_id, user_id=request.data['user_id'],
                    sr_rescheduled_date=rescheduled_date, sr_rescheduled_time=time_slot, reschedule_count=count)
                
            if doc_flag == 'junior':
                print("jr flag")
                AppointmentReshedule.objects.create(
                    appointment_id=appointment_id, user_id=request.data['user_id'],
                    rescheduled_date=rescheduled_date, time_slot=time_slot, reschedule_count=count)

        AppointmentHeader.objects.filter(
            appointment_id=appointment_id).update(appointment_status=request.data['appointment_status'])
        if request.data['appointment_status'] == 4:
            print("email-cust")
            subject = 'Order Rescheduled'
            html_message = render_to_string('order_reschedule.html', {'appointment_date': rescheduled_date,
                                                                     'appointment_time': time_slot, 'doctor_flag': 0,
                                                                     'email': get_user_mail(
                                                                         AppointmentHeader.objects.get(
                                                                             appointment_id=appointment_id).user_id)})
            plain_message = strip_tags(html_message)
            from_email = 'wecare@inticure.com'
            cc = 'nextbighealthcare@inticure.com'
            to = get_users_email(request.data['user_id'])
            try:
                sms_service.send_message(
                    "Hi There, Your Appointment #%s has been rescheduled to:%s,%s Please refer mail for more details"
                    % (appointment_id, rescheduled_date, time_slot),
                    "+91" + str(CustomerProfile.objects.get(user_id=request.data['user_id']).mobile_number))
            except Exception as e:
                print(e)
                print("MESSAGE SENT ERROR")

            mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)

        if request.data['appointment_status'] == 7:
            print("email-doc")
            subject=""
            try:
                subject = 'Order Rescheduled'
                html_message = render_to_string(
                    'order_reschedule.html', {'appointment_date': rescheduled_date,
                                            'appointment_time': time_slot, 'doctor_flag': 1,
                                            'email': get_users_name(doctor_id)})
                                               # get_user_mail(doctor_id)})
                plain_message = strip_tags(html_message)
                from_email = 'wecare@inticure.com'
                to = get_users_email(doctor_id)
                cc = 'nextbighealthcare@inticure.com'
                #to = "gopika197.en@gmail.com"
                mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)
            
                sms_service.send_message(
                    "Hi There, Your Appointment #%s has been rescheduled to:%s,%s Please refer mail for more details"
                    % (appointment_id, rescheduled_date, time_slot),
                    "+91" + str(CustomerProfile.objects.get(user_id=request.data['user_id']).mobile_number))
            except Exception as e:
                print(e)
                print("MESSAGE SENT ERROR")
                
            try:
                subject = 'Order Rescheduled'
                html_message = render_to_string('order_reschedule.html', {'appointment_date': rescheduled_date,
                                                                        'appointment_time': time_slot, 'doctor_flag': 0,
                                                                        'email': get_users_name(AppointmentHeader.objects.get(
                                                                                appointment_id=appointment_id).user_id)})
                                                                            # get_user_mail(
                                                                            # AppointmentHeader.objects.get(
                                                                            #     appointment_id=appointment_id).user_id)})
                plain_message = strip_tags(html_message)
                from_email = 'wecare@inticure.com'
                to = get_users_email(request.data['user_id'])
                cc = "nextbighealthcare@inticure.com"
                #to = "gopika197.en@gmail.com"
                # try:
                #     sms_service.send_message(
                #         "Hi There, Your Appointment #%s has been rescheduled to:%s,%s Please refer mail for more details"
                #         % (appointment_id, rescheduled_date, time_slot),
                #         "+91" + str(CustomerProfile.objects.get(user_id=request.data['user_id']).mobile_number))
                # except Exception as e:
                #     print(e)
                #     print("MESSAGE SENT ERROR")
            except Exception as e:
                print(e)
            cc ='nextbighealthcare@inticure.com'
            mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)

        # if request.data['appointment_status'] == 5:
        #     print("email-doc")
        #     subject = 'Order Rescheduled'
        #     html_message = render_to_string('order_reschedule.html', {'appointment_date': rescheduled_date,
        #                                                              'appointment_time': time_slot, 'doctor_flag': 1,
        #                                                              'email': get_user_mail(doctor_id)})
        #     plain_message = strip_tags(html_message)
        #     from_email = 'Inticure <hello@inticure.com>'
        #     to = get_users_email(doctor_id)
        #     mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)
        #     try:
        #         sms_service.send_message(
        #             "Hi There, Your Appointment #%s has been rescheduled to:%s,%s Please refer mail for more details"
        #             % (appointment_id, rescheduled_date, time_slot),
        #             "+91" + str(CustomerProfile.objects.get(user_id=request.data['user_id']).mobile_number))
        #     except Exception as e:
        #         print(e)
        #         print("MESSAGE SENT ERROR")
        try:
            specialization=DoctorProfiles.objects.get(user_id=doctor_id).specialization
        except:
            specialization=None
        doctor_email = get_user_mail(doctor_id)
        doc_id=DoctorProfiles.objects.get(user_id=doctor_id).doctor_profile_id

        user_email = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
        
        start_time, end_time = get_appointment_time(request.data['appointment_time'], rescheduled_date,specialization,doc_flag,doctor_id=doc_id)
        meet_link = generate_google_meet("Inticure,Doctor Appointment", "",
                                         [{"email": user_email}, {"email": doctor_email}], start_time,
                                         end_time)
        print('3564', doc_flag)
        print(oldest_data, oldest_time)
        if doc_flag == 'senior':
            print(doctor_id, rescheduled_date, time_slot)
            if AppointmentHeader.objects.get(pk = request.data['appointment_id']).escalated_date == None and AppointmentHeader.objects.get(pk = request.data['appointment_id']).escalated_time_slot == None:
                AppointmentHeader.objects.filter(appointment_id=appointment_id).update(appointment_time_slot_id=time_slot, appointment_date = rescheduled_date, senior_meeting_link=meet_link)
            else:
                AppointmentHeader.objects.filter(appointment_id=appointment_id).update(escalated_time_slot=time_slot, escalated_date = rescheduled_date, senior_meeting_link=meet_link)

            SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=rescheduled_date,time_slot=time_slot).update(is_active=1)
            SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=oldest_data,time_slot=oldest_time).update(is_active=0)
            
        else:
            print(doctor_id, request.data['appointment_time'], rescheduled_date)
            AppointmentHeader.objects.filter(appointment_id=appointment_id).update(appointment_date = rescheduled_date, appointment_time_slot_id = time_slot, meeting_link=meet_link)
            JuniorDoctorSlots.objects.filter(doctor_id=doctor_id,time_slot=request.data['appointment_time'],date=rescheduled_date).update(is_active=1)
            JuniorDoctorSlots.objects.filter(doctor_id=doctor_id,time_slot=oldest_time,date=oldest_data).update(is_active=0)
        
        return Response({
            'response_code': 200,
            'status': 'Ok',
            'message': "Appointment Re-Scheduled"
        })
    return Response({
        'response_code': 400,
        'status': 'Ok',
        'message': "Time Slot not Available"
    })
