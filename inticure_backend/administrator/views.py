
from django.contrib.auth.hashers import make_password
from multiprocessing.util import is_abstract_socket_namespace
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.core import mail
from common.filter import custom_filter
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.db.models import Sum
from django.db.models import Count
from django.db.models import OuterRef, Subquery
from django.db.models import Min
import math

# Create your views here.
from rest_framework import status,viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from datetime import datetime
# Models and Serializers
from doctor.views import get_users_name,get_doctor_specialization,\
    get_patient_medical_details
from customer.models import AppointmentRatings,CustomerProfile,Refund
from customer.serializer import AppointmentRatingsSerializer,RefundSerializer
from django.contrib.auth.models import User
from analysis.models import Options, Questionnaire,AppointmentHeader,OtpVerify,EmailOtpVerify,Invoices,\
     AppointmentQuestions, AppointmentAnswers
from doctor.models import DoctorProfiles, DoctorLanguages,DoctorMapping,Prescriptions,PrescriptionsDetail,\
    ConsumptionTime,Medications,AppointmentReshedule,AppointmentTransferHistory
from analysis.serializers import CategorySerializer, QuestionnaireSerializer, OptionsSerializer
    
from doctor.serializer import DoctorProfileSerializer,AppointmentHeaderSerializer,PrescriptionTextSerializer,\
    MedicationsSerializer,AppointmentQuestionsSerializer,AppointmentAnswersSerializer,PrescriptionSerializer
from .serializer import PlansSerializer, UserSerializer,LocationSerializer,\
    PayoutsSerializer,TransactionsSerializer,LanguageSerializer,CouponCodeSerializer,InticureEarningsSerializer
from .models import LanguagesKnown, Locations, Plans,Payouts, ReportCustomer,Transactions,TotalPayouts,\
    DiscountCoupons,TotalEarnings,InticureEarnings, Duration
from common.views import encryption_key 
from analysis.views import generateOTP
from common.twilio_test import MessageClient

from analysis.views import get_currency,get_doctor_location,get_user_mail, get_duration
from common.views import get_category_name

sms_service = MessageClient()

@api_view(['POST'])
def contact_form_submission(request):
    # Extract data from request
    name = request.data.get('name')
    email = request.data.get('email')
    phone_number = request.data.get('number')
    message = request.data.get('message')

    # Define email content
    email_subject = f"Contact Form Submission from {name}"
    email_body = (
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Phone Number: {phone_number}\n"
        f"Message:\n{message}"
    )

    # Send email
    mail.send_mail(
        email_subject,
        email_body,
        'your_email@example.com',  # Sender's email
        ['your_recipient_email@example.com'],  # Recipient email
        fail_silently=False,
    )

    return JsonResponse({'message': 'Email sent successfully'}, status=status.HTTP_200_OK)

def get_customer_location(customer_id):
    try:
        location=CustomerProfile.objects.get(user_id=customer_id).location
        
    except Exception as e :
        print(e)
        location=1
    return location

@api_view(['POST'])
def sign_in_view(request):
    username = request.data['username']
    password = request.data['password']
    print(username, password)
    account = authenticate(username=username, password=password)
    print(account)
    is_senior=0
    id_doc=0
    id_jr_doc=0
    id_usr=0
    gender=""
    languages_known=""
    try:
        user=User.objects.get(username=username)
        id_usr=user.id
        print('users',id_usr)
    except Exception as e:
        print("Except",e)
        return Response({
            'response_code': 401,
            'status': 'Unauthorized',
            'message': 'Username/password combination invalid.'
        }, status=status.HTTP_401_UNAUTHORIZED)
    try:
        is_seniors=DoctorProfiles.objects.get(doctor_flag='senior',user_id=id_usr)
        id_doc=is_seniors.user_id
        gender=is_senior.gender
        languages_known=is_senior.languages_known
    except:
        is_seniors=None
    try:
        is_junior=DoctorProfiles.objects.get(doctor_flag='junior',user_id=id_usr)
        id_jr_doc=is_junior.user_id
        gender=is_junior.gender
        languages_known=is_junior.languages_known
    except:
        is_junior=None
    print(is_seniors)
    if account is not None:
        if account.is_active:
            if id_usr == id_doc:
               is_senior=1
            elif id_usr==id_jr_doc:
                is_senior=2
            login(request, account)
            return Response({
                'response_code': 200,
                'message': 'login successfull',
                'doctor_flag':is_senior,
                'user_id':id_usr,
                'gender':gender,
                'languages_known':languages_known })
        else:
            return Response({
                'response_code': 401,
                'status': 'Unauthorized',
                'message': 'This account is Unauthorized'
            }, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({
            'response_code': 401,
            'status': 'Unauthorized',
            'message': 'Username/password combination invalid.'
        }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def sign_in_otp_view(request):
    print("otp_login")
    print(request.data)
    OTP=""
    id_doc=0
    id_jr_doc=0
    gender=""
    is_senior=0
    languages_known=""
    user_flag=""
    if "mobile_num" in request.data and "otp" not in request.data :
        try:
            try:
                user_id=CustomerProfile.objects.get(mobile_number=request.data['mobile_num']).user_id
                print(user_id)
                user_flag="customer"
                print('customer')
            except Exception as e:
                print(e)
                user_id=None
            if user_id == None:
                try:
                    user_id=DoctorProfiles.objects.get(mobile_number=request.data['mobile_num']).user_id
                    print(user_id)
                    print('doctor')
                except Exception as e:
                    print(e)
                    if user_flag=="":
                        user_id=None
            print('user_id',user_id)
            if user_id != None:   
                OTP=generateOTP()
                print(OTP)
                try:
                    otp_verrify=OtpVerify.objects.get(
                    mobile_number=request.data['mobile_num'])
                    otp_verrify.otp = OTP
                    otp_verrify.save()
                except:
                    OtpVerify.objects.create(
                        mobile_number=request.data['mobile_num'],otp=OTP)
                print("OTP",OTP)
                
                if User.objects.get(id=user_id).is_active==0:
                        return Response({
                        'response_code': 400,
                        'status': 'Failed',
                        'message': 'User Banned'},
                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    pass
                try:    
                    sms_service.send_message("Hi There, Your OTP for LogIn is:%s"%OTP,
                    "+91" + str(request.data['mobile_num']))
                except:
                    print("MESSAGE SENT ERROR")
                return Response({
                 'response_code': 200,
                    'status': 'Success',
                    'message': 'OTP Generated',
                    'otp':OTP})
            else:
                print("USER_NONE")
                return Response({
                 'response_code': 400,
                    'status': 'Failed',
                    'message': 'Invalid User'},
                    status=status.HTTP_400_BAD_REQUEST)
            # sms_service.send_message("Hello Your OTP for LogIn is:%s"%OTP,
            #      "+91" + str(request.data['mobile_num']))
            # return Response({
            #      'response_code': 200,
            #         'status': 'Success',
            #         'message': 'OTP Generated',
            #         'otp':OTP})
            
        except Exception as e:
            print(e)
            return Response({
                 'response_code': 400,
                    'status': 'Failed',
                    'message': 'Invalid User'},
                    status=status.HTTP_400_BAD_REQUEST)
    if "email" in request.data and "otp" not in request.data :
        print('email')
        try:
            user_id=User.objects.get(email=request.data['email']).id
            OTP=generateOTP()
            try:
                otp_verify = EmailOtpVerify.objects.get(
                email=request.data['email'])
                otp_verify.otp = OTP
                otp_verify.save()
            except Exception as e:
                print(e)
                EmailOtpVerify.objects.create(
                    email=request.data['email'],otp=OTP)
            print("OTP",OTP)

            if User.objects.get(id=user_id).is_active==0:
                    print('user object entererd')
                    return Response({
                    'response_code': 400,
                    'status': 'Failed',
                    'message': 'User Banned'},
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                print('invalid otp verification')
                subject = 'Inticure OTP Verification'
                html_message = render_to_string('email_otp.html', {'email':request.data['email'],
                 "confirm":0,"OTP":OTP })
                plain_message = strip_tags(html_message)
                # plain_message="account-created"
                from_email = 'wecare@inticure.com'
                to = request.data['email']
                cc = 'nextbighealthcare@inticure.com'
                mail.send_mail(subject, plain_message, from_email, [to], [cc],html_message=html_message)
                return Response({
                 'response_code': 200,
                    'status': 'Success',
                    'message': 'OTP Generated',
                    'otp':OTP})
            # sms_service.send_message("Hello Your OTP for LogIn is:%s"%OTP,
            #      "+91" + str(request.data['mobile_num']))
            # return Response({
            #      'response_code': 200,
            #         'status': 'Success',
            #         'message': 'OTP Generated',
            #         'otp':OTP})
            
        except Exception as e:
            print(e)
            return Response({
                 'response_code': 400,
                    'status': 'Failed',
                    'message': 'Invalid User'},
                    status=status.HTTP_400_BAD_REQUEST)
    if "resend" in request.data:
        try:
            OTP=OtpVerify.objects.get(mobile_number=request.data['mobile_num']).otp
            sms_service.send_message("Hi There, Your OTP for LogIn is:%s"%OTP,
                "+91" + str(request.data['mobile_num']))
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
        try:
            if "mobile_num" in request.data and request.data['mobile_num']!="":
               OtpVerify.objects.get(mobile_number=request.data['mobile_num'],otp=request.data['otp'])
               OtpVerify.objects.get(mobile_number=request.data['mobile_num'],otp=request.data['otp']).delete()
               try:
                  user_id=CustomerProfile.objects.get(mobile_number=request.data['mobile_num']).user_id
               except:
                  user_id=DoctorProfiles.objects.get(mobile_number=request.data['mobile_num']).user_id
            if "email" in request.data and request.data['email']!="":
                EmailOtpVerify.objects.get(email=request.data['email'],otp=request.data['otp'])
                EmailOtpVerify.objects.get(email=request.data['email'],otp=request.data['otp']).delete()
                user_id=User.objects.get(email=request.data['email']).id
                
                subject = 'Login Confirmation'
                html_message = render_to_string('email_otp.html', {'email':request.data['email'],
                 "confirm":1 })
                plain_message = strip_tags(html_message)
                # plain_message="account-created"
                from_email = 'wecare@inticure.com'
                to = request.data['email']
                cc = 'nextbighealthcare@inticure.com'
                mail.send_mail(subject, plain_message, from_email, [to], [cc],html_message=html_message)
            try:
               is_seniors=DoctorProfiles.objects.get(doctor_flag='senior',user_id=user_id)
               id_doc=is_seniors.user_id
               gender=is_seniors.gender
               languages_known=is_seniors.languages_known
            except:
               is_seniors=None
            try:
                is_junior=DoctorProfiles.objects.get(doctor_flag='junior',user_id=user_id)
                id_jr_doc=is_junior.user_id
                gender=is_junior.gender
                languages_known=is_junior.languages_known
            except:
                is_junior=None
            if user_id == id_doc:
               is_senior=1
            elif user_id==id_jr_doc:
                is_senior=2
            return Response({
                 'response_code': 200,
                    'status': 'Success',
                    'message': 'OTP Verified',
                    'doctor_flag':is_senior,
                    'user_id':user_id,
                    'gender':gender,
                    'languages_known':languages_known })
        except Exception as e:
            print(e)
            return Response({
                 'response_code': 400,
                    'status': 'Failed',
                    'message': 'Otp Incorrect '},
                    status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_view(request):
    try:
        logout(request)
        request.session.flush()
        return Response({
            'response_code': 200,
            'message': 'User logged out',
        })
    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'message': 'logout failed'
        })


@api_view(['POST'])
def create_questions_view(request):
    try:
        questionnaire_serializer = QuestionnaireSerializer(data=request.data)
        if questionnaire_serializer.is_valid(raise_exception=True):
            question_save = questionnaire_serializer.save()
            for option in request.data['options']:
                Options.objects.create(option=option, question_id=question_save.id)
            return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': "Question created"
            })
        return Response({
            'response_code': 400,
            'status': 'Failed to create question'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def update_questions_view(request):
    try:
        questionnaire_serializer = QuestionnaireSerializer(data=request.data)
        if questionnaire_serializer.is_valid(raise_exception=True):
            Questionnaire.objects.filter(pk=request.data['question_id']).update(
                **questionnaire_serializer.validated_data)
            if 'option' in request.data and request.data['option']!="":
                for option in request.data['option']:
                    Options.objects.create(option=option, question_id=request.data['question_id'])
            
            return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': "Question updated"
            })
        return Response({
            'response_code': 400,
            'status': 'Failed to update question'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def remove_question_view(request):
    Questionnaire.objects.filter(pk=request.data['question_id']).delete()
    Options.objects.filter(question_id=request.data['question_id']).delete()
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Question removed"
    })
from django.http import JsonResponse

@api_view(['GET'])
def get_price(request):
    location_id = request.GET.get('location_id')
    plan_id = request.GET.get('plan_id')     
    print(location_id, plan_id)
    try:
        plan = Plans.objects.get(doctor_id = plan_id, location_id = location_id)
        data = {'price_for_single':plan.price_for_single,'price_for_couple':plan.price_for_couple,'currency':get_currency(plan.location_id)}
        return JsonResponse(data)  
    
    except Exception as e:
        print(e)
    return Response({
        'response_code':404,
        'status':'failed',
        'data':None
    })

@api_view(['POST'])
def get_plan(request):
    plan_id = request.data['plan_id']
    location_id = request.data['location_id']
    print(location_id, plan_id)
    try:
        plan = Plans.objects.get(doctor_id = plan_id, location_id = location_id)
        data = {'plan_id':plan.id,'doctor_name':plan.doc_name,'speciality':plan.speciality,'price_for_single':plan.price_for_single,'price_for_couple':plan.price_for_couple,'currency':get_currency(plan.location_id)}
        location = Locations.objects.get(location_id = location_id)
        data['location_name'] = location.location
        return JsonResponse(data)  
    
    except Exception as e:
        print(e)
    return Response({
        'response_code':404,
        'status':'failed',
        'data':None
    })

@api_view(['POST'])
def edit_plan(request):
    try:
        doc_id = request.data['doc_id']
        location = request.data['location_id']
        price_for_single = request.data['price_for_single']
        price_for_couple = request.data['price_for_couple']
        doctor = DoctorProfiles.objects.get(doctor_profile_id = doc_id)
        user = User.objects.get(id = doctor.user_id)
        plan = Plans.objects.filter(doctor_id=doc_id, location_id=location).update(
                price_for_single=price_for_single,
                price_for_couple=price_for_couple,
                speciality=doctor.specialization,
                doc_name=f'{user.first_name} {user.last_name}'
            )
        return Response({
            'response_code':200,
            'status':'ok',
            'message': "plan updated"
        })
    except Exception as e:
        print(e)
        return Response({
        'response_code':404,
        'status':'failed',
        'message':e
    })

@api_view(['POST'])
def remove_plan(request):
    try:
        doc_id = request.data['doc_id']
        location = request.data['location_id']
        plan = Plans.objects.get(doctor_id=doc_id, location_id=location)
        plan.delete()
        return Response({
            'response_code':200,
            'status':'ok',
            'message': "plan deleted"
        })
    except Exception as e:
        print(e)
        return Response({
        'response_code':404,
        'status':'failed',
        'message':str(e)
    })

@api_view(['POST'])
def get_location(request):
    try:
        try:
            location = Locations.objects.get(location = request.data['location']).location_id
            if location is None:
                location = Locations.objects.get(location = 'Default').location_id
        except:
            location = Locations.objects.get(location = 'Default').location_id

        return Response({
            'response_code':200,
            'status':'ok',
            'location_id':location
        })
    except Exception as e:
        print(e)
        return Response({
            'response_code':400,
            'status':'failed',
            'message':str(e)
        })

@api_view(['POST'])
def update_option_view(request):
    try:
        option_serializer = OptionsSerializer(data=request.data)
        if option_serializer.is_valid(raise_exception=True):
            Options.objects.filter(pk=request.data['option_id']).update(
                **option_serializer.validated_data)
            return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': "Option updated"
            })
        return Response({
            'response_code': 400,
            'status': 'Failed to update Option'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(e)
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
def remove_option_view(request):
    Options.objects.filter(pk=request.data['option_id']).delete()
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message': "Option removed"
    })
"""Doctor Profile Creation"""
def create_user(email,doc_fname,doc_lname,location,specialization,mobile_num,gender,qualification,address,certificate_no,doctor_bio):
    try:
        print('449 ',email,doc_fname,doc_lname,location,specialization,mobile_num,gender,qualification,address,certificate_no,doctor_bio)
        try:
            user_queryset = User.objects.filter(email=email)
        except Exception as e:
            print(e)
            user_queryset = 0

        if user_queryset.exists():
            print('asdfasdf')
            return 0
        else:
            user = User.objects.create_user(username=email, password=email, email=email,
            first_name=doc_fname,last_name=doc_lname)
            print(user)
            print('tryurtyu')
            DoctorProfiles.objects.create(user_id=user.id,
            specialization=specialization,mobile_number=mobile_num,location=location,
            department="all",gender=gender,qualification=qualification,address=address,
            certificate_no=certificate_no,doctor_bio=doctor_bio)
            print('uyioyuio')

            try:
                print('ertyvbn')
                print(encryption_key.encrypt(str(user.id).encode()))
                print('yutnmm')
                user_id=encryption_key.encrypt(str(user.id).encode())
                print('ytu45gf')
                subject = 'inticure account creation'
                html_message = render_to_string('account_creation_update.html', {'email': email,
                'user_id':user_id.decode()})
                plain_message = strip_tags(html_message)
                # plain_message="account-created"
                to = email
                cc = 'nextbighealthcare@inticure.com'
                from_email = 'wecare@inticure.com'

                try:
                    print('Encrypted user_id:', user_id.decode())  # Verify if this step is working
                    mail.send_mail(subject, plain_message, from_email, [to], [cc],html_message=html_message,fail_silently=False)
                except Exception as e:
                    print(f"Error in sending email: {str(e)}")

                return user.id
            except Exception as e:
                print(e)
                return 0
    except Exception as e:
        print(e)
        return 0

"""View for Adding a New Doctor"""
@api_view(['POST'])
def doctor_create_view(request):
    print(request.data)
    try:
        user = request.data['user_id']
        if not user:
            user = request.data['new_user']
        print(user)
        if user == 1:
            user_id = create_user(request.data['email'],request.data['doc_fname'],
                                   request.data['doc_lname'],
                                   request.data['location'],request.data['specialization'],
                                   request.data['mobile_num'],request.data['gender'],
                                   request.data['qualification'],request.data['address'],
                                   request.data['certificate_no'],request.data['doctor_bio'])
            if not user_id:
                return Response({
                    'response_code': 400,
                    'status': 'Failed',
                    'message': 'Email id Exists'
                },
                    status=status.HTTP_400_BAD_REQUEST)
            print(user_id)
            for language in request.data['language_known']:
                DoctorLanguages.objects.create(doctor_id=user_id,languages=language)
           
            if "registration_certificate" in request.data and request.data['registration_certificate'] != "":
                registration_certificate=request.data['registration_certificate']
                DoctorProfiles.objects.filter(user_id=user_id).update(registration_certificate=registration_certificate,
                reg_file_name=request.data['reg_file_name'],reg_file_size=request.data['reg_file_size'])

            if "address_proof" in request.data and request.data['address_proof'] != "":
                address_proof=request.data['address_proof']
                DoctorProfiles.objects.filter(user_id=user_id).update(address_proof=address_proof,
                addr_file_name=request.data['addr_file_name'],addr_file_size=request.data['addr_file_size'])  

            if "signature" in request.data and request.data['signature'] != "":
                signature=request.data['signature']
                DoctorProfiles.objects.filter(user_id=user_id).update(signature=signature,
                sign_file_name=request.data['sign_file_name'],sign_file_size=request.data['sign_file_size'])  
            
            if "profile_pic" in request.data and request.data['profile_pic'] != "":
                profile_pic=request.data['profile_pic']
                DoctorProfiles.objects.filter(user_id=user_id).update(profile_pic=profile_pic,
                profile_file_name=request.data['profile_file_name'],profile_file_size=request.data['profile_file_size'])
        
        return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': 'New Doctor Added'
            })

    except Exception as e:
        print("except",e)
        return Response({
            'response_code': 400,
            'status': 'Failed'},
            status=status.HTTP_400_BAD_REQUEST)
        
"""Listing all doctors registered in Inticure APP"""
@api_view(['POST'])
def doctor_list_view(request):
    filter={}
    try:
        if('user_id' in request.data and request.data['user_id'] !=''):
            filter['user_id']=request.data['user_id']
        if('location' in request.data and request.data['location'] !=''):
            filter['location']=request.data['location']
        if('gender' in request.data and request.data['gender'] !=''):
            filter['gender']=request.data['gender']
        if('is_accepted' in request.data and request.data['is_accepted'] !=''):
            filter['is_accepted']=request.data['is_accepted']
        if('doctor_flag' in request.data and request.data['doctor_flag'] !=''):
            filter['doctor_flag']=request.data['doctor_flag']
        if('specialization' in request.data and request.data["specialization"]!=''):
           filter['specialization'] = request.data['specialization']
        queryset = custom_filter(DoctorProfiles, filter)
        doctors=DoctorProfileSerializer(queryset,many=True).data
        # print(doctors)
        for user in doctors:
           user_id=user['user_id']
        #    print(user_id)
           try:  
              queryset_user=User.objects.get(id=user_id)
            #   print(queryset_user)
            #   print(user['location'])
              user['user_fname']=queryset_user.first_name
              user['user_lname']=queryset_user.last_name
              user['user_mail']=queryset_user.email
              try:
                user['location']=Locations.objects.get(location_id=user['location']).location
              except:
                user['location']=""
              try:
                doctor_languages=[]
                doctor_obj=DoctorLanguages.objects.filter(doctor_id=user['user_id'])
                for doctor_lang in doctor_obj:
                    # print("lang",doctor_lang.languages)
                    doctor_languages.append(doctor_lang.languages)
                user['language_known']=doctor_languages
              except:
                  user['language_known']=""
           except:
              user['user_fname']=""
              user['user_lname']=""
              user['user_mail']=""

        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': doctors
    })
    except Exception as e:
        print('except',e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Doctors List None"
    })

"""Doctor Profile Edit View"""
@api_view(['POST'])
def doctor_profile_edit_view(request):
    if "edit" in request.data["operation_flag"]: 
      if "user_id" in request.data and request.data['user_id'] !='':
        
        user_id=request.data['user_id']
        if "user_fname" in request.data and request.data['user_fname'] !="":
          user_fname=request.data['user_fname']
          User.objects.filter(id=user_id).update(first_name=user_fname)
        
        if "user_lname" in request.data and request.data['user_lname'] !="":
          user_lname=request.data['user_lname']
          User.objects.filter(id=user_id).update(last_name=user_lname)
        
        if "user_mail" in request.data and request.data['user_mail'] != "":
           user_mail=request.data['user_mail']  
           User.objects.filter(id=user_id).update(email=user_mail)
        
        if "location" in request.data and request.data['location'] != "":
           DoctorProfiles.objects.filter(user_id=user_id).update(location=request.data['location'])
       
        if "qualification" in request.data and request.data['qualification'] != "":
           DoctorProfiles.objects.filter(user_id=user_id).update(qualification=request.data['qualification'])
       
        if "address" in request.data and request.data['address'] != "":
           DoctorProfiles.objects.filter(user_id=user_id).update(address=request.data['address'])
        if "doctor_bio" in request.data and request.data['doctor_bio'] != "":
           DoctorProfiles.objects.filter(user_id=user_id).update(doctor_bio=request.data['doctor_bio'])

        if "language_known" in request.data and request.data['language_known'] and request.data['language_known'] != "":
          # DoctorProfiles.objects.filter(user_id=user_id).update(language_known=request.data['language_known'])
            DoctorLanguages.objects.filter(doctor_id=user_id).delete()
            for language in request.data['language_known']:
                DoctorLanguages.objects.create(doctor_id=user_id,languages=language)
        if "gender" in request.data and request.data['gender'] != "":
          DoctorProfiles.objects.filter(user_id=user_id).update(gender=request.data['gender'])
        
        if "specialization" in request.data and request.data['specialization'] != "":
          DoctorProfiles.objects.filter(user_id=user_id).update(specialization=request.data['specialization'])
        
        if "doctor_flag" in request.data and request.data['doctor_flag'] != "":
          DoctorProfiles.objects.filter(user_id=user_id).update(doctor_flag=request.data['doctor_flag'])

        if "mobile_num" in request.data and request.data['mobile_num'] != "":
          mobile_num=request.data['mobile_num']
          DoctorProfiles.objects.filter(user_id=user_id).update(mobile_number=mobile_num)
        
        if "registration_certificate" in request.data and request.data['registration_certificate'] != "":
                registration_certificate=request.data['registration_certificate']
                DoctorProfiles.objects.filter(user_id=user_id).update(registration_certificate=registration_certificate,
                reg_file_name=request.data['reg_file_name'],reg_file_size=request.data['reg_file_size'])

        if "address_proof" in request.data and request.data['address_proof'] != "":
                address_proof=request.data['address_proof']
                DoctorProfiles.objects.filter(user_id=user_id).update(address_proof=address_proof,
                addr_file_name=request.data['addr_file_name'],addr_file_size=request.data['addr_file_size'])  

        if "signature" in request.data and request.data['signature'] != "":
                signature=request.data['signature']
                DoctorProfiles.objects.filter(user_id=user_id).update(signature=signature,
                sign_file_name=request.data['sign_file_name'],sign_file_size=request.data['sign_file_size'])  
            
        if "profile_pic" in request.data and request.data['profile_pic'] != "":
                profile_pic=request.data['profile_pic']
                DoctorProfiles.objects.filter(user_id=user_id).update(profile_pic=profile_pic,
                profile_file_name=request.data['profile_file_name'],profile_file_size=request.data['profile_file_size'])

        if "certificate_no" in request.data and request.data['certificate_no'] != "" :
            DoctorProfiles.objects.filter(user_id=user_id).update(certificate_no=request.data['certificate_no'])
        
        # if "time_from" in request.data and request.data['time_from'] != "" and "time_to" in request.data and request.data['time_to'] != "" :
        #      DoctorProfiles.objects.filter(user_id=user_id).update(time_slot_from=request.data['time_from'],time_slot_to=request.data['time_to'],)
        
        return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Doctor Profile Updated'},
                status=status.HTTP_201_CREATED)
    elif "delete" in request.data["operation_flag"]:
        user_id=request.data['user_id']
        User.objects.filter(id=user_id).delete()
        DoctorProfiles.objects.filter(user_id=user_id).delete()
        return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Doctor Deleted'})
    else:    
        return Response(
                {'response_code': 400,
                 'status': 'Ok',
                 'message': 'Invalid UserID'})


@api_view(['POST'])
def payout_list_view(request):
    payouts_list=[]
    filter={}
    total_earning_curr=0
    total_earning=0
    total_payouts_curr=0
    total_payouts=0
    earnings=0
    current_month = datetime.now().month
    total_payout=TotalPayouts.objects.filter(payout_date__month=current_month)
    print("payount in  month",total_payout)
    try:
        print("tr_y")
        if 'payout_status' in request.data and request.data['payout_status']!="":
            print("status-filter")
            filter['payout_status']=request.data['payout_status']
        if 'doctor_id' in request.data and request.data['doctor_id']!="":
            filter['doctor_id']=request.data['doctor_id']
            try:
                print("curr total payot")
                total_payouts_curr=Payouts.objects.filter(
                doctor_id=request.data['doctor_id'],payout_date__month=current_month).aggregate(Sum('payout_amount'))['payout_amount__sum']
                print("totalpayout curr",total_payouts_curr)
            except Exception as e :
                print(e)
                total_payouts_curr=0
            try:
               total_payouts=TotalPayouts.objects.get(doctor_id=request.data['doctor_id']).total_payouts
               print("payouts",total_payouts)
            except Exception as e :
               print("payouts",e)
               total_payouts=0
            try:
               total_earning_curr=Payouts.objects.filter(payout_status=1,
                doctor_id=request.data['doctor_id'],accepted_date__month=current_month).aggregate(Sum('payout_amount'))['payout_amount__sum']
               print("total_earning_curr",total_earning_curr,total_earning_curr) 
            except Exception as e :
                print(e)
                total_earning_curr=0
            try:
               total_earning=TotalEarnings.objects.get(doctor_id=request.data['doctor_id']).total_earnings
               print("earnings",total_earning)
            except Exception as e:
                print(e)
                total_earning=0
            earnings=PayoutsSerializer(
               Payouts.objects.filter(doctor_id=request.data['doctor_id'],payout_status=1),many=True).data
            print(earnings,total_earning,"eranings","totl earings")
            for user in earnings:
                user_id=user['doctor_id']
                try:  
                       user['earnings_doctor_name']=get_users_name(user_id)
                except:
                      user['earnings_doctor_name']=""
                user['currency']=get_currency(get_doctor_location(user['doctor_id']))
                if 'currency' in request.data and request.data['currency'] !="":
                        if user['currency'] ==  request.data['currency']:
                            payouts_list.append(user)
                else:
                        payouts_list.append(user)
                   
        else:
            earnings=PayoutsSerializer(
            Payouts.objects.filter(payout_status=1),many=True).data
            print(earnings)
            for user in earnings:
                user_id=user['doctor_id']
                try:  
                    user['earnings_doctor_name']=get_users_name(user_id)
                except:
                    user['earnings_doctor_name']=""
                user['currency']=get_currency(get_doctor_location(user['doctor_id']))
                if 'currency' in request.data and request.data['currency'] !="":
                    if user['currency'] ==  request.data['currency']:
                        payouts_list.append(user)
                else:
                    payouts_list.append(user)
        queryset = custom_filter(Payouts, filter)
        payouts=PayoutsSerializer(queryset,many=True).data
        for user in payouts:
           user_id=user['doctor_id']
           try:  
              user['doctor_name']=get_users_name(user_id)
           except:
              user['doctor_name']=""
           user['currency']=get_currency(get_doctor_location(user['doctor_id']))
           if 'currency' in request.data and request.data['currency'] !="":
               if user['currency'] ==  request.data['currency']:
                   payouts_list.append(user)
           else:
                payouts_list.append(user)
        if total_earning_curr == None:
            total_earning_curr=0
        if total_payouts_curr == None:
            total_payouts_curr=0
        payout={
            "payouts":payouts_list,
            "earnings":earnings,
            "total_payouts_curr":total_payouts_curr,
            "total_payouts":total_payouts,
            "total_earning_curr":total_earning_curr,
            "total_earning":total_earning
        }
        print(payout)
        print(total_payouts_curr)
        print(total_payout)
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': payout
    })
    except Exception as e:
        print("payout_exception",e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Payout List None"
    })
        

@api_view(['POST'])
def payout_detail_view(request):
    filter={}
    try:
        # filter['payout_id']=request.data['payout_id']
        queryset = Payouts.objects.get(payout_id=request.data['payout_id'])
        payouts=PayoutsSerializer(queryset).data
        try:  
              payouts['doctor_name']=get_users_name(payouts['doctor_id'])
        except Exception as e:
              payouts['doctor_name']=""
        print(payouts)
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': payouts
    })
    except Exception as e:
        print("payout_exception",e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Invalid Payout ID"
    })

def get_doctor_id(invoice_id):
    try:
        doctor_id=Invoices.objects.get(invoice_id=invoice_id).doctor_id
    except Exception as e:
        print(e)
        doctor_id=0
        
@api_view(['POST'])
def transaction_list_view(request):
    filter={}
    transaction_list=[]
    try:
        
            
        queryset = Transactions.objects.filter(**filter)
        transaction=TransactionsSerializer(queryset,many=True).data
        print(transaction)
        for data in transaction:
            doctor_id=get_doctor_id(data['invoice_id'])
            data['currency']=get_currency(get_doctor_location(doctor_id))
            if 'currency' in request.data and request.data['currency']!="":
                if data['currency'] == request.data['currency']:
                    transaction_list.append(data)
            else:
                transaction_list.append(data)
            
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': transaction_list
    })
    except Exception as e:
        print("transaction_exception",e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"List None"
    })

@api_view(['POST'])
def transaction_detail_view(request):
    filter={}
    try:
        filter['transaction_id']=request.data['transaction_id']
        queryset = custom_filter(Transactions, filter)
        transactions=TransactionsSerializer(queryset,many=True).data
        print(transactions)
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': transactions
    })
    except Exception as e:
        print("transaction_exception",e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Invalid Transaction ID"
    })

"""Reporting Customer for bad behaviour"""
@api_view(['POST'])
def report_customer_view(request):
    print('report_customer')
    report_count=0
    try:
        print("try")
        customer_qset=ReportCustomer.objects.get(customer_id=request.data['customer_id'])
        report_count=customer_qset.report_count
        user_mail=User.objects.get(id=request.data['customer_id']).email
        print("email")
    except Exception as e:
        print('except',e)
        customer_qset=None
        report_count=0
        user_mail=User.objects.get(id=request.data['customer_id']).email
    if customer_qset:    
        print(customer_qset)
        print("yep",type(report_count))
        if report_count:
            report_count+=1
        else:
            report_count=0
        ReportCustomer.objects.filter(customer_id=request.data['customer_id']).update(
            appointment_id=request.data['appointment_id'],
            customer_id=request.data['customer_id'],
            doctor_id=request.data['doctor_id'],
            report_count=report_count
        )
        if report_count==2:
            try:
                subject = 'User Banned'
                html_message = render_to_string('user_banned.html', {
                'email':user_mail})
                plain_message = strip_tags(html_message)
                to =  user_mail
                cc = 'nextbighealthcare@inticure.com'
                from_email = 'wecare@inticure.com'
                mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)
                user=User.objects.get(id=request.data['customer_id'])
                user.is_active= False
                user.save()
                return Response({
              'response_code': 200,
               'status': 'Ok',
               'message':'Customer Banned'
                })
            except Exception as e:
                print("report_customer_except",e)  
        else:
            subject = 'Oh no…You have been reported'
            html_message = render_to_string('report_customer.html', {"doctor_flag":0,
                'name':get_users_name(request.data['customer_id'])})
            plain_message = strip_tags(html_message)
            from_email = 'wecare@inticure.com'
            cc = "nextbighealthcare@inticure.com"
            to =  user_mail
            mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)
            specialization=DoctorProfiles.objects.get(user_id=request.data['doctor_id']).specialization
            if specialization=="junior":
                salutation="Dr"
            else:
                salutation=""
            subject = 'Action initiated against your patient'
            html_message = render_to_string('report_customer.html', {"doctor_flag":1,
            "name":get_users_name(request.data['customer_id']),
            'doctor_name':get_users_name(request.data['doctor_id']),"salutation":salutation })
            plain_message = strip_tags(html_message)
            from_email = 'wecare@inticure.com'
            to =  get_user_mail(request.data['doctor_id'])
            cc = "nextbighealthcare@inticure.com"
            mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)
 
    else:
       report_count+=1
       ReportCustomer.objects.create(
            appointment_id=request.data['appointment_id'],
            customer_id=request.data['customer_id'],
            doctor_id=request.data['doctor_id'],report_count=report_count)
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':'Customer Reported'
    })


"""Forgot Password API"""
@api_view(['POST'])
def forgot_password_view(request):
        print("forgot-password")
        encrypted_user_id=0
        try:
           user_id=User.objects.get(email=request.data['email']).id
           encrypted_user_id= encryption_key.encrypt(str(user_id).encode())
        except Exception as e:
            print(e)
            return Response({
        'response_code': 400,
        'status': 'Failed',
        'message':'Invalid Email' })

        subject = 'Password Reset'
        html_message = render_to_string('forget_password.html', {"email":request.data['email'],
        "encrypted_id":encrypted_user_id.decode()})
        plain_message = strip_tags(html_message)
        from_email = 'wecare@inticure.com'
        to = request.data['email']
        cc = "nextbighealthcare@inticure.com"
        mail.send_mail(subject, plain_message, from_email, [to], [cc], html_message=html_message)

        return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':'Password reset email sent'
    })

"""Actions for doctor Application"""
@api_view(['POST'])
def application_action_view(request):
   user_id=request.data['user_id']
   if "is_accepted" in request.data and request.data['is_accepted'] != "":
          is_accepted=request.data['is_accepted']
          if is_accepted==1:
              print("1")
              DoctorProfiles.objects.filter(user_id=user_id).update(
            is_accepted=is_accepted,doctor_flag=request.data['doctor_flag'])
              doctor = DoctorProfiles.objects.get(user_id=user_id)
            #   if request.data['doctor_flag'] == 'senior':
            #       plan = Plans.objects.create(price_for_single = request.data['fee'], price_for_couple = math.ceil(request.data['fee']), speciality = doctor.specialization, location_id = doctor.location, doctor_id = doctor.id)
          else:
              print("0")
              DoctorProfiles.objects.filter(user_id=user_id).update(is_accepted=is_accepted)
          print(encryption_key.encrypt(str(user_id).encode()))
          encrypt_user_id=encryption_key.encrypt(str(user_id).encode())
          subject=''
          if is_accepted==1:
            subject = 'Welcome to the inticure family!'
          if is_accepted==0:
            print("is accept....0")
            subject = 'Application Rejected!'
          html_message = render_to_string('account_creation_update.html', {'doctor_name':get_users_name(user_id),
          "is_accepted":is_accepted,'salutation':'Dr'})
          plain_message = strip_tags(html_message)
          # plain_message="account-created"
          from_email = 'wecare@inticure.com'
          to = get_user_mail(user_id)
          cc = "nextbighealthcare@inticure.com"
          print("here")
          mail.send_mail(subject, plain_message, from_email, [to],[cc],html_message=html_message)
          return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':'Application Decision Made'
    })
"""Forgot Password API"""
@api_view(['POST'])
def password_change_view(request):
        print("forgot-password-change")
        # message=request.data['user_id']
        # encMessage = encryption_key.encrypt(str(message).encode())
        
        # print("original string: ", message)
        # print("encrypted string: ", encMessage)
        print(encryption_key.decrypt(request.data['user_id']))
        user_id= encryption_key.decrypt(request.data['user_id']).decode()
        try:
            password=make_password(request.data['password'],hasher='default')
            User.objects.filter(id=int(user_id)).update(password=password)
            return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':'Password changed',
        'user_id':int(user_id)
    })
        except Exception as e:
            print(e)
            return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':'Error Could not Change Password'
    })
        # print("decrypted string: ", int(user_id))

        # subject = 'Password Reset'
        # html_message = render_to_string('forgot_password.html', {"email":request.data['email']})
        # plain_message = strip_tags(html_message)
        # from_email = 'Inticure <hello@inticure.com>'
        # to = request.data['email']
        # mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)

"""admin settings view"""
@api_view(['POST'])
def settings_view(request):
    print("settings Updations")
    return Response({
         'response_code': 200,
         'status': 'Success',
         'message': 'Settings Updation Success'
    })

"""admin dashboard view"""
@api_view(['POST'])
def admin_dashboard_view(request):
    print("dashboard api")
    return Response({
         'response_code': 200,
         'status': 'Success',
         'message': 'Settings Updation Success'
    })
"""Update payouts to Earnings"""
@api_view(['POST'])
def earnings_view(request):
    print("earnings api")
    doctor=request.data['doctor_id']
    payout_id=request.data['payout_id']
    current_date=datetime.today().date()
    current_time=datetime.now().time()
    try:
       doctor_fee=Payouts.objects.get(payout_id=payout_id).payout_amount
    except Exception as e:
         print(e)
         return Response({
                'response_code': 400,
                'status': 'Failed',
                'message': 'Doctor Earnings Updation Failed'},
                status=status.HTTP_201_CREATED
            )
    try:
            print("earnings_calc")
            total=TotalEarnings.objects.get(doctor_id=doctor)
            print("toatsl",total)
            TotalEarnings.objects.filter(doctor_id=doctor).update(
            doctor_id=doctor,total_earnings=doctor_fee)

    except Exception as e:
            print(e)
            print("exception",doctor)
            total_earnings=doctor_fee
            earnings=TotalEarnings.objects.create(
            doctor_id=doctor,total_earnings=total_earnings)
            print("earnings created",earnings)
            
    Payouts.objects.filter(doctor_id=doctor,payout_id=payout_id).update(payout_status=request.data['payout_status'],
    accepted_time=current_time,accepted_date=current_date)
    return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': 'Doctor Earnings Updated'},
                status=status.HTTP_201_CREATED
            )

"""Invoice Status Update"""
@api_view(['POST'])
def invoice_status_update_view(request):
    print("invoice_status-update")
    Invoices.objects.filter(
        invoice_id=request.data['invoice_id']).update(invoice_status=request.data['invoice_status'])

"""Inticure Earnings view"""
@api_view(['POST'])
def inticure_earnings_view(request):
    print("inticure_earnings")
    inticure_earnings=InticureEarningsSerializer(InticureEarnings.objects.filter(currency__icontains=request.data['currency']),many=True).data
    print(inticure_earnings)
    return Response({
        'response_code': 200,
                'status': 'Ok',
                'message': 'Inticure Earnings',
                "data":inticure_earnings
    })

"""Plans ViewSet"""
class PlansViewSet(viewsets.ModelViewSet):
    queryset = Plans.objects.all()   
    serializer_class = PlansSerializer

    def create(self, request, *args, **kwargs):            
        location_id = request.data.get('location_id')
        doctor_id = request.data.get('doctor_id')

        if Plans.objects.filter(location_id=location_id, doctor_id=doctor_id).exists():
            return Response({
                'response_code': 401,
                'status': 'Bad request',
                'message': 'A plan with this location ID and doctor ID already exists.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            se = serializer.save()
            return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': 'Plans created'
            }, status=status.HTTP_201_CREATED)

        return Response({
            'response_code': 400,
            'status': 'Bad request',
            'message': 'Plans could not be created with received data.',
            'exception': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request, *args, **kwargs):
        filter_item={}
        print('1207',request.data)
        if 'location_id' in request.data and request.data['location_id']:
            filter_item['location_id']=request.data['location_id']
        if 'session_type' in request.data and request.data['session_type']:
            filter_item['session_type']=request.data['session_type']
        print(filter_item)
        unique_plans = Plans.objects.values('doctor_id').annotate(first_plan_id=Min('id'))

        plan_ids = [plan['first_plan_id'] for plan in unique_plans]

        queryset = Plans.objects.filter(id__in=plan_ids)
        serializer = self.serializer_class(queryset, many=True).data
        for data in serializer:
            data['currency']=get_currency(data['location_id'])
            data['duration'] = get_duration(data['doctor_id'])
        return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Plans list',
                 'data':serializer},
                  status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            plans = Plans.objects.filter(
                pk=self.kwargs['pk']).update(**serializer.validated_data)
            return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Plans Updated'},
                status=status.HTTP_201_CREATED
            )

    def destroy(self, request, *args, **kwargs):
        # serializer = self.serializer_class(data=request.data)
        # if serializer.is_valid(raise_exception=True):
        plans = Plans.objects.filter(pk=self.kwargs['pk'])
        plans.delete()
        return Response(
            {'response_code': 200,
             'status': 'Ok',
             'message': 'Plans Deleted'},
            status=status.HTTP_201_CREATED
        )


"""Location ViewSet"""
class LocationViewSet(viewsets.ModelViewSet):
    queryset = Locations.objects.all()
    serializer_class = LocationSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # if serializer.is_valid():
            se = serializer.save()
            return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': 'Locations created'},
                status=status.HTTP_201_CREATED
            )

        return Response({
            'response_code': 400,
            'status': 'Bad request',
            'message': 'Locations could not be created with received data.',
            'exception':serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    def list(self, request, *args, **kwargs):
        queryset=Locations.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Locations list',
                 'data':serializer.data},
                  status=status.HTTP_201_CREATED)
    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            location = Locations.objects.filter(
                pk=self.kwargs['pk']).update(**serializer.validated_data)
            return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Location Updated'},
                status=status.HTTP_201_CREATED
            )

    def destroy(self, request, *args, **kwargs):
        # serializer = self.serializer_class(data=request.data)
        # if serializer.is_valid(raise_exception=True):
        location = Locations.objects.filter(pk=self.kwargs['pk'])
        location.delete()
        return Response(
            {'response_code': 200,
             'status': 'Ok',
             'message': 'Language Deleted'},
            status=status.HTTP_201_CREATED
        )

"""Language Viewset"""
class LanguageViewset(viewsets.ModelViewSet):
    queryset=LanguagesKnown.objects.all()
    serializer_class=LanguageSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # if serializer.is_valid():
            se = serializer.save()
            return Response({
                'response_code': 200,
                'status': 'Ok',
                'message': 'Language created'},
                status=status.HTTP_201_CREATED
            )

        return Response({
            'response_code': 400,
            'status': 'Bad request',
            'message': 'Language could not be created with received data.',
            'exception':serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    def list(self, request, *args, **kwargs):
        queryset=LanguagesKnown.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Language list',
                 'data':serializer.data},
                  status=status.HTTP_201_CREATED)
    def update(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            language = LanguagesKnown.objects.filter(
                pk=self.kwargs['pk']).update(**serializer.validated_data)
            return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Language Updated'},
                status=status.HTTP_201_CREATED
            )

    def destroy(self, request, *args, **kwargs):
        # serializer = self.serializer_class(data=request.data)
        # if serializer.is_valid(raise_exception=True):
        language = LanguagesKnown.objects.filter(pk=self.kwargs['pk'])
        language.delete()
        return Response(
            {'response_code': 200,
             'status': 'Ok',
             'message': 'Language Deleted'},
            status=status.HTTP_201_CREATED
        )



class AppointmentRatingsViewset(viewsets.ModelViewSet):
    queryset=AppointmentRatings.objects.all()
    serializer_class=AppointmentRatingsSerializer

class CouponCodeViewset(viewsets.ModelViewSet):
    queryset=DiscountCoupons.objects.all()
    serializer_class=CouponCodeSerializer


class RefundViewSet(viewsets.ModelViewSet):
    queryset = Refund.objects.all()   
    serializer_class = RefundSerializer
    pagination_class = LimitOffsetPagination
    pagination_class.offset = 10

    def list(self, request, *args, **kwargs):
        filter_item={}
        refund_list=[]
        if 'refund_id' in request.query_params and request.query_params['refund_id']:
            filter_item['refund_id']=request.query_params['refund_id']
        if 'date_from' in request.query_params and request.query_params['date_from']:
            filter_item['refund_requested_date__gte'] = request.query_params['date_from']
        if 'date_to' in request.query_params and request.query_params['date_to']:
            filter_item['refund_requested_date__lte'] = request.query_params['date_to']
        if 'status' in request.query_params and request.query_params['status']:
            filter_item['refund_status'] = request.query_params['status']
            
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(**filter_item)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            for data in serializer.data:
                try:
                    doctor_name=Invoices.objects.get(appointment_id=data['appointment_id']).doctor_name
                except Exception as e:
                    print(e)
                    doctor_name=""
                data['customer_name']=get_users_name(data['customer_id'])
                data['customer_email']=get_user_mail(data['customer_id'])
                data['doctor_name']=doctor_name
                data['currency']=get_currency(get_customer_location(data['customer_id']))
                if 'currency' in  request.query_params and request.query_params['currency']:
                    print(type(request.query_params['currency']),data['currency'],type(data['currency']))
                    if data['currency'] == request.query_params['currency']:
                        print("currency is ",data['currency'],request.query_params['currency'])
                        refund_list.append(data)
                else:
                    print("else part")
                    refund_list.append(data)
            # return self.get_paginated_response(serializer.data)
            if refund_list:
                return self.get_paginated_response(refund_list)
            else:
                return Response({'count':0,
                             'next':None,
                             'previous':None,
                             'results':[]})

            # print(refund_list)
            # return self.get_paginated_response(refund_list)
        
        serializer = self.serializer_class(queryset, many=True)
        for data in serializer.data:
            try:
                doctor_name=Invoices.objects.get(appointment_id=data['appointment_id']).doctor_name
            except Exception as e:
                print(e)
                doctor_name=""
            data['customer_name']=get_users_name(data['customer_id'])
            data['customer_email']=get_user_mail(data['customer_id'])
            data['doctor_name']=doctor_name
            data['currency']=get_currency(get_customer_location(data['customer_id']))
            if 'currency' in  request.query_params and request.query_params['currency']:
                if data['currency'] == request.query_params['currency']:
                    print("here")
                    refund_list.append(data)
            else:
                print("sec else part")
                refund_list.append(data)
        if refund_list:
            return self.get_paginated_response(refund_list)
        else:
            return Response({'count':0,
                             'next':None,
                             'previous':None,
                             'results':[]})
        
    def post(self, request, *args, **kwargs):
        data=request.data
        if 'refund_status' in request.data and request.data['refund_status'] == 1:
            data['refund_processed_date']=datetime.today().date()
            try:
                customer_id=Refund.objects.get(pk=self.kwargs['pk']).customer_id
            except Exception as e:
                print(e)
                customer_id=None
            subject = 'You Refund have been Processed'
            html_message = render_to_string('refund_completed.html', {"doctor_flag":0,
                'name':get_users_name(customer_id)})
            plain_message = strip_tags(html_message)
            from_email = 'wecare@inticure.com'
            cc = "nextbighealthcare@inticure.com"
            to =  get_user_mail(customer_id)
            print("here..........")
            mail.send_mail(subject, plain_message, from_email, [to],[cc], html_message=html_message)
        Refund.objects.filter(pk=self.kwargs['pk']).update(**data)
        return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Refund Updated'},
                status=status.HTTP_200_OK
            )

import json

@api_view(['POST'])
def duration(request):
    data = json.loads(request.body)
    doctor_id = data.get('doctor_id')
    if not doctor_id:
        return JsonResponse({'error': 'Doctor ID is required'}, status=400)
    try:
        duration = Duration.objects.get(doctor_id = doctor_id).duration
        return JsonResponse({'duration': duration}, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({'error': 'duration not found'}, status=404)

@api_view(['POST'])
def add_duration(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    doctor_id = data.get('doctor_id')
    new_duration = data.get('duration')

    if not doctor_id:
        return JsonResponse({'error': 'Doctor ID is required'}, status=400)
    
    if not new_duration:
        return JsonResponse({'error': 'Duration is required'}, status=400)
    
    try:
        rows_affected = Duration.objects.filter(doctor_id=doctor_id).update(duration=new_duration)

        if rows_affected == 0:
            duration_obj = Duration.objects.create(doctor_id=doctor_id, duration=new_duration)
            return JsonResponse({'message': 'Duration created successfully', 'duration': duration_obj.duration}, status=201)
        else:
            updated_duration = Duration.objects.get(doctor_id=doctor_id)
            return JsonResponse({'message': 'Duration updated successfully', 'duration': updated_duration.duration}, status=200)
    
    except Duration.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

"""View to list appointments"""
@api_view(['POST'])
def dashboard_view(request):
    filter = {}
    count=0
    appointment_list=[]
    if 'appointment_status' in request.data and request.data['appointment_status']:
            filter['appointment_status__in'] = request.data['appointment_status']
    queryset1 = custom_filter(AppointmentHeader, filter).order_by('-appointment_id')
    appointment_data = AppointmentHeaderSerializer(queryset1, many=True).data
    print(appointment_data)
    for user in appointment_data:
         user_id=user['user_id']
         appointment_id=user['appointment_id']
         cat_id=user['category_id']
         user['time_slot']=user['appointment_time_slot_id']
         user['escalate_time_slots']=user['escalated_time_slot']
         user['category']=get_category_name(cat_id)
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
         try:
           queryset_user=User.objects.get(id=user['junior_doctor'])
           print(queryset_user)
           user['junior_doc_id']=queryset_user.id
           user['junior_doc_name']=queryset_user.first_name+queryset_user.last_name
           user['specialization']=get_doctor_specialization(user['junior_doctor'])
         except Exception as e:
            print(e)
            user['junior_doc_name']=""
         try:
           queryset_user=User.objects.get(id=user['senior_doctor'])
           print(queryset_user)
           user['senior_doc_id']=queryset_user.id
           user['senior_doc_name']=queryset_user.first_name+queryset_user.last_name
           user['specialization']=get_doctor_specialization(user['senior_doctor'])
           try:
              
              doctor_id=DoctorMapping.objects.get(added_doctor=1,appointment_id=appointment_id).mapped_doctor
              user["added_doctor"]=get_users_name(doctor_id)
              user['added_doctor_id']=doctor_id
           except Exception as e:
              print("added_doc",e)
              user["added_doctor"]=None
              user['added_doctor_id']=None
         except Exception as e:
            print(e)
            user['senior_doc_name']=""
         try:
            queryset_invoice=Invoices.objects.get(appointment_id=appointment_id)
            user['invoice_status']=queryset_invoice.status
            user['invoice_id']=queryset_invoice.invoice_id
         except:
            user['invoice_status']=""
            user['invoice_id']=""
        
         if 'location' in request.data and request.data['location']:
             if request.data['location'] == get_customer_location(user_id):
                 appointment_list.append(user)
                 if user['appointment_status'] != 3:
                     count+=1
         else:
             appointment_list.append(user)
             count=AppointmentHeader.objects.exclude(appointment_status=3).count()
    doc_count=0
    custom_count=0
    if 'location' in request.data and request.data['location']:
        doctors_count=DoctorProfiles.objects.filter(is_accepted=1)
        for data in doctors_count:
            if str(data.location) == str(request.data['location']):
                doc_count+=1
    
        customers_count=CustomerProfile.objects.all()
        for customer in customers_count:
            if customer.location == request.data['location']:
                custom_count+=1
    else:
        doc_count=DoctorProfiles.objects.filter(is_accepted=1)
        custom_count=CustomerProfile.objects.all()
        
        #total_appointments=AppointmentHeader.objects.exclude(appointment_status=3).count()
        
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': appointment_data,
        "doctors_count":doc_count,
        "customers_count":custom_count,
        "total_appointments":count,
        "total_profit":"",
        "total_payout":""
        })
    