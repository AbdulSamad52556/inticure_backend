import random,math,stripe
from datetime import datetime,date
from re import template
import re
from sys import flags
from django.http import Http404

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils.html import strip_tags
from django.core import mail    
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template.loader import get_template

from rest_framework import viewsets, status, permissions, views
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

from .models import Category, Questionnaire, Options, AppointmentHeader, AppointmentQuestions, \
    AppointmentAnswers,Options,Invoices,OtpVerify,AnswerType,EmailOtpVerify
from administrator.models import Plans,Locations,DiscountCoupons,CouponRedeemLog,Transactions, Duration
from conf_files.google_meet import generate_google_meet
from doctor.models import Timeslots,DoctorProfiles,SrDoctorEngagement,JrDoctorEngagement,DoctorMapping,\
    DoctorAvailableDates,DoctorAvailableTimeslots,DoctorLanguages,DoctorCalenderUpdate,\
        SeniorDoctorAvailableTimeSLots,JuniorDoctorSlots,SeniorDoctorAvailableTimeSLots, EscalatedAppointment
from .serializers import CategorySerializer, QuestionnaireSerializer,OptionsSerializer,InvoicesSerializer,\
    AnswerTypeSerializer
from doctor.serializer import TimeSlotSerializer
from customer.models import CustomerProfile,StripeCustomer,TemporaryTransactionData
from common.filter import custom_filter
from common.views import encryption_key
# Create your views here.
from doctor.views import get_user_mail,get_users_name,time_in_range,get_slot_time,get_doctor_specialization
from common.twilio_test import MessageClient
from twilio.rest import Client
from django.conf import settings
from common.views import get_category_name,get_appointment_time

from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

sms_service=MessageClient()


def send_whatsapp_message(to, body):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=body,
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=f'whatsapp:{to}'
    )
    return message

def get_doctor_bio(id):
    try:
        doc=DoctorProfiles.objects.get(user_id=id)
        bio=doc.doctor_bio
        profile=doc.profile_pic
    except Exception as e:
        print(e)
        bio="Bio is not available"
        profile=None
    return bio,profile

def get_currency(location_id):
    print("currency",location_id)
    try:
        currency=Locations.objects.get(location_id=location_id).currency
    except Exception as e:
        print("locations excpetion",e)
        currency='inr'
    return currency

def get_duration(doctor_id):
    try:
        duration = Duration.objects.get(doctor_id = doctor_id).duration
    except Exception as e:
        duration = 0
    return duration 

def get_doctor_location(doctor_id):
    try:
        location=DoctorProfiles.objects.get(user_id=doctor_id).location
        print("doctor_ocation",location)
        # if location =='India':
        #     location_id=1
        # else:
        #     location_id=2
    except Exception as e :
        print(e)
        location=1
    return location

def assign_senior_doctor(request):
    filter={}
    if "language_pref" in request.data and request.data['language_pref'] != "":
        # filter['user_id__in']=DoctorLanguages.objects.filter(
        #     languages=request.data['language_pref']).values_list('doctor_id',flat=True)
        user_ids=DoctorLanguages.objects.filter(languages=request.data['language_pref']).values_list('doctor_id',flat=True)
        if len(user_ids) == 0:
                user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
            # filter['user_id__in']=DoctorLanguages.objects.filter(
            # languages=request.data['language_pref']).values_list('doctor_id',flat=True)
        filter['user_id__in']=user_ids
    if "gender_pref" in request.data and request.data['gender_pref'] != "":
        filter['gender']=request.data['gender_pref']
    if "specialization" in request.data and request.data['specialization'] != "":
        filter['specialization']=request.data['specialization']
    filter['doctor_flag']="senior"
    
    if  "doctor_id" in request.data and request.data['doctor_id']!="" and request.data['doctor_id'] != 0 :
        print("doctor id is available",request.data['doctor_id'])
        doctor_id = custom_filter(DoctorProfiles, filter)
        doctor_id_list=doctor_id.exclude(user_id=request.data['doctor_id']).values_list('user_id',flat=True)
    else:
        doctor_id_list = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
    print("languase",filter['user_id__in'])    
    print("first-filtered",doctor_id_list)
    appointment_date_=datetime.strptime(request.data['appointment_date'],"%Y-%m-%d")
    weekday=appointment_date_.strftime("%A")
    try:
            doctor_id_time_slots=SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id__in=doctor_id_list,\
                date=request.data['appointment_date'],time_slot=request.data['appointment_time']).values_list('doctor_id',flat=True)
            filter['user_id__in']=doctor_id_time_slots
            doc_id = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
            print(doc_id)
            if doc_id:
                random_id=random.choice(doc_id)
                return random_id
    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Doctor Does Not Exist'},
            status=status.HTTP_400_BAD_REQUEST
        )

   

@api_view(['POST'])
def category_view(request):
    try:
        category_serialized = CategorySerializer(Category.objects.all(), many=True).data

        return Response({
            'response_code': 200,
            'status': 'Ok',
            'data': category_serialized,
        })
    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def create_category_view(request):
    try:
        category_serializer = CategorySerializer(data=request.data)
        if category_serializer.is_valid(raise_exception=True):
            category_serializer.save()
            return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': "Category created"
            })
        return Response({
            'response_code': 400,
            'status': 'Failed to create category'},
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST
        )

# """Timeslot list """
# @api_view(['POST'])
# def timeslot_view(request):
#     print("time-slot")
#     timeslot1=DoctorProfiles.objects.filter(working_date_frm__lte=request.data['appointment_date'],
#         working_date_to__gte=request.data['appointment_date'],
#         doctor_flag="junior").values_list('time_slot_from',flat=True)
#     timeslot2=DoctorProfiles.objects.filter(working_date_frm__lte=request.data['appointment_date'],
#         working_date_to__gte=request.data['appointment_date'],
#         doctor_flag="junior").values_list('time_slot_to',flat=True)
#     # timeslot_max=max(timeslot1+timeslot2)
#     # timeslot_min=min(timeslot1+timeslot2)
#     # print(timeslot1,timeslot2)
#     # timeslot_list=TimeSlotSerializer(
#     #         Timeslots.objects.filter(id__lte=timeslot_min,id__gte=timeslot_max),many=True).data 
    
#     return Response({
#             'response_code': 200,
#              'status': 'Ok',
#             #  'timeslots':timeslot_list
#              })

# def get_users_name(user_id):

#     try:
#         doc = User.objects.get(id=user_id)
#         users_name = doc.first_name + doc.last_name
#     except Exception as e:
#         print("except", e)
#         users_name = ""
#     return users_name

# def get_users_email(user_id):
#     try:
#         mail = User.objects.get(id=user_id)
#         users_mail = mail.email
#     except Exception as e:
#         print("except", e)
#         users_mail = ""
    # return users_mail

"""View to List the questions in analysis """
@api_view(['GET'])
def questionnaire_view(request):
    try:
        filter = {}
        if 'category_id' in request.query_params and request.query_params.get('category_id'):
            filter['category_id'] = request.query_params.get('category_id')
        if 'customer_gender' in request.query_params and request.query_params.get('customer_gender'):
            filter['customer_gender'] = request.query_params.get('customer_gender')
        # serializing data from questionnaire table
        questionnaire_serialized = QuestionnaireSerializer(Questionnaire.objects.filter(**filter), many=True).data
        
        for question in questionnaire_serialized:
            try:
                question['options'] = OptionsSerializer(Options.objects.filter(question_id=question['id']),
                                                        many=True).data
            except:
                question['options'] = ""
        return Response({
            'response_code': 200,
            'status': 'Ok',
            'data': questionnaire_serialized
        })
    except Exception as e:
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST)

def generateOTP():
    digits = "0123456789"
    OTP = ""
    for i in range(4):
        OTP += digits[math.floor(random.random() * 10)]
    print(OTP)
    # print(send_whatsapp_message('+917356860792', 'message vanna parayy'))
    
    return OTP
def create_user_mobile_num(mobile_number):
    user_queryset = User.objects.filter(email=mobile_number)
    if user_queryset.exists():
        return 0
    else:
        user = User.objects.create_user(username=mobile_number, password=mobile_number, email=mobile_number)
        CustomerProfile.objects.create(user_id=user.id)
    # checkout_preprocess(user.id)
    return user.id

def create_user(email,first_name,last_name):
    try:
        user_queryset = User.objects.get(email=email)
        if user_queryset:
            return user_queryset.id
        else:
            user = User.objects.create_user(username=email, password=email, email=email, first_name=first_name,
            last_name=last_name)
            CustomerProfile.objects.create(user_id=user.id)
    except:
        user = User.objects.create_user(username=email, password=email, email=email, first_name=first_name,
            last_name=last_name)
        CustomerProfile.objects.create(user_id=user.id)
        
        html_template=get_template('user_confirmation.html')
        print(encryption_key.encrypt(str(user.id).encode()))
        user_id=encryption_key.encrypt(str(user.id).encode())
        subject = 'inticure account creation'
        html_message = render_to_string('user_confirmation.html', {'email': user.email,
        'user_id':user_id.decode()})
        plain_message = strip_tags(html_message)
        # plain_message="account-created"
        from_email = 'wecare@inticure.com'
        to = user.email
        email_message = mail.EmailMessage(
            subject=subject,
            body=plain_message,
            from_email=from_email,
            to=[to],
        )

        email_message.send(fail_silently=False)
        # email_message = mail.EmailMessage(subject, plain_message, from_email, [to], [cc], html_message=html_message)
        # email_message.send(fail_silently=False)

        return user.id


""" OTP GENERATION AND VERIFICATION OF CUSTOMER """



@api_view(['POST'])
def otp_verify_view(request):
    OTP=""
    print(request.data)
    if "mobile_num" in request.data and "otp" not in request.data and request.data['mobile_num']:            
        if CustomerProfile.objects.filter(mobile_number=request.data['mobile_num']).count() > 0:
            return Response({
                 'response_code': 409,
                    'status': 'Failed',
                    'message': 'User Exists'},
                    status=status.HTTP_409_CONFLICT)
        else:
            OTP=generateOTP()
            OtpVerify.objects.create(mobile_number=request.data['mobile_num'], otp=OTP)
            print("OTP",OTP)
            # try:
            #     sms_service.send_message("Hi There, Your OTP for SignUp is:%s"%OTP,
            #     "+91" + str(request.data['mobile_num']))
            # except Exception as e :
            #     print("MESSAGE SENT ERROR",e)
            return Response({
                'response_code': 200,
                'status': 'Success',
                'message': 'OTP Generated',
                'otp':OTP})
            
        #try:
        #    CustomerProfile.objects.get(mobile_number=request.data['mobile_num'])
        #    return Response({
        #         'response_code': 400,
        #            'status': 'Failed',
        #            'message': 'User Exists'},
        #            status=status.HTTP_400_BAD_REQUEST)
        #except:
        #    OTP=generateOTP()
        #    OtpVerify.objects.create(mobile_number=request.data['mobile_num'],otp=OTP)
        #    print("OTP",OTP)
        #    try:
        #        sms_service.send_message("Hi There, Your OTP for SignUp is:%s"%OTP,
        #        "+91" + str(request.data['mobile_num']))
        #    except Exception as e :
        #        print("MESSAGE SENT ERROR",e)
        #        return Response({
        #         'response_code': 200,
        #            'status': 'Success',
        #            'message': 'OTP Generated',
        #            'otp':OTP})
    if "email" in request.data and "otp" not in request.data :
        try:

            User.objects.get(email=request.data['email'])
            #first_name=request.data['first_name'],last_name=request.data['last_name'])
            return Response({
                 'response_code': 409,
                    'status': 'Failed',
                    'message': 'User Exists'},
                    status=status.HTTP_409_CONFLICT)
        except:
           OTP=generateOTP()
           EmailOtpVerify.objects.create(email=request.data['email'],otp=OTP)
           print("OTP",OTP)
           subject = 'Inticure OTP Verification'
           html_message = render_to_string('email_otp.html', {'email':request.data['email'],
           "confirm":0,"OTP":OTP })
           plain_message = strip_tags(html_message)
           # plain_message="account-created"
           from_email = 'wecare@inticure.com'
           to = request.data['email']
           cc = "nextbighealthcare@inticure.com"
           mail.send_mail(subject, plain_message, from_email, [to],[cc],html_message=html_message)
           return Response({
                 'response_code': 200,
                    'status': 'Success',
                    'message': 'OTP Generated',
                    'otp':OTP})
    if "resend" in request.data:
        try:
            OTP=OtpVerify.objects.get(mobile_num=request.data['mobile_num']).otp
            # sms_service.send_message("Hi There, Your OTP for LogIn is:%s"%OTP,
            #     "+91" + str(request.data['mobile_num']))
            return Response({
                 'response_code': 200,
                    'status': 'Success',
                    'message': 'OTP Generated',
                    'otp':OTP})
        except:
            return Response({
                 'response_code': 400,
                    'status': 'Failed',
                    'message': 'Otp Re-Generation Failed '},
                    status=status.HTTP_400_BAD_REQUEST)
    if "otp" in request.data and request.data['otp']!="":
        if "mobile_num" in request.data and  request.data['mobile_num']!="": 
          print(request.data['mobile_num'].split(' '))
          try:
            print(request.data['otp'])
            OtpVerify.objects.get(mobile_number=request.data['mobile_num'].split(' ')[1],otp=request.data['otp'])
            OtpVerify.objects.get(mobile_number=request.data['mobile_num'].split(' ')[1],otp=request.data['otp']).delete()
            return Response({
                 'response_code': 200,
                    'status': 'Success',
                    'message': 'OTP Verified'})
          except:
            return Response({
                 'response_code': 400,
                    'status': 'Failed',
                    'message': 'Otp Incorrect '},
                    status=status.HTTP_400_BAD_REQUEST)
        if "email" in request.data and request.data['email']!="":
            try: 
                print(request.data['otp'])
                EmailOtpVerify.objects.get(email=request.data['email'],otp=request.data['otp'])
                EmailOtpVerify.objects.get(email=request.data['email'],otp=request.data['otp']).delete()
            
                subject = 'LogIn Confirmation'
                html_message = render_to_string('email_otp.html', {'email':request.data['email'],
                "confirm":1 })
                plain_message = strip_tags(html_message)
               # plain_message="account-created"
                from_email = 'wecare@inticure.com'
                to = request.data['email']
                cc = "nextbighealthcare@inticure.com"
                mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)
           
                return Response({
                 'response_code': 200,
                    'status': 'Success',
                    'message': 'OTP Verified'})
            except Exception as e:
                print(e)
                return Response({
                 'response_code': 400,
                    'status': 'Failed',
                    'message': 'Otp Incorrect '},
                    status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                 'response_code': 400,
                    'status': 'Failed'},
                    status=status.HTTP_400_BAD_REQUEST)
    else:
        print("else")
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST)
            
    
def assign_junior_doctor(request):
    print("assign junnior doctor")
    print(request.data)
    doctor_id_time_slots=JuniorDoctorSlots.objects.filter(date=request.data['appointment_date'],time_slot=request.data['appointment_time'], is_active = 0).values_list('doctor_id',flat=True)
    print('doctor_id_time_slots: ',doctor_id_time_slots)
    filter={}
    filter['is_accepted'] = 1
    filter['doctor_flag'] = 'junior'
    if "language_pref" in request.data and request.data['language_pref'] != "":
        try:
            doctor_id = []
            user_ids=DoctorLanguages.objects.filter(languages=request.data['language_pref']).values_list('doctor_id',flat=True)
            if len(user_ids) == 0:
                user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
            for i in user_ids:
                if i in doctor_id_time_slots:
                    doctor_id.append(i)
            
            print(doctor_id)
            filter['user_id__in']=doctor_id
            print('filter_after_first_language: ',filter)

            if "gender_pref" in request.data and request.data['gender_pref'] != "":
                filter['gender']=request.data['gender_pref']
                doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
                print('filter_after_first_gender: ',doctor_ids)
                if len(doctor_ids) == 0:
                    user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
                    for i in user_ids:
                        doctor_id.append(i)
                    filter['user_id__in']=doctor_id
                    doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
                    print('filter_after_unavailable_of_language', doctor_ids)
                    if len(doctor_ids) == 0:
                        del filter['gender']
                        user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
                        doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)       
                        print('filter_after_unavailability_of_gender', doctor_ids) 
            else:
                doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
                print('filter_after_gender_pref_is_not', doctor_ids)
                if len(doctor_ids) == 0:
                    user_ids=DoctorLanguages.objects.filter(languages='English').values_list('doctor_id',flat=True)
                    doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
                    print('filter_after_language_is_not_available_when_gender_is_not: ', doctor_ids)
        except Exception as e:
            print(e)

    else:
        if "gender_pref" in request.data and request.data['gender_pref'] != "":
            filter['gender']=request.data['gender_pref']
            doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)
            if len(doctor_ids) == 0:
                del filter['gender']
                doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)        
        else:
            doctor_ids = custom_filter(DoctorProfiles, filter).values_list('user_id',flat=True)

    doc_id=None
    print("first-filtered doctor who knows preferred language",doctor_ids)
    appointment_date_=datetime.strptime(request.data['appointment_date'],"%Y-%m-%d")

    if doctor_ids:
        print('entered')

        def get_random_available_doctor(appointment_date, appointment_time, docs,excluded_appointment_id):
           
            try:
                print('appointment_date: ',appointment_date)
                print('appointment_time: ',appointment_time)
                print('docs: ',docs)
                booked_doctor_ids = list(
                    AppointmentHeader.objects.filter(
                        appointment_date=appointment_date,
                        appointment_time_slot_id=appointment_time
                    ).exclude(appointment_id=excluded_appointment_id)  # Exclude the specific appointment ID
                    .values_list('junior_doctor', flat=True)
                )

                print('booked doctors: ', booked_doctor_ids)
                            
                booked_doctor_ids2 = list(AppointmentHeader.objects.filter(
                    appointment_date=appointment_date,
                    appointment_time_slot_id=appointment_time
                ))
                print('appointments on the same date and time: ',booked_doctor_ids2)
                # Exclude booked doctors from the list of all doctors
                available_doctor_ids = [doc_id for doc_id in docs if doc_id not in booked_doctor_ids]
                print(available_doctor_ids)
                rand_id = []
                if available_doctor_ids is not None:
                    for i in available_doctor_ids:
                        if i != None:
                            rand_id.append(i)
                    random_doctor_id = rand_id[0]
                    return random_doctor_id
                else:
                    return None
            except Exception as e:
                print(e)
                return None

        try:
            appoint = AppointmentHeader.objects.get(appointment_id=request.data['appointment_id'])
            if appoint:
                res = get_random_available_doctor(appoint.appointment_date, appoint.appointment_time_slot_id, doctor_ids,request.data['appointment_id'])
                print(res)
                if res is None:
                    raise Http404("Object not found")
        except:
            return Response({
            'response_code': 400,
            'status': 'Ok',
            'message': 'Doctor not Available'
            })

        if res:
            random_id = res
        else:
            return Response({
            'response_code': 400,
            'status': 'Ok',
            'message': 'Doctor not Available'
            })


        try:
            doctor_email = User.objects.get(pk=random_id).email
        except:
            doctor_email = ""
        if random_id:
            DoctorMapping.objects.create(mapped_doctor=random_id,appointment_id=request.data['appointment_id'],
            doctor_flag="junior")
            AppointmentHeader.objects.filter(
                appointment_id=request.data['appointment_id']).update(appointment_status=1,junior_doctor=random_id)
            JuniorDoctorSlots.objects.filter(doctor_id = random_id, date=request.data['appointment_date'],time_slot=request.data['appointment_time']).update(is_active = 1)
            return random_id,doctor_email
        else:
            return Response({
            'response_code': 400,
            'status': 'Ok',
            'message': 'Time Slot not Available'
            })
    else:
   
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message': 'Doctor not Available'
    })

@api_view(['POST'])
def create_user_view(request):
    data = request.data
    print('612', request.data)
    if request.data['email'] != "":
        if 'whatsapp_contact' in request.data and request.data['whatsapp_contact'] != "":
            user_id = create_user(data['email'],data['first_name'], data['last_name'])
            CustomerProfile.objects.filter(user_id = user_id).update(whatsapp_contact = request.data['whatsapp_contact'], confirmation_choice = 'Whats App')
        else:
            user_id = create_user(data['email'], data['first_name'],data['last_name'])
    else:
        user_id = create_user_mobile_num(request.data[''])
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': 'user created',
        'user_id':user_id
    })
        
"""First Booking of a customer"""
@api_view(['POST'])
def analysis_submit_view(request):
    doc_id=[]
    customer_message=""
    print('submission doing')       
    print(request.data) 

    appointment_date_str = request.data['appointment_date']
    appointment_time_str = request.data['appointment_time']
    appointment_datetime_str = f"{appointment_date_str} {appointment_time_str}"
    appointment_datetime = datetime.strptime(appointment_datetime_str, '%Y-%m-%d %I:%M%p')
    current_datetime = datetime.now()

    if appointment_datetime < current_datetime:
        return Response({'error': 'Appointment date and time must be in the future.'}, status=400)
    try:
        user_id = request.data['user_id']
        if request.data['new_user'] == 1:
          if "email" in request.data:
           
             if 'appointment_date' in request.data and request.data['appointment_date']!="" and \
                 'appointment_time' in request.data and  request.data['appointment_time']!="":
                 try:
                    if request.data['email'] != "" and request.data['email'] != None:
                        user = User.objects.get(email=request.data['email'])
                    print('got it')
                 except:
                     user = 0
                 if user:
                     user_i = User.objects.get(email = request.data['email'])
                     user_id = user_i.id
                 else:
                    if request.data['email'] != "" and request.data['email'] != None:
                        user_id = create_user(request.data['email'],request.data['first_name'],request.data['last_name'])
                    elif 'mobile_num' in request.data and request.data['mobile_num'] != "":
                        user_id = create_user_mobile_num(request.data['mobile_num'])
             else:
                 try:
                    if request.data['email'] != "" and request.data['email'] != None:
                        User.objects.get(email=request.data['email']).delete()
                    else:
                        User.objects.get(email=request.data['mobile_num']).delete()
                    return Response({
                    'response_code': 400,
                    'status': 'Failed'},
                    status=status.HTTP_400_BAD_REQUEST)
                 except:
                     return Response({
                    'response_code': 400,
                    'status': 'Failed'},
                    status=status.HTTP_400_BAD_REQUEST)
             print(user_id)
             other_gender=""
             customer_message=""
             mobile_num=0
             if "other_gender" in request.data and request.data['other_gender']!="":
                other_gender=request.data['other_gender']
             
             if "customer_message" in request.data and request.data['customer_message']!="":
                customer_message=request.data['customer_message']
             
             if "mobile_num" in request.data and request.data['mobile_num']!="":
                mobile_num=request.data['mobile_num']

             if "customer_dob" in request.data and request.data['customer_dob'] != "":
                dob=request.data['customer_dob']
                born=datetime.strptime(dob,"%Y-%m-%d")
                today = date.today()
                age=today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                print(today,age,"AGE CALCULATED")
             location=2
             if "customer_location" in request.data and request.data["customer_location"]!="":
                 try:
                    location = Locations.objects.get(location = request.data['customer_location']).location_id
                 except Exception as e:
                    print(e)
                    location = Locations.objects.get(location = 'USA').location_id
             if mobile_num != 0:
                CustomerProfile.objects.filter(user_id=user_id).update(mobile_number=mobile_num.split(' ')[1],
                date_of_birth=request.data['customer_dob'],
                gender=request.data['customer_gender'],other_gender=other_gender,age=age,location=location,
                residence_location = request.data['customer_location'])
             else:
                CustomerProfile.objects.filter(user_id=user_id).update(
                date_of_birth=request.data['customer_dob'],
                gender=request.data['customer_gender'],other_gender=other_gender,age=age,location=location,
                residence_location = request.data['customer_location'])

        appointment_time=request.data['appointment_time']
        appointment_date=request.data['appointment_date']
        print("create appointment")

        appointment = AppointmentHeader.objects.create(user_id=user_id, 
        category_id=request.data['category_id'],is_free=request.data['new_user'],
        appointment_date=request.data['appointment_date'],
        appointment_time_slot_id=appointment_time,type_booking='new',
        language_pref=request.data['language_pref'],gender_pref=request.data['gender_pref'],
        customer_message=customer_message,payment_status=True)
        print("appointment created")
        for question in request.data['questions']:
            appointment_questions = AppointmentQuestions.objects.create(question_id=question['question_id'],
                                    question=question['question'],appointment_id=appointment.appointment_id)
            try:
              answer_type=Questionnaire.objects.get(id=question['question_id']).answer_type
            except:
                answer_type=""
            if answer_type !='textfield':
               print('options:  \n',question['options'],'\n')
               for option in question['options']:  
                  if answer_type=='checkbox':
                    print("CHECKBOX")

                    for options in option['option_id']:
                         print('option  \n',options,'\n')
                         try:
                            print("try")
                            answers=Options.objects.get(id=options).option
                         except Exception as e:
                            print("excepy",e)
                            answers=""
                         print('answers \n',answers)
                         AppointmentAnswers.objects.create(
                         appointment_questions_id=appointment_questions.appointment_questions_id,
                         option_id=options, answer=answers)
                  else:
                    print('answer_type: \n',answer_type,'\n')
                    print('option_id : ', option['option_id'],'\n')

                    appointment_answers=OptionsSerializer(Options.objects.filter(id=option['option_id']),many=True).data
                    for answer in appointment_answers:
                       answers=answer['option']
                       print('appointment_answers: \n',appointment_answers,'\n')
                       AppointmentAnswers.objects.create(
                       appointment_questions_id=appointment_questions.appointment_questions_id,
                       option_id=option['option_id'], answer=answers)
            else:
                print("ESLE")
                for option in question['options']:  
                    AppointmentAnswers.objects.create(
                    appointment_questions_id=appointment_questions.appointment_questions_id,
                    option_id=0, answer=option['answer'])
        if request.data['email'] != "" and request.data['email'] != None:
            Invoices.objects.create(
                appointment_id=appointment.appointment_id,
                user_id=user_id, 
                bill_for=request.data['first_name'],
                email=request.data['email'],
                total=0,
                status=0,
                due_date=request.data['appointment_date']
            )
        else:
            Invoices.objects.create(
                appointment_id=appointment.appointment_id,
                user_id=user_id, 
                bill_for=request.data['first_name'],
                email=request.data['mobile_num'],
                total=0,
                status=0,
                due_date=request.data['appointment_date']
            )

        request.data['appointment_id']=appointment.appointment_id
        random_id=0
        try:
            random_id,doctor_email=assign_junior_doctor(request)
            print("random id",random_id,"email",doctor_email)
        except:
            appoint = AppointmentHeader.objects.get(appointment_id = appointment.appointment_id).delete()
            return Response({
                'response_code': 400,
                'status': 'Ok',
                'message': 'Doctor not Available'
                })


        # start_time,end_time = get_slot_time(appointment_time,request.data['appointment_date'],doctor_flag='junior')
        if random_id:
            print("timeslot updated inactive")
            JuniorDoctorSlots.objects.filter(doctor_id=random_id,date=appointment_date,time_slot=appointment_time).update(is_active=1)
        specialization="no specialization"
        start_time,end_time = get_appointment_time(appointment_time,request.data['appointment_date'],specialization,doctor_flag='junior',doctor_id=random_id)
        meet_link= generate_google_meet("Inticure,Preliminary Analysis","",[{"email":request.data['email']},{"email":doctor_email}],start_time,end_time)
        print("************************************")
        print(meet_link,"google meet link")
        AppointmentHeader.objects.filter(appointment_id=appointment.appointment_id).update(meeting_link=meet_link, appointment_status = 1)
        appoint = AppointmentHeader.objects.get(appointment_id = appointment.appointment_id)
        # try:
        #     sms_service.send_message(
        #     "Hi There, Your Appointment has been confirmed on:%s%s Please refer mail for more details"%(request.data['appointment_date'],start_time),
        #         "+91" + str(CustomerProfile.objects.get(user_id=user_id).mobile_number))
        # except:
        #     print("MESSAGE SENT ERROR")
        subject = 'YES! Your FIRST consultation is confirmed'
        '''for testing purpose only '''
        html_message = render_to_string('order_confirmation_customer.html', {"doctor_flag":0,"meet_link":meet_link,
        'appointment_id': appointment.appointment_id,"doctor_name":get_users_name(random_id),
        "doctor_name":get_users_name(random_id),"name":get_users_name(appoint.user_id)})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        to = request.data['email']
        cc = "nextbighealthcare@inticure.com"
        mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)
        subject = 'Appointment Confirmation'
        html_message = render_to_string('order_confirmation_doctor.html', {"doctor_flag":1,"meet_link":meet_link,
            'appointment_id': appointment.appointment_id,"doctor_name":get_users_name(random_id),
        "name":get_users_name(appoint.user_id),"meet_link":meet_link})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        to = get_user_mail(random_id)
        cc = "nextbighealthcare@inticure.com"
        mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)
        return Response({
            'response_code': 200,
            'status': 'Ok',
            'message': 'Analysis submitted',
            'assigned_doctor':get_user_mail(random_id),
            'appointment_id':appointment.appointment_id
        })
    except Exception as e:
        print("except Exce",e)  
        # user_id=CustomerProfile.objects.last().user_id
        # CustomerProfile.objects.last().delete()
        # AppointmentHeader.objects.last().delete()
        # Invoices.objects.last().delete()
        # User.objects.get(id=user_id).delete()
        # JuniorDoctorSlots.objects.filter(doctor_id=random_id,time_slot=appointment_time).update(is_active=0)
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST)


"""First Booking of a customer"""
# @api_view(['POST'])
# def analysis_submit_view_Copy(request):
#     doc_id=[]
#     customer_message=""
#     try:
#         user_id = request.data['user_id']
#         if request.data['new_user'] == 1:
#           if "email" in request.data and request.data['email'] !="":
#              try:
#                 User.objects.get(email=request.data['email'])
#                 #first_name=request.data['first_name'],last_name=request.data['last_name'])
#                 return Response({
#                     'response_code': 409,
#                     'status': 'Failed',
#                     'message': 'User Exists'},
#                     status=status.HTTP_409_CONFLICT)
#              except:
#                 if 'appointment_date' in request.data and request.data['appointment_date']!="" and \
#                     'appointment_time' in request.data and  request.data['appointment_time']!="":
#                     user_id = create_user(request.data['email'],request.data['first_name'],request.data['last_name'])
#                 else:
#                     return Response({
#                     'response_code': 400,
#                     'status': 'Failed'},
#                     status=status.HTTP_400_BAD_REQUEST)
#              print(user_id)
#              other_gender=""
#              customer_message=""
#              mobile_num=0
#              if "other_gender" in request.data and request.data['other_gender']!="":
#                 other_gender=request.data['other_gender']
             
#              if "customer_message" in request.data and request.data['customer_message']!="":
#                 customer_message=request.data['customer_message']
             
#              if "mobile_num" in request.data and request.data['mobile_num']!="":
#                 mobile_num=request.data['mobile_num']

#              if "customer_dob" in request.data and request.data['customer_dob'] != "":
#                 dob=request.data['customer_dob']
#                 born=datetime.strptime(dob,"%Y-%m-%d")
#                 today = date.today()
#                 age=today.year - born.year - ((today.month, today.day) < (born.month, born.day))
#                 print(today,age,"AGE CALCULATED")
#              location=1
#              if "customer_location" in request.data and request.data["customer_location"]!="":
#                  if request.data['customer_location']=="IN":
#                     location=1
#                  else:
#                     location=2
#              CustomerProfile.objects.filter(user_id=user_id).update(mobile_number=mobile_num,
#              date_of_birth=request.data['customer_dob'],
#              gender=request.data['customer_gender'],other_gender=other_gender,age=age,location=location)

#         appointment_time=request.data['appointment_time']
#         appointment_date=request.data['appointment_date']
#         print("create appointment")
#         appointment = AppointmentHeader.objects.create(user_id=user_id, 
#         category_id=request.data['category_id'],is_free=request.data['new_user'],
#         appointment_date=request.data['appointment_date'],
#         appointment_time_slot_id=appointment_time,type_booking='new',
#         language_pref=request.data['language_pref'],gender_pref=request.data['gender_pref'],
#         customer_message=customer_message)
#         print("appointment created")
#         for question in request.data['questions']:
#             appointment_questions = AppointmentQuestions.objects.create(question_id=question['question_id'],
#                                     question=question['question'],appointment_id=appointment.appointment_id)
#             try:
#               answer_type=Questionnaire.objects.get(id=question['question_id']).answer_type
#             except:
#                 answer_type=""
#             if answer_type !='textfield':
#                for option in question['options']:  
#                   if answer_type=='checkbox':
#                     print("CHECKBOX")
#                     for options in option['option_id']:
#                          print(options)
#                          try:
#                             print("try")
#                             answers=Options.objects.get(id=options).option
#                          except Exception as e:
#                             print("excepy",e)
#                             answers=""
#                          print(answers)
#                          AppointmentAnswers.objects.create(
#                          appointment_questions_id=appointment_questions.appointment_questions_id,
#                          option_id=options, answer=answers)
#                   else:
#                     print(answer_type)
#                     appointment_answers=OptionsSerializer(Options.objects.filter(id=option['option_id']),many=True).data
#                     for answer in appointment_answers:
#                        answers=answer['option']
#                        print(appointment_answers)
#                        AppointmentAnswers.objects.create(
#                        appointment_questions_id=appointment_questions.appointment_questions_id,
#                        option_id=option['option_id'], answer=answers)
#             else:
#                 print("ESLE")
#                 for option in question['options']:  
#                     AppointmentAnswers.objects.create(
#                     appointment_questions_id=appointment_questions.appointment_questions_id,
#                     option_id=0, answer=option['answer'])
       
#         Invoices.objects.create(
#             appointment_id=appointment.appointment_id,
#             user_id=user_id, 
#             bill_for=request.data['first_name'],
#             email=request.data['email'],
#             total=0,
#             status=0,
#             due_date=request.data['appointment_date']
#         )
#         request.data['appointment_id']=appointment.appointment_id
#         '''auto assign junior doctor'''
#         random_id,doctor_email=assign_junior_doctor(request)
#         print("random id",random_id,"email",doctor_email)
#         start_time,end_time = get_slot_time(appointment_time,request.data['appointment_date'],doctor_flag='junior')
#         meet_link= generate_google_meet("Inticure,Preliminary Analysis","",[{"email":request.data['email']},{"email":doctor_email}],start_time,end_time)
#         print("************************************")
#         print(meet_link,"google meet link")
#         AppointmentHeader.objects.filter(appointment_id=appointment.appointment_id).update(meeting_link=meet_link)
#         # try:
#         #     sms_service.send_message(
#         #     "Hi There, Your Appointment has been confirmed on:%s%s Please refer mail for more details"%(request.data['appointment_date'],start_time),
#         #         "+91" + str(CustomerProfile.objects.get(user_id=user_id).mobile_number))
#         # except:
#         #     print("MESSAGE SENT ERROR")
#         subject = 'YES! Your FREE consultation is confirmed'
#         '''for testing purpose only '''
#         html_message = render_to_string('order_confirmation_customer.html', {"doctor_flag":0,"meet_link":meet_link,
#         'appointment_id': appointment.appointment_id,"doctor_name":get_users_name(random_id),
#         "doctor_name":get_users_name(random_id),"name":request.data['email']})
#         plain_message = strip_tags(html_message)
#         from_email = 'Inticure <hello@inticure.com>'
#         to = request.data['email']
#         mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)
#         subject = 'Appointment Confirmation'
#         html_message = render_to_string('order_confirmation_doctor.html', {"doctor_flag":1,"meet_link":meet_link,
#             'appointment_id': appointment.appointment_id,"doctor_name":get_users_name(random_id),
#         "name":request.data['email'],"meet_link":meet_link})
#         plain_message = strip_tags(html_message)
#         from_email = 'Inticure <hello@inticure.com>'
#         to = get_user_mail(random_id)
#         mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)
#         return Response({
#             'response_code': 200,
#             'status': 'Ok',
#             'message': 'Analysis submitted',
#             'assigned_doctor':get_user_mail(random_id)
#         })
#     except Exception as e:
#         print("except",e)
#         return Response({
#             'response_code': 400,
#             'status': 'Failed'},
#             status=status.HTTP_400_BAD_REQUEST)




"""View to create followup and paid bookings """
@api_view(['POST'])
def followup_booking_view(request):

    # last_request_time = cache.get(f"last_request_time_{request.data['user_id']}")    
    # current_time = timezone.now()
    # if last_request_time and (current_time - last_request_time) < timedelta(seconds=10):
    #     return redirect('another_view')  
    # cache.set(f"last_request_time_{request.data['user_id']}", current_time, timeout=10)  

    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@follow up booking@@@@@@@@@@@@@@@@@@@@@@@@ ")
    print("request",request.data)
    appointment_time_slot=request.data['appointment_time']
    appointment_date=request.data['appointment_date']
    user_id=request.data['user_id']
    doctor_flag=request.data['doctor_flag']
    appointment_status=request.data['appointment_status']
    time_slot_id=request.data['appointment_time']
    
    print("type_booking",request.data['type_booking'])
    try:
        user=User.objects.get(id=request.data['user_id'])
        customer=CustomerProfile.objects.get(user_id=request.data['user_id'])
        username=user.username
        customer_addr=customer.address
        customer_phone=customer.mobile_number
        customer_age=customer.age
        customer_dob=customer.date_of_birth
        customer_gender=customer.gender
    except Exception as e:
        print(e)
        username=""
        customer_addr=""
        customer_phone=""
        customer_age=""
        customer_dob=""
        customer_gender=""
    
    if (request.data['type_booking']=='followup'):
        appointment_id=request.data['followup_id']
        doctor_flg=""
        try:
            appointment_qset=AppointmentHeader.objects.get(appointment_id=appointment_id)
            language_pref=appointment_qset.language_pref
            gender_pref=appointment_qset.gender_pref
        except Exception as e:
            print(e)
            language_pref=""
            gender_pref=""
        if doctor_flag==1:
            print("doctor")
            doctor_id=request.data['doctor_id']
            doctor_flg="senior"
            appointment=AppointmentHeader.objects.create(
                user_id=user_id, category_id=request.data['category_id'],
                is_free=request.data['new_user'],
                appointment_date=appointment_date,
                appointment_time_slot_id=time_slot_id,
                followup_id=request.data['followup_id'],
                type_booking=request.data['type_booking'],
                followup_created_by=request.data['followup_created_by'],
                followup_created_doctor_id=request.data['followup_created_doctor_id'],
                appointment_status=appointment_status,
                language_pref=language_pref,gender_pref=gender_pref,
                senior_doctor=doctor_id,followup_remark=request.data['remarks'])
            time_slot_querysets=SrDoctorEngagement.objects.create(user_id=doctor_id,
                appointment_id=appointment.appointment_id,date=appointment_date,time_slot=time_slot_id)
            DoctorMapping.objects.create(appointment_id=appointment.appointment_id,
            mapped_doctor=request.data['followup_created_doctor_id'],doctor_flag="senior")
            
            if ("language_pref" in request.data and request.data["language_pref"] != "" )and \
                ("gender_pref" in request.data and request.data["gender_pref"] != "") and \
                ("specialization" in request.data and request.data["specialization"] != ""):
                print("assign sr doc")
                followup_doc_id=assign_senior_doctor(request)
                DoctorMapping.objects.create(appointment_id=appointment.appointment_id,
                mapped_doctor=followup_doc_id,doctor_flag="senior",added_doctor=1)
            try:
                location=CustomerProfile.objects.get(user_id=request.data['user_id']).location
            except Exception as e :
                print("location exception",e)
                location=1
            print("location",location)
            try:
               doctor=DoctorProfiles.objects.get(user_id=doctor_id)
               print("specialization",specialization,location)
            except Exception as e:
                print("exception specialization",e)
                specialization=None
            try:
               price=Plans.objects.get(speciality=doctor.specialization,location_id=location,doctor_id=doctor.doctor_profile_id).price
            except Exception as e:
                print("exception specialization",e)
            
                price=0
            print("specialization",doctor.specialization,"price",price)
            Invoices.objects.create(
            appointment_id=appointment.appointment_id,
            user_id=request.data['user_id'], 
            bill_for=get_users_name(request.data['user_id']),
            email=username,
            address=customer_addr,
            mobile_number=customer_phone,
            age=customer_age,
            date_of_birth=customer_dob,
            appointment_for="service",
            service=doctor.specialization,
            gender=customer_gender,
            appointment_date=appointment_date, 
            appointment_time=time_slot_id,
            vendor_fee=price*20/100,
            tax=0,
            total=price,
            status=2,category_id=request.data['category_id'],
            due_date=appointment_date)
            if doctor_flg=="senior":
                SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=appointment_date,time_slot=time_slot_id).update(is_active=1)
            doctor_email = get_user_mail(doctor_id)
            user_email = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
            start_time, end_time = get_appointment_time(appointment_time_slot,appointment_date,doctor.specialization,doctor_flag=doctor_flg,doctor_id = doctor.doctor_profile_id)
            meet_link = generate_google_meet("Inticure,Follow Up Appointment", "",
                                         [{"email": user_email}, {"email": doctor_email}], start_time,
                                         end_time)
            AppointmentHeader.objects.filter(appointment_id=appointment_id).update(senior_meeting_link=meet_link,appointment_status = 1)
            AppointmentHeader.objects.filter(appointment_id=appointment.appointment_id).update(senior_meeting_link=meet_link,appointment_status = 1)
            subject = 'Payment for consultation'
            html_message = render_to_string('payment_mail.html', {'appointment_id': appointment.appointment_id,
                "doctor_name":get_users_name(doctor_id),"name":get_users_name(request.data['user_id']),
                "meet_link":meet_link,"specialization":get_doctor_specialization(doctor_id),'date':appointment.appointment_date,
                "time":request.data['appointment_time']})
            plain_message = strip_tags(html_message)
            from_email = 'wecare@inticure.com'
            cc = "nextbighealthcare@inticure.com"
            to = user_email
            mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)

        if doctor_flag==0:
            doctor_qset=AppointmentHeader.objects.get(appointment_id=request.data['followup_id'])
            doctor_id=doctor_qset.senior_doctor
            appointment=AppointmentHeader.objects.create(user_id=user_id, 
                category_id=request.data['category_id'],
                is_free=request.data['new_user'],
                appointment_date=appointment_date,
                appointment_time_slot_id=time_slot_id,
                followup_id=request.data['followup_id'],
                senior_doctor=doctor_id,
                language_pref=language_pref,gender_pref=gender_pref,
                followup_created_by=request.data['followup_created_by'],
                followup_created_doctor_id=doctor_id,
                appointment_status=appointment_status,
                type_booking=request.data['type_booking'],followup_remark=request.data['remarks'])
            try:
                location=CustomerProfile.objects.get(user_id=request.data['user_id']).location
            except Exception as e :
                print("location exception",e)
                location=1
            try:
               doctor=DoctorProfiles.objects.get(user_id=doctor_id)
            except Exception as e:
                doctor.specialization=None
            try:
               price=Plans.objects.get(speciality=doctor.specialization,location_id=location,doctor_id = doctor.doctor_profile_id).price
            except Exception as e:
                print("cust followup",e)
                price=0
                
            invoice_obj=Invoices.objects.create(
            appointment_id=appointment.appointment_id,
            user_id=request.data['user_id'], 
            bill_for=get_users_name(request.data['user_id']),
            email=username,
            address=customer_addr,
            mobile_number=customer_phone,
            age=customer_age,
            date_of_birth=customer_dob,
            appointment_for="service",
            service=doctor.specialization,
            appointment_date=appointment_date,
            appointment_time=time_slot_id,
            gender=customer_gender,
            doctor_id=doctor_id,
            doctor_name=get_users_name(doctor_id),
            vendor_fee=price*20/100,
            tax=0,
            total=price,
            status=1,category_id=request.data['category_id'],
            due_date=appointment_date)
            Transactions.objects.create(invoice_id=invoice_obj.invoice_id,
            transaction_amount=price,payment_status=1)
        if doctor_id:
            SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=appointment_date,time_slot=time_slot_id).update(is_active=1)
        doctor_email = get_user_mail(doctor_id)
        user_email = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment_id).user_id)
        start_time, end_time = get_appointment_time(appointment_time_slot,appointment_date,doctor.specialization,doctor_flag=doctor_flg, doctor_id = doctor.doctor_profile_id)
        meet_link = generate_google_meet("Inticure,Follow Up Appointment", "",
                                         [{"email": user_email}, {"email": doctor_email}], start_time,
                                         end_time)
        AppointmentHeader.objects.filter(appointment_id=appointment_id).update(senior_meeting_link=meet_link,appointment_status = 1)
        AppointmentHeader.objects.filter(appointment_id=appointment.appointment_id).update(senior_meeting_link=meet_link,appointment_status = 1)
        # try:
        #    sms_service.send_message(
        #     "Hi There, Your Followup Appointment has been confirmed on: %s %s Please refer mail for more details"%(appointment_date,start_time),
        #         "+91" + str(CustomerProfile.objects.get(user_id=request.data['user_id']).mobile_number))
        # except Exception as e:
        #     print(e)
        #     print("MESSAGE SENT ERROR")
        doctor_bio,profile_pic=get_doctor_bio(doctor_id)
        subject = ' Yes! Your follow-up consultation is confirmed'
        html_message = render_to_string('order_followup.html', {'appointment_id': appointment.appointment_id,
        "doctor_name":get_users_name(doctor_id),"name":get_users_name(request.data['user_id']),
        "meet_link":meet_link,"specialization":get_doctor_specialization(doctor_id),'date':appointment_date,
        "time":time_slot_id,"doctor_bio":doctor_bio,"profile_pic":profile_pic
        })
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        to = user_email
        cc = "nextbighealthcare@inticure.com"
        mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)
        
        subject = 'Appointment Confirmation'
        html_message = render_to_string('order_confirmation_doctor.html', {'appointment_id': appointment.appointment_id,
        "name":get_users_name(request.data['user_id']),"doctor_name":get_users_name(doctor_id),'date':appointment_date,
        "time":time_slot_id,"doctor_flag":2,"meet_link":meet_link})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        to = doctor_email
        cc = "nextbighealthcare@inticure.com"
        mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)

        return Response({
            'response_code': 200,
            'status': 'Ok',
            'message': 'Followup Booking Created',
            'followup_appointment_id':appointment.appointment_id
        })
    

    elif (request.data['type_booking']=='regular'):
        #doctor_id=request.data['doctor_id']
        print("regular booking ")
        doctor_id=0
        #if doctor_flag == 1:
        if 'doctor_user_id' not in request.data or request.data['doctor_user_id'] == "" or request.data['doctor_user_id'] == 0:

            senior_doctor_id=assign_senior_doctor(request)
            if senior_doctor_id:
                doctor_id=senior_doctor_id
            
        else:
            doctor_id=request.data['doctor_user_id']
        print("checking doctor flag ")
        if request.data['doctor_flag']==0:  
          print("doctor flag is 0")
          appointment =AppointmentHeader.objects.create(
          user_id=request.data['user_id'], 
          category_id=request.data['category_id'],
          is_free=request.data['new_user'],
          appointment_date=appointment_date,
          appointment_time_slot_id=time_slot_id,
          language_pref=request.data['language_pref'],
          gender_pref=request.data['gender_pref'],
          appointment_status=appointment_status,
          senior_doctor=doctor_id,
          type_booking=request.data['type_booking'])
          DoctorMapping.objects.create(appointment_id=appointment.appointment_id,mapped_doctor=doctor_id,
          doctor_flag="senior")
          try:
                location=CustomerProfile.objects.get(user_id=request.data['user_id']).location
          except Exception as e :
                location = Locations.objects.get(location = 'USA').location_id
          try:
           specialization=DoctorProfiles.objects.get(user_id=doctor_id).specialization
           print("specialization",specialization,location)
           if request.data['session_type'] == 'couple':
            price=Plans.objects.get(speciality=specialization,location_id=location, doctor_id = request.data['senior_doctor']).price_for_couple
           else:
            price=Plans.objects.get(speciality=specialization,location_id=location, doctor_id = request.data['senior_doctor']).price_for_single
        
          except Exception as e :
            print("exception in specialization plans-------------",e)
            specialization=None
            #price=None
            price=0
          print("plans","specialization",price,specialization)
          invoice_obj=Invoices.objects.create(
            appointment_id=appointment.appointment_id,
            user_id=request.data['user_id'], 
            bill_for=get_users_name(request.data['user_id']),
            email=username,
            address=customer_addr,
            mobile_number=customer_phone,
            age=customer_age,
            date_of_birth=customer_dob,
            appointment_date=appointment_date,
            appointment_time=time_slot_id,
            gender=customer_gender,
            doctor_id=doctor_id,
            doctor_name=get_users_name(doctor_id),
            appointment_for="service",
            service=specialization,
            vendor_fee=price*20/100,
            tax=0,
            total=price,
            status=1,category_id=None,
            due_date=appointment_date)
          Transactions.objects.create(invoice_id=invoice_obj.invoice_id,
            transaction_amount=price,payment_status=1)
            
        if request.data['doctor_flag']==1:  
          print("doctor flag is 1")
          appointment =AppointmentHeader.objects.create(
          user_id=request.data['user_id'], 
          category_id=request.data['category_id'],
          is_free=request.data['new_user'],
          appointment_date=appointment_date,
          appointment_time_slot_id=time_slot_id,
          language_pref=request.data['language_pref'],
          gender_pref=request.data['gender_pref'],
          type_booking=request.data['type_booking'],
          senior_doctor=doctor_id,
          appointment_status=1)
          DoctorMapping.objects.create(appointment_id=appointment.appointment_id,mapped_doctor=doctor_id,doctor_flag="senior")
          try:
                location=CustomerProfile.objects.get(user_id=request.data['user_id']).location
          except Exception as e :
                print("location exception",e)
                location=1
          try:
           print("inside try  block ")
           specialization=DoctorProfiles.objects.get(user_id=doctor_id)
           price=Plans.objects.get(speciality=specialization.specialization,doctor_id=specialization.doctor_profile_id,location_id=location).price
          except:
            print("inside except block ")
            #price=None
            price=0
            specialization=None
          Invoices.objects.create(
            appointment_id=appointment.appointment_id,
            user_id=request.data['user_id'], 
            bill_for=get_users_name(request.data['user_id']),
            email=username,
            address=customer_addr,
            mobile_number=customer_phone,
            age=customer_age,
            date_of_birth=customer_dob,
            appointment_for="service",
            appointment_date=appointment_date,
            appointment_time=time_slot_id,
            gender=customer_gender,
            doctor_id=doctor_id,
            doctor_name=get_users_name(doctor_id),
            service=specialization.specialization,
            vendor_fee=price*20/100,
            tax=0,
            total=price,
            status=2,category_id=None,
            due_date=appointment_date)
          print("created invoice ")
        if doctor_id:
            SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=appointment_date,time_slot=time_slot_id).update(is_active=1)
        doctor_email = get_user_mail(doctor_id)
        user_email = get_user_mail(AppointmentHeader.objects.get(appointment_id = appointment.appointment_id).user_id)
        doctor = DoctorProfiles.objects.get(user_id = doctor_id).doctor_profile_id
        start_time, end_time = get_appointment_time(appointment_time_slot,appointment_date,specialization,doctor_flag=doctor_flag, doctor_id = doctor)
        meet_link = generate_google_meet("Inticure,Follow Up Appointment", "",
                                         [{"email": user_email}, {"email": doctor_email}], start_time,
                                         end_time)
        AppointmentHeader.objects.filter(appointment_id=appointment.appointment_id).update(senior_meeting_link=meet_link, appointment_status = 1)
        AppointmentHeader.objects.filter(appointment_id=appointment.appointment_id).update(senior_meeting_link=meet_link, appointment_status = 1)

        user = AppointmentHeader.objects.filter(appointment_id=appointment.appointment_id).user_id
        if CustomerProfile.objects.filter(user_id = user).confirmation_choice == 'Whats App':
            pass
        else:
            doctor_bio,profile_pic=get_doctor_bio(doctor_id)
            subject = ' Yes! Your follow-up consultation is confirmed'
            html_message = render_to_string('order_followup.html', {'appointment_id': appointment.appointment_id,
            "doctor_name":get_users_name(doctor_id),"name":get_users_name(request.data['user_id']),
            "meet_link":meet_link,"specialization":get_doctor_specialization(doctor_id),'date':appointment_date,
            "time":time_slot_id,"doctor_bio":doctor_bio,"profile_pic":profile_pic
            })
            plain_message = strip_tags(html_message)
            from_email = 'wecare@inticure.com'
            to = user_email
            cc = "nextbighealthcare@inticure.com"
            mail.send_mail(subject, plain_message, from_email, [to],[cc] ,html_message=html_message)
            subject = 'Appointment Confirmation'
            html_message = render_to_string('order_confirmation_doctor.html', {'appointment_id': appointment.appointment_id,
            "name":get_users_name(request.data['user_id']),"doctor_name":get_users_name(doctor_id),'date':appointment_date,
            "time":time_slot_id,"doctor_flag":2,"meet_link":meet_link})
            plain_message = strip_tags(html_message)
            from_email = 'wecare@inticure.com'
            to = doctor_email
            mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)

        return Response({
            'response_code': 200,
            'status': 'Ok',
            'message': 'Booking Created',
            'appointment_id':appointment.appointment_id})
    
    elif (request.data['type_booking']=='referred'):
        #doctor_id=request.data['doctor_id']
        print("referred booking ")
        doctor_id=0
            
        if request.data['doctor_flag']:  
          print("doctor flag is 1")
          appointment =AppointmentHeader.objects.get(appointment_id = request.data['appointment_id'])
          appointment2 =AppointmentHeader.objects.filter(appointment_id = request.data['appointment_id']).update(payment_status = True,appointment_status=1)
          doctor_id = appointment.senior_doctor
          doctor = DoctorProfiles.objects.get(user_id = appointment.senior_doctor)
          DoctorMapping.objects.create(appointment_id=appointment.appointment_id,mapped_doctor=doctor.user_id,doctor_flag="senior")
          try:
                location=CustomerProfile.objects.get(user_id=request.data['user_id']).location
          except Exception as e :
                print("location exception",e)
                location=Locations.objects.get(location = 'USA').id
          try:
           print("inside try  block ")
           specialization=doctor.specialization
           if (request.data['session_type'] == 'single' or request.data['session_type'] == 'individual'):
               price=Plans.objects.get(speciality=specialization,location_id=location,doctor_id = doctor.doctor_profile_id).price_for_single
           else:
               price=Plans.objects.get(speciality=specialization,location_id=location,doctor_id = doctor.doctor_profile_id).price_for_couple
               
          except Exception as e:
            print("inside except block ",e)
            #price=None
            price=0
            specialization=None
          try:
            Invoices.objects.create(
              appointment_id=appointment.appointment_id,
              user_id=request.data['user_id'], 
              bill_for=get_users_name(request.data['user_id']),
              email=username,
              address=customer_addr,
              mobile_number=customer_phone,
              age=customer_age,
              date_of_birth=customer_dob,
              appointment_for="service",
              appointment_date=appointment_date,
              appointment_time=time_slot_id,
              gender=customer_gender,
              doctor_id=doctor_id,
              doctor_name=get_users_name(doctor_id),
              service=specialization,
              vendor_fee=price*20/100,
              tax=0,
              total=price,
              status=2,category_id=None,
              due_date=appointment_date)
            print("created invoice ")
          except Exception as e:
              print(e)
        
        
        
        # if request.data['doctor_flag']==2:  
        #   appointment =AppointmentHeader.objects.create(
        #   user_id=request.data['user_id'], 
        #   category_id=request.data['category_id'],
        #   is_free=request.data['new_user'],
        #   appointment_date=appointment_date,
        #   appointment_time_slot_id=time_slot_id,
        #   language_pref=request.data['language_pref'],
        #   gender_pref=request.data['gender_pref'],
        #   appointment_status=appointment_status,
        #   type_booking=request.data['type_booking'])
        #   DoctorMapping.objects.create(appointment_id=appointment.appointment_id,mapped_doctor=doctor_id,
        #   doctor_flag="junior")
        if doctor_id:
            SeniorDoctorAvailableTimeSLots.objects.filter(doctor_id=doctor_id,date=appointment_date,time_slot=time_slot_id).update(is_active=1)
        doctor_email = get_user_mail(doctor_id)
        user_email = get_user_mail(AppointmentHeader.objects.get(appointment_id=appointment.appointment_id).user_id)
        start_time, end_time = get_appointment_time(appointment_time_slot,appointment_date,specialization,doctor_flag="senior",doctor_id=doctor.doctor_profile_id)
        meet_link = generate_google_meet("Inticure,Doctor Appointment", "",
                                         [{"email": user_email}, {"email": doctor_email}], start_time,
                                         end_time)
        AppointmentHeader.objects.filter(appointment_id=appointment.appointment_id).update(senior_meeting_link=meet_link,payment_status=True)
        # try:
        #    sms_service.send_message(
        #     "Hi There, Your Paid Appointment has been confirmed on:%s%s Please refer mail for more details"%(appointment_date,start_time),
        #         "+91" + str(CustomerProfile.objects.get(user_id=request.data['user_id']).mobile_number))
        # except Exception as e:
        #     print(e)
        #     print("MESSAGE SENT ERROR")
        
        doctor_bio,profile_pic=get_doctor_bio(doctor_id)
        subject = ' Yes! Your consultation is confirmed'
        html_message = render_to_string('consultation_confirmation_customer.html', {'appointment_id': appointment.appointment_id,
        "doctor_name":get_users_name(doctor_id),"name":get_users_name(request.data['user_id']),
        "meet_link":meet_link,"specialization":get_doctor_specialization(doctor_id),"date":appointment_date,"time":time_slot_id,
        "doctor_bio":doctor_bio,"profile_pic":profile_pic})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        cc = "nextbighealthcare@inticure.com"
        to = user_email
        #to="gopika197.en@gmail.com"
        mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)
        
        subject = 'Appointment Confirmation'
        html_message = render_to_string('order_confirmation_doctor.html', {'appointment_id': appointment.appointment_id,
        "name":get_users_name(request.data['user_id']),"doctor_name":get_users_name(doctor_id),
        "doctor_flag":2,"meet_link":meet_link})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        cc = "nextbighealthcare@inticure.com"
        to = doctor_email
        mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)

        return Response({
            'response_code': 200,
            'status': 'Ok',
            'message': 'Booking Created',
            'appointment_id':appointment.appointment_id})
    else:
        return Response({
            'response_code': 400,
            'status': 'Failed',
            'message': 'Booking Creation Failed'
        })

"""Invoice List API"""
@api_view(['POST'])
def invoice_list_view(request):
    filter={}
    try:
        if 'user_id' in request.data and request.data['user_id']!= '':
            filter['user_id']=request.data['user_id']
        if 'status' in request.data and request.data['status']!='':
            filter['status']=request.data['status']
        queryset = custom_filter(Invoices, filter).order_by('-invoice_id')
        invoice=InvoicesSerializer(queryset,many=True).data
        for data in invoice:
            data['category']=get_category_name(data['category_id'])
            data['currency']=get_currency(get_doctor_location(data['doctor_id']))
        print(invoice)
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': invoice
    })
    except Exception as e:
        print("invoice_exception",e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Invoice List None"
    })  

"""Invoice Detail API"""
@api_view(['POST'])
def invoice_detail_view(request):
    filter={}
    try:
        queryset=Invoices.objects.get(invoice_id=request.data['invoice_id'])
        invoices=InvoicesSerializer(queryset).data
        invoices['category']=get_category_name(invoices['category_id'])
        invoices['currency']=get_currency(get_doctor_location(invoices['doctor_id']))
        print(invoices)
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': invoices
    })
    except Exception as e:
        print("invoice_exception",e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Invoice List None"
    })  
    
"""Payments API"""
@api_view(['POST'])
def payments_view(request):
    print('payment view',request.data)
    current_date=datetime.today().date()
    discount=0
    coupon_message=""
    coupon_id=0
    specialization=""   
    price_breakup={}
    user_id=request.data['user_id']
    appointment_id=request.data['appointment_id']
    location_id = request.data['location_id']
    if appointment_id=="":
        appointment_id=None
    try: 
        try:
            coupon_qset=DiscountCoupons.objects.get(coupon_code=request.data['coupon_code'])
            print(current_date<=coupon_qset.expiry_date)
            try:
                CouponRedeemLog.objects.get(coupon_id=coupon_qset.id)
                coupon_id=0
                coupon_message="Coupon Used"
                print("end of try 1")
            except Exception as e :
                print(e)
                if (current_date<=coupon_qset.expiry_date)==True:
                    discount=coupon_qset.discount_percentage
                    coupon_id=coupon_qset.id
                    coupon_message="Coupon Redeemed"
                else:
                    discount=0
                    coupon_id=0
                    coupon_message="Coupon Expired"
                print("end of excet1")
        except Exception as e:
            print(e)
            coupon_id=0
            coupon_message="Invalid Coupon"
        doctor = None
        if 'specialization' in request.data and request.data['specialization']!='':
            specialization=request.data['specialization']
     
        if 'appointment_id' in request.data and request.data['appointment_id']!="":
            try:
                doc_id=AppointmentHeader.objects.get(appointment_id=appointment_id).senior_doctor
                print(doc_id)
                if doc_id is None:
                    raise ValueError("Error doctor")
            except:
                doc_id=AppointmentHeader.objects.get(appointment_id=appointment_id).doctor_id
                print(doc_id)
            doctor =DoctorProfiles.objects.get(user_id=doc_id)

        try:
            location_id=CustomerProfile.objects.get(user_id=user_id).location
            if location_id == None:
                location_name=CustomerProfile.objects.get(user_id=user_id).residence_location
                try:
                    location_id = Locations.objects.get(location = location_name).location_id
                except:
                    location_id = Locations.objects.get(location = 'USA').location_id

            print(location_id,"location")
            print(specialization, location_id)
            if appointment_id:
                session_type = AppointmentHeader.objects.get(appointment_id= appointment_id).session_type
            else:
                session_type = request.data['session_type']
            if session_type == 'single' or session_type == 'individual':
                print('single_session')
                if specialization == 'no specialization':
                    location_id = request.data['location_id']
                    try:
                        plan = Plans.objects.get(speciality = specialization, location_id = location_id).price_for_single
                    except:
                        location_id = Locations.objects.get(location = 'USA').location_id
                        plan = Plans.objects.get(speciality = specialization, location_id = location_id).price_for_single
                else:
                    try:
                        plan=Plans.objects.get(doctor_id=doctor.doctor_profile_id,
                            location_id=location_id).price_for_single
                    except:
                        location_id = Locations.objects.get(location = 'USA').location_id
                        plan = Plans.objects.get(doctor_id=doctor.doctor_profile_id, location_id = location_id).price_for_single
            else:
                print('couple_session')
                try:
                    plan=Plans.objects.get(doctor_id=doctor.doctor_profile_id,
                        location_id=location_id).price_for_couple
                except:
                    location_id = Locations.objects.get(location = 'USA').location_id
                    plan = Plans.objects.get(doctor_id=doctor.doctor_profile_id, location_id=location_id).price_for_couple
            selected_doctor = 0
            doctor_user_id = 0
        except Exception as e:
            print("plans exception",e)
            if 'session_type' in request.data and request.data['session_type'] != '':
                session_type = request.data['session_type']
            if specialization == "no specialization":
                if 'location_id' in request.data:
                    location_id = request.data['location_id']
                    try:
                        plan=Plans.objects.get(doc_name = 'Junior doctor',location_id=location_id).price_for_single
                        print(plan)
                    except:
                        default_location_id = Locations.objects.get(location = 'USA').location_id
                        print(default_location_id)
                        plan=Plans.objects.get(doc_name = 'Junior doctor',location_id=default_location_id).price_for_single
                else:
                    default_location_id = Locations.objects.get(location = 'USA').location_id
                    print(default_location_id)
                    plan=Plans.objects.get(doc_name = 'Junior doctor',location_id=default_location_id).price_for_single
                selected_doctor = 0
                doctor_user_id = 0

            else:
                if 'location_id' in request.data:
                    location_id = request.data['location_id']
                else:
                    default_location_id = Locations.objects.get(location = 'USA').location_id

                selected_doctor = 0
                doctor_user_id = 0

                senior_doctors = SeniorDoctorAvailableTimeSLots.objects.filter(date=request.data['date'], time_slot = request.data['time'],is_active = 0)

                print(senior_doctors)
                doctors_id = []
                for users in senior_doctors:
                    try:
                        doctors = DoctorProfiles.objects.get(user_id = users.doctor_id,location = request.data['location_id'])
                        doctors_id.append(doctors.user_id)
                    except Exception as e:
                        doctors = DoctorProfiles.objects.get(user_id = users.doctor_id)
                        doctors_id.append(doctors.user_id)
                print(doctors_id)
                if len(doctors_id) == 0:
                    for users in senior_doctors:
                        doctors = DoctorProfiles.objects.get(user_id = users.doctor_id)
                        doctors_id.append(doctors.user_id)

                doctor_languages = DoctorLanguages.objects.filter(languages = request.data['language_pref'],doctor_id__in = doctors_id)
                if len(doctor_languages) == 0:
                    doctor_languages = DoctorLanguages.objects.filter(doctor_id__in = doctors_id)
                print(doctor_languages)
                doctor_id2 = []
                plans = Plans.objects.filter(location_id = location_id, speciality = specialization)
                dr_plans = []
                for plan in plans:
                    user = DoctorProfiles.objects.get(doctor_profile_id = plan.doctor_id).user_id
                    dr_plans.append(user)
                print(dr_plans)
                for users in doctor_languages:
                    if users.doctor_id not in doctor_id2 and users.doctor_id in dr_plans:
                        doctor_id2.append(users.doctor_id)
                print(doctor_id2)
                if len(doctor_id2) == 0:
                    location = Locations.objects.get(location = 'USA').location_id
                    plans = Plans.objects.filter(location_id = location, speciality = specialization)
                    dr_plans = []
                    for plan in plans:
                        user = DoctorProfiles.objects.get(doctor_profile_id = plan.doctor_id).user_id
                        dr_plans.append(user)
                    print(dr_plans)
                    for users in doctor_languages:
                        if users.doctor_id not in doctor_id2 and users.doctor_id in dr_plans:
                            doctor_id2.append(users.doctor_id)
                if request.data['gender_pref'] != "" and "gender_pref" in request.data:
                    print('gender available')
                    users = DoctorProfiles.objects.filter(user_id__in = doctor_id2, gender = request.data['gender_pref'])
                    if len(users) == 0:
                        users = DoctorProfiles.objects.filter(user_id__in = doctor_id2)
                else:
                    users = DoctorProfiles.objects.filter(user_id__in = doctor_id2)

                print(users)
                final_filter = []
                for user in users:
                    final_filter.append(user.doctor_profile_id)
                
                print('final_filter',final_filter)
                selected_doctor = final_filter[0]
                print('location_id',location_id)
                print('doctor_id',selected_doctor)
                if 'location_id' in request.data:
                    if 'session_type' in request.data and (request.data['session_type'] == 'single' or request.data['session_type'] == 'individual'):
                        try:
                            plan=Plans.objects.get(doctor_id = selected_doctor,location_id=int(location_id)).price_for_single
                        except Exception as e:
                            location = Locations.objects.get(location = 'USA').location_id
                            plan = Plans.objects.get(doctor_id = selected_doctor, location_id = location).price_for_single
                    elif request.data['session_type'] == 'couple':
                        print(selected_doctor, location_id)
                        try:
                            plan=Plans.objects.get(doctor_id = selected_doctor,location_id=int(location_id)).price_for_couple
                        except Exception as e:
                            print(e)
                            location = Locations.objects.get(location = 'USA').location_id
                            print(location)
                            plan=Plans.objects.get(doctor_id = selected_doctor,location_id=location).price_for_couple
                else:
                    default_location_id = Locations.objects.get(location = 'USA').location_id
                    if 'session_type' in request.data and (request.data['session_type'] == 'single' or request.data['session_type'] == 'individual'):
                        plan=Plans.objects.get(doctor_id = selected_doctor,location_id=default_location_id).price_for_single
                    elif request.data['session_type'] == 'couple':
                        plan=Plans.objects.get(doctor_id = selected_doctor,location_id=default_location_id).price_for_couple
        print(location_id)
        try:
            currency=Locations.objects.get(location_id=location_id).currency
        except Exception as e:
            print("locations excpetion",e)
            currency='INR'
        try:
            doctor_user_id = DoctorProfiles.objects.get(doctor_profile_id = selected_doctor).user_id
        except:
            doctor_user_id = 0
        pricing=plan-(plan*discount/100)
        price_breakup={
        "base_amount":plan,
        "taxes":0,
        "discounts":discount,
        "total":pricing ,
        "currency":currency}
        temp=TemporaryTransactionData.objects.create(vendor_fee=0,currency=currency,appointment_id=appointment_id,
        total_amount=pricing,tax=0,discount=discount,coupon_id=coupon_id,user_id=user_id
     )
    except Exception as e:
        print("payment_view_except",e)
        return Response({
            'response_code': 400,
            'status': 'Failed',
            'message': 'Invalid Specialization'
        })
    print('payment',price_breakup,
            'Coupon_Redeem_message',coupon_message,
            'coupon_id',coupon_id,
            'temp_data_id',temp.temp_id,
            'doctor_id',selected_doctor,
            'doctor_user_id',doctor_user_id,
            )
    duration = 0
    try:
        duration = Duration.objects.get(doctor_id = selected_doctor).duration
    except Exception as e:
        plan = Plans.objects.filter(doc_name = 'Junior doctor').first()
        duration = Duration.objects.get(doctor_id = plan.doctor_id).duration

    return Response({
            'response_code': 200,
            'status': 'OK',
            'message': 'Calculated Amount',
            'payment':price_breakup,
            'Coupon_Redeem_message':coupon_message,
            'coupon_id':coupon_id,
            'temp_data_id':temp.temp_id,
            'doctor_id':selected_doctor,
            'doctor_user_id':doctor_user_id,
            'duration':duration,
            'session_type':session_type
        })
    
"""Selecting answer type button """
@api_view(['POST'])
def answer_type_view(request):
   print("answer type")
   if "operation_flag" in request.data and request.data['operation_flag']=="add":
      try:
        answer_type_serializer = AnswerTypeSerializer(data=request.data)
        if answer_type_serializer.is_valid(raise_exception=True):
            answer_type_serializer.save()
            return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': "Answer type created"
            })
        return Response({
            'response_code': 400,
            'status': 'Failed to create Answer type'},
            status=status.HTTP_400_BAD_REQUEST
        )

      except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST
        )
   if "operation_flag" in request.data and request.data['operation_flag']=="view":
        try:

            answer_type_serialized = AnswerTypeSerializer(AnswerType.objects.all(), many=True).data
            return Response({
            'response_code': 200,
            'status': 'Ok',
            'data': answer_type_serialized, })
        except Exception as e:
          print(e)
          return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST
        )
   return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST
        )



"""Language Viewset"""
class CategoryViewSet(viewsets.ModelViewSet):
    queryset=Category.objects.all()
    serializer_class=CategorySerializer
    
    
    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            language = Category.objects.filter(
                pk=self.kwargs['pk']).update(**serializer.validated_data)
            return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Category Updated'},
                status=status.HTTP_201_CREATED
            )

    def destroy(self, request, *args, **kwargs):
        # serializer = self.serializer_class(data=request.data)
        # if serializer.is_valid(raise_exception=True):
        language = Category.objects.filter(pk=self.kwargs['pk'])
        language.delete()
        return Response(
            {'response_code': 200,
             'status': 'Ok',
             'message': 'Category Deleted'},
            status=status.HTTP_201_CREATED
        )
