from django.urls import path
from .views import (
    TeacherAssignmentListView,
    TeacherAssignmentDetailView,
    TeacherAssignmentCreateView,
    TeacherAssignmentUpdateView,
    TeacherAssignmentDeleteView,
)
from rest_framework.routers import DefaultRouter
from .views import TeacherProfileViewSet

router = DefaultRouter()
router.register("profiles", TeacherProfileViewSet, basename="teacher-profile")

urlpatterns = router.urls

urlpatterns = [
    path("", TeacherAssignmentListView.as_view(), name="assignment-list"),
    path("<int:pk>/", TeacherAssignmentDetailView.as_view(), name="assignment-detail"),
    path("create/", TeacherAssignmentCreateView.as_view(), name="assignment-create"),
    path("update/<int:pk>/", TeacherAssignmentUpdateView.as_view(), name="assignment-update"),
    path("delete/<int:pk>/", TeacherAssignmentDeleteView.as_view(), name="assignment-delete"),
]
