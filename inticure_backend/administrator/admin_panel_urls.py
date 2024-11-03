from django.urls import path, include

from .views import remove_option_view, sign_in_view, logout_view, create_questions_view, \
    update_questions_view, remove_question_view, update_option_view,doctor_list_view,doctor_create_view,\
    payout_list_view,payout_detail_view,transaction_list_view,transaction_detail_view,doctor_profile_edit_view,\
    report_customer_view,forgot_password_view,password_change_view,application_action_view,sign_in_otp_view,\
    earnings_view,admin_dashboard_view,settings_view,inticure_earnings_view,invoice_status_update_view,\
    dashboard_view,create_user, get_price, get_plan, edit_plan, remove_plan, get_location, duration, add_duration,\
    contact_form_submission

from .routers import router


urlpatterns = [

    path('sign_in', sign_in_view, name='sign_in'),
    path('signup_view',create_user,name='create_user'),
    path('logout', logout_view, name='logout'),
    path('create_questions', create_questions_view, name='create_questions'),
    path('update_questions', update_questions_view, name='update_questions'),
    path('remove_question', remove_question_view, name='remove_question'),
    path('update_option', update_option_view, name='update_option'),
    path('remove_option', remove_option_view, name='remove_option'),
    path('doc_list',doctor_list_view,name='doc_list'),
    path('doc_create',doctor_create_view,name='doc_create'),
    path('payout_list',payout_list_view,name='payout_list'),
    path('payout_detail',payout_detail_view,name='payout_detail'),
    path('transaction_list',transaction_list_view,name='transaction_list'),
    path('transaction_detail',transaction_detail_view,name='transaction_detail'),
    path('doctor_profile_edit',doctor_profile_edit_view,name='doctor_profile_edit'),
    path('report_customer',report_customer_view,name='report_customer'),
    path('forgot_password',forgot_password_view,name='forgot_password'),
    path('password_change',password_change_view,name='password_change'),
    path('application_action',application_action_view,name='application_action'),
    path('sign_in_otp',sign_in_otp_view,name='sign_in_otp'),
    path('doctor_earnings',earnings_view,name='doctor_earnings'),
    path('admin_dash',admin_dashboard_view,name='admin_dash'),
    path('settings_view',settings_view,name='settings_view'),
    path('inticure_earnings',inticure_earnings_view,name='inticure_earnings'),
    path('invoice_status',invoice_status_update_view,name='invoice_status'),
    path('dashboard',dashboard_view,name='dashboard'),
    path('get-price', get_price, name='get_price'),
    path('get-plan', get_plan, name='get_plan'),
    path('edit-plan',edit_plan,name='edit_plan'),
    path('remove-plan',remove_plan,name='remove_plan'),
    path('get-location',get_location, name='get_location'),
    path('api/doctor-duration/', duration, name='doctor_duration'),
    path('api/add-duration/', add_duration, name='add_duration'),
    path('api/contact/', contact_form_submission, name='contact_form_submission'),

    path('', include(router.urls)),
]