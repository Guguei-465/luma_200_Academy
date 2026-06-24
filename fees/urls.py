from rest_framework.routers import DefaultRouter
from .views import FeeViewSet

router = DefaultRouter()
router.register(r'fees', FeeViewSet)

urlpatterns = router.urls 