from django.urls import path, include
# from .routers import router
from .views import customer_crud_view,customer_payments_view,customer_profile_view,appointment_ratings_list_view,\
  appointment_ratings_view,success_view,failed_view,create_checkout_session,checkout_view, success_view2, failed_view2,\
  payment_page,create_order, verify_payment



urlpatterns = [
  path('customer_crud',customer_crud_view,name="customer_crud"),
  path('customer_payments',customer_payments_view,name='customer_payments'),
  path('customer_profile',customer_profile_view,name='customer_profile'),
  path('appointment_ratings',appointment_ratings_view,name='appointment_ratings'),
  path('appointment_ratings_list',appointment_ratings_list_view,name='appointment_ratings_list'),
  path('checkout/<int:temp_id>/', checkout_view, name="checkout"),
  path('success/<int:temp_id>/', success_view, name="success"),
  path('failed/<int:temp_id>/', failed_view, name="failed"),
  path('success2/<int:temp_id>/', success_view2, name="success2"),
  path('failed2/<int:temp_id>/', failed_view2, name="failed2"),
  path('api_checkout_session', create_checkout_session, name="api_checkout_session"),
  path('payment-page/<int:temp_id>/', payment_page, name='payment_page'),
  path('create-order/', create_order, name='create_order'),
  path('verify-payment/', verify_payment, name='verify_payment'),
]