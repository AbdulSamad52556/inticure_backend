from email.mime import base
from rest_framework import routers
from .views import CategoryViewSet

router = routers.DefaultRouter()
router.register(r'category_viewset',CategoryViewSet,basename='category_viewset')
