from django.contrib import admin
from .models import LanguagesKnown, Plans,Locations,Payouts, ReportCustomer,SpecializationTimeDuration,\
    TotalEarnings,CouponRedeemLog,DiscountCoupons,InticureEarnings,TotalPayouts
# Register your models here.
admin.site.register(Plans)
admin.site.register(Locations)
admin.site.register(Payouts)
admin.site.register(TotalEarnings)
admin.site.register(TotalPayouts)
admin.site.register(ReportCustomer)
admin.site.register(LanguagesKnown)
admin.site.register(CouponRedeemLog)
admin.site.register(DiscountCoupons)
admin.site.register(SpecializationTimeDuration)
admin.site.register(InticureEarnings)