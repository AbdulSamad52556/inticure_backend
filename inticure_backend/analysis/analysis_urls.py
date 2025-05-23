from django.contrib import admin
from django.urls import path, include
from .routers import router

from analysis.views import category_view, create_category_view, questionnaire_view, analysis_submit_view,\
followup_booking_view,payments_view,invoice_list_view,invoice_detail_view,answer_type_view,otp_verify_view,create_user_view, \
reschedule_check, did_appointment_complete_view

urlpatterns = [
    
    path('category', category_view, name='category'),
    path('create_category', create_category_view, name='create_category'),
    path('create_user',create_user_view,name='create_user'),
    path('questionnaire', questionnaire_view, name='quesionnaire'),
    path('analysis_submit', analysis_submit_view, name='analysis_submit'),
    path('followup_booking',followup_booking_view,name='followup_booking'),
    path('invoice_list',invoice_list_view,name='invoice_list'),
    path('invoice_detail',invoice_detail_view,name='invoice_detail'),
    path('payments',payments_view,name='payments'),
    path('answer_type',answer_type_view,name='answer_type'),
    path('otp_verify',otp_verify_view,name='otp_verify'),
    path('reschedule_check',reschedule_check,name='reschedule_check'),
    path('did_appointment_complete',did_appointment_complete_view, name='did_appointment_complete'),
    path('', include(router.urls)),
]