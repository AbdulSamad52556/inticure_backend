from email.mime import base
from rest_framework import routers
from .views import PlansViewSet,LocationViewSet,LanguageViewset,AppointmentRatingsViewset,CouponCodeViewset,RefundViewSet

router = routers.DefaultRouter()
router.register(r'plans_viewset',PlansViewSet,basename='plans_viewset')
router.register(r'locations_viewset',LocationViewSet,basename='location_viewset')
router.register(r'languages_viewset',LanguageViewset,basename='languages_viewset')
router.register(r'ratings_viewset',AppointmentRatingsViewset,basename='ratings_viewset')
router.register(r'coupons_viewset',CouponCodeViewset,basename='coupons_viewset')
router.register(r'refund',RefundViewSet,basename='refund')

urlpatterns = router.urls