from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ParentStudentViewSet

router = DefaultRouter()
router.register(
    r"",
    ParentStudentViewSet,
    basename="parent",
)

urlpatterns = [
    path("", include(router.urls)),
]