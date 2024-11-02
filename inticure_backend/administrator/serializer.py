from rest_framework import serializers
from django.contrib.auth.models import User
from .models import LanguagesKnown, Locations, Plans,Payouts,Transactions,DiscountCoupons,InticureEarnings

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields=['username','first_name','last_name','email']
class PlansSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plans
        fields="__all__"
class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model= Locations
        fields="__all__"
class PayoutsSerializer(serializers.ModelSerializer):
    class Meta:
        model= Payouts
        fields="__all__"
class TransactionsSerializer (serializers.ModelSerializer):
    class Meta:
        model=Transactions
        fields="__all__"
class LanguageSerializer (serializers.ModelSerializer):
    class Meta:
        model=LanguagesKnown
        fields="__all__"
class CouponCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model=DiscountCoupons
        fields="__all__"
class InticureEarningsSerializer(serializers.ModelSerializer):
    class Meta:
        model=InticureEarnings
        fields="__all__"