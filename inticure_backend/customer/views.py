# Payment gateway imports
import stripe
import json
from django.http.response import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from datetime import date,datetime
from django.shortcuts import render, redirect
from inticure_backend import settings
# Create your views here.

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets,status

from django.contrib.auth.models import User

from analysis.models import AppointmentHeader,Invoices
from doctor.serializer import  AppointmentHeaderSerializer
from .serializer import CustomerProfileSerializer,AppointmentRatingsSerializer
from .models import CustomerProfile, AppointmentRatings,StripeCustomer,TemporaryTransactionData
from administrator.models import Plans,Transactions,CouponRedeemLog,Locations
from administrator.serializer import UserSerializer
import razorpay
# Create your views here.
from razorpay.errors import SignatureVerificationError

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))


# class CustomerProfileViewSet(viewsets.ModelViewSet):

#     serializer_class=CustomerProfileSerializer

#     def update(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid(raise_exception=True):
#             CustomerProfile.objects.filter(pk=self.kwargs['pk']).update(**serializer.validated_data)
#             User.objects.filter(pk=self.kwargs['pk']).update(**serializer.validated_data)
#             return Response(
#                 {'response_code': 200,
#                  'status': 'Ok',
#                  'message': 'SubCategory Updated'},
#                 status=status.HTTP_201_CREATED
#             )

"""Customer Profile CRUD operations"""

def payment_page(request,temp_id):
    appointment_flag = request.GET.get('appointment_flag')
    new_data = request.GET.get('new_data')
    print('appointment_flag',appointment_flag)
    print('new_data',new_data)
    return render(request, 'razorpayment/payment.html', {"api_key": settings.RAZORPAY_API_KEY})

@csrf_exempt
def create_order(request):
    if request.method == "POST":
        # Get payment details from the request
        amount = 500*100 # Amount in paise (e.g., 50000 paise = ₹500)
        currency = "INR"
        receipt = "receipt_001"

        # Create Razorpay order
        razorpay_order = razorpay_client.order.create(
            dict(amount=amount, currency=currency, receipt=receipt, payment_capture="1")
        )
        
        order_id = razorpay_order["id"]
        print('razorpay_order',razorpay_order)
        return JsonResponse({
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "razorpay_key": settings.RAZORPAY_API_KEY,
        })

    return JsonResponse({"error": "Invalid request method."}, status=400)

@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print("Received Data:", data)
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })
            return JsonResponse({"status": "success"})
        except SignatureVerificationError:
            return JsonResponse({"status": "failed", "message": "Signature verification failed"})
    return JsonResponse({"error": "Invalid request method."}, status=400)

@api_view(['POST'])
def customer_crud_view(request):
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
        
        if "mobile_num" in request.data and request.data['mobile_num'] != "":
          mobile_num=request.data['mobile_num']
          CustomerProfile.objects.filter(user_id=user_id).update(mobile_number=mobile_num)
        
        if "gender" in request.data and request.data['gender'] != "":
          gender=request.data['gender']
          CustomerProfile.objects.filter(user_id=user_id).update(gender=gender)
        
        if "profile_pic" in request.data and request.data['profile_pic'] != "":
                profile_pic=request.data['profile_pic']
                CustomerProfile.objects.filter(user_id=user_id).update(profile_pic=profile_pic)  
        if "dob" in request.data and request.data['dob'] != "":
          dob=request.data['dob']
          born=datetime.strptime(dob,"%Y-%m-%d")
          today = date.today()
          age=today.year - born.year - ((today.month, today.day) < (born.month, born.day))
          print(today,age,"AGE CALCULATED")
          CustomerProfile.objects.filter(user_id=user_id).update(date_of_birth=dob,age=age)
        return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'Customer Profile Updated'},
                status=status.HTTP_201_CREATED
            )
      else:    
          return Response(
                {'response_code': 400,
                 'status': 'Ok',
                 'message': 'Invalid UserID'})

  elif "delete" in request.data["operation_flag"]:
    user_id=request.data['user_id']
    User.objects.filter(id=user_id).delete()
    CustomerProfile.objects.filter(user_id=user_id).delete()
    return Response(
                {'response_code': 200,
                 'status': 'Ok',
                 'message': 'User Deleted'})
  
  elif "view" in request.data['operation_flag']:
    try:
        queryset=CustomerProfile.objects.all()
        customers=CustomerProfileSerializer(queryset,many=True).data
        print(customers)
        for user in customers:
           user_id=user['user_id']
           try:
              queryset_user=User.objects.get(id=user_id)
              user['user_fname']=queryset_user.first_name
              user['user_lname']=queryset_user.last_name
              user['user_mail']=queryset_user.email
              try:
                user['location']=Locations.objects.get(location_id=user['location']).location
              except:
                user['location']=""
           except Exception as e:
               print(e)
               user['user_fname']=""
               user['user_lname']=""
               user['user_mail']=""
        
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data': customers
    })
    except Exception as e:
        print('except',e)
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':"Customer List None"
    })
  else:
    return Response(
                {'response_code': 400,
                 'status': 'Ok',
                 'message': 'Invalid Request'})

def success_view(request,temp_id):
    data = {}
    print(temp_id)
    print(request)
    temp_qset=TemporaryTransactionData.objects.get(temp_id=temp_id)
    print(temp_qset)
    if temp_qset.appointment_id is None:
      print("none")
    else:
      
       try:
           invoice=Invoices.objects.get(appointment_id=temp_qset.appointment_id)
           invoice_id=invoice.invoice_id
       except:
           invoice_id=None
       total_amount=temp_qset.total_amount
       Invoices.objects.filter(appointment_id=temp_qset.appointment_id,status=2).update(
         status=1,vendor_fee=total_amount*20/100,tax=0,
         discounts=temp_qset.discount,total=total_amount,mode_of_pay="card")
       Transactions.objects.create(invoice_id=invoice_id,transaction_amount=total_amount,payment_status=1)
    if temp_qset.coupon_id != 0:
      CouponRedeemLog.objects.create(coupon_id=temp_qset.coupon_id,user_id=temp_qset.user_id)
    return redirect("https://customers.inticure.online/payment_success")


def failed_view(request,temp_id):
    data = {}
    print(temp_id)
    try:
      TemporaryTransactionData.objects.get(temp_id=temp_id).delete()
      # total_amount=temp_qset.total_amount
      # Invoices.objects.filter(appointment_id=temp_qset.appointment_id,status=2).update(
      # status=1,vendor_fee=total_amount*20/100,tax=0,
      # discounts=temp_qset.discount,total=total_amount,mode_of_pay="card")
      
    except:
      print('Transaction data unavailable')  
    data['key'] = settings.STRIPE_PUBLISHABLE_KEY
    return redirect("https://customers.inticure.online/payment_failure")

def success_view2(request,temp_id):
    data = {}
    print(temp_id)
    temp_qset=TemporaryTransactionData.objects.get(temp_id=temp_id)
    if temp_qset.appointment_id is None:
      print("none")
    else:
      
       try:
           invoice=Invoices.objects.get(appointment_id=temp_qset.appointment_id)
           invoice_id=invoice.invoice_id
       except:
           invoice_id=None
       total_amount=temp_qset.total_amount
       Invoices.objects.filter(appointment_id=temp_qset.appointment_id,status=2).update(
         status=1,vendor_fee=total_amount*20/100,tax=0,
         discounts=temp_qset.discount,total=total_amount,mode_of_pay="card")
       Transactions.objects.create(invoice_id=invoice_id,transaction_amount=total_amount,payment_status=1)
    
    if temp_qset.coupon_id != 0:
      CouponRedeemLog.objects.create(coupon_id=temp_qset.coupon_id,user_id=temp_qset.user_id)
    return redirect("https://analysis.inticure.online/thank_you_page")

def failed_view2(request,temp_id):
    data = {}
    print(temp_id)
    try:
      TemporaryTransactionData.objects.get(temp_id=temp_id).delete()
      # total_amount=temp_qset.total_amount
      # Invoices.objects.filter(appointment_id=temp_qset.appointment_id,status=2).update(@@@@@@@@@follow up booking@@@@@@@@@@@@@@@@@@
      # status=1,vendor_fee=total_amount*20/100,tax=0,
      # discounts=temp_qset.discount,total=total_amount,mode_of_pay="card")
      
    except:
      print('Transaction data unavailable')  
    data['key'] = settings.STRIPE_PUBLISHABLE_KEY
    return redirect("https://customers.inticure.online/payment_failure")

@csrf_exempt
def create_checkout_session(request):
    request_data = json.loads(request.body)
    print('7654321',request_data)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    print(request_data['temp_id'])
    if request_data['currency'] == 'Dollar':
      request_data['currency'] = 'usd'
    print(request_data['appointment_flag'])
    if request_data['appointment_flag'] == 'first_appointment':
      success_url = request.build_absolute_uri(reverse('success2',kwargs={'temp_id':request_data['temp_id']}))
      cancel_url = request.build_absolute_uri(reverse('failed2',kwargs={'temp_id':request_data['temp_id']}))
    else:
      success_url = request.build_absolute_uri(reverse('success',kwargs={'temp_id':request_data['temp_id']}))
      cancel_url = request.build_absolute_uri(reverse('failed',kwargs={'temp_id':request_data['temp_id']}))
    name = "Appointment"
    shipping_info = None
    if request_data['currency'] == 'INR':
        shipping_address_collection = {
            'allowed_countries': ['IN']
        }
    checkout_session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[
            {
                'price_data': {
                    'currency': request_data['currency'],
                    'product_data': {
                        'name': name,
                    },
                    'unit_amount': request_data['amount']*100,
                },
                'quantity': 1,
            }
        ],
    customer=request_data['stripe_customer_token_id'],
    mode='payment',
    success_url=success_url,
    cancel_url=cancel_url,
    shipping_address_collection=shipping_info,  # Include shipping info only for Indian customers
    billing_address_collection='required' if request_data['currency'] == 'INR' else 'auto',  # Required for India

    )
    print("checkout_session",checkout_session.id)
    return JsonResponse({'sessionId': checkout_session.id})

def checkout_preprocess(user_id,amount,temp_id,currency,appointment_flag):
    customer_email = User.objects.get(id=user_id).email
    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_customer = StripeCustomer.objects.filter(customer_id=user_id)
    if stripe_customer.count() > 0:
        stripe_customer_token_id = stripe_customer.first().stripe_customer_token_id
    else:
        customer = stripe.Customer.create(
            description="Stripe Customer",
            email=customer_email, )
        print(customer)
        stripe_customer_token_id = customer['id']
        StripeCustomer.objects.create(customer_id=user_id,
                                      stripe_customer_token_id=stripe_customer_token_id)
    data = {}
    data['key'] = settings.STRIPE_PUBLISHABLE_KEY
    data['stripe_customer_token_id'] = stripe_customer_token_id
    data['amount'] = amount
    data['temp_id'] = temp_id
    data['currency'] = currency
    data['user_id'] = user_id
    data['appointment_flag'] = appointment_flag
    return data

"""Checkout view for customer app appointment checkout"""
def checkout_view(request, temp_id):
    appointment_flag = request.GET.get('appointment_flag')
    new_data = request.GET.get('new_data')
    print(appointment_flag)
    print('new_data',new_data)
    
    try:
        transaction_qset=TemporaryTransactionData.objects.get(temp_id=temp_id)
        print(transaction_qset.user_id,transaction_qset.total_amount,transaction_qset.currency,appointment_flag)
        data = checkout_preprocess(transaction_qset.user_id,
        transaction_qset.total_amount,temp_id,transaction_qset.currency,appointment_flag)
        print(data)
        return render(request, "payment/checkout.html", data)
    except Exception as e:
        print(e)
        return redirect('failed',temp_id=temp_id)

@api_view(['POST'])
def customer_payments_view(request):                 
    # location=request.data['location_id']
    appointment_id=request.data['appointment_id']
    print("payments")
    try:
        plan=Plans.objects.get(id=2)
        pricing=plan.price
    except:
        pricing=0
        return Response({
        'response_code': 400,
        'status': 'Ok',
        'message':'Invalid Location' })
    return Response({
        'response_code': 200,
        'status': 'Ok',
        'message':'Payment Complete' })

@api_view(['POST'])
def customer_profile_view(request):
    print(request.data)
    print('asdfasdf')
    user_id=request.data['user_id']
    try:
        customer=CustomerProfile.objects.get(user_id=user_id)
        user=User.objects.get(id=user_id)
        user_profile=UserSerializer(user).data
        customer_profile=CustomerProfileSerializer(customer).data
        return Response({
        'response_code': 200,
        'status': 'Ok',
        'data1': user_profile,
        'data2':customer_profile
    })

    except Exception as e:
          print("doc_profile_except",e)
          return Response({
        'response_code': 400,
        'status': 'Failed',
        'message':'Customer doesnot Exist',
        'data': None
    })

@api_view(['POST'])
def appointment_ratings_view(request):
  ratings_serializer=AppointmentRatingsSerializer(data=request.data)
  if ratings_serializer.is_valid():
    ratings_serializer.save()
    return Response({
            'response_code': 200,
            'status': 'Ok',
            'message': 'Created Successfully'
        })
  return Response({
        'response_code': 400,
        'status': 'Ok',
        'message': 'Failed to add Ratings '
    })
# @api_view(['POST'])
# def appon_ratings_view(request):
#   ratings_serializer=AppointmentRatingsSerializer(data=request.data)
#   if ratings_serializer.is_valid():
#     ratings_serializer.save()
#     return Response({
#             'response_code': 200,
#             'status': 'Ok',
#             'message': 'Created Successfully'
#         })
#   return Response({
#         'response_code': 400,
#         'status': 'Ok',
#         'message': 'Failed to add Ratings '
    # })
@api_view(['POST'])
def appointment_ratings_list_view(request):
  avg_doctor_ratings=0
  avg_user_ratings=0
  if 'doctor_id' in request.data and request.data['doctor_id'] !="":
      doctor_id=request.data['doctor_id']
      doc_ratings=AppointmentRatings.objects.filter(
        doctor_id=doctor_id,added_by='customer').values_list('rating',flat=True)
      avg_doctor_ratings=format(float(sum(doc_ratings)/len(doc_ratings)),'.2f')
  
  if 'user_id' in request.data and request.data['user_id'] !="":
      user_id=request.data['user_id']
      ratings=AppointmentRatings.objects.filter(
        user_id=user_id,added_by='doctor').values_list('rating',flat=True)
      avg_user_ratings=format(float(sum(ratings)/len(ratings)),'.2f')
  
  inticure_ratings=AppointmentRatings.objects.all().values_list('app_rating',flat=True)
  avg_inticure_ratings=format(float(sum(inticure_ratings)/len(inticure_ratings)),'.2f')
  return Response({
            'response_code': 200,
            'status': 'Ok',
            'message': 'Ratings-List',
            'customer_ratings':avg_user_ratings,
            'doctor_ratings':avg_doctor_ratings,
            'inticure_ratings':avg_inticure_ratings
        })