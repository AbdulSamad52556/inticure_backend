from email.mime import base
from unicodedata import name
from rest_framework import routers
from .views import ObservationsViewSet,PrescriptionsTextViewSet,CommonFileUploaderViewset,SpecializationViewset

router = routers.DefaultRouter()
router.register(r'observations_viewset',ObservationsViewSet,basename='observations_viewset')
router.register(r'prescriptions_text_viewset',PrescriptionsTextViewSet,basename='prescriptions_texts_viewset')
router.register(r'common_file',CommonFileUploaderViewset,basename='common_file')
router.register(r'specialization_list',SpecializationViewset,basename='specialization_list')
urlpatterns = router.urls