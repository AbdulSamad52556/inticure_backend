from dataclasses import fields
from pyexpat import model
from rest_framework import serializers

from .models import AppointmentRatings, CustomerProfile,Refund

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomerProfile
        fields="__all__"
        
class AppointmentRatingsSerializer(serializers.ModelSerializer):
    class Meta:
        model=AppointmentRatings
        fields="__all__"
        
class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model=Refund
        fields="__all__"