from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TeacherAssignmentListView,
    TeacherAssignmentDetailView,
    TeacherAssignmentCreateView,
    TeacherAssignmentUpdateView,
    TeacherAssignmentDeleteView,
    TeacherProfileViewSet,
)

router = DefaultRouter()
router.register(r"teacher-profile", TeacherProfileViewSet, basename="teacher-profile")

urlpatterns = [
    path("", TeacherAssignmentListView.as_view(), name="assignment-list"),
    path("<int:pk>/", TeacherAssignmentDetailView.as_view(), name="assignment-detail"),
    path("create/", TeacherAssignmentCreateView.as_view(), name="assignment-create"),
    path("update/<int:pk>/", TeacherAssignmentUpdateView.as_view(), name="assignment-update"),
    path("delete/<int:pk>/", TeacherAssignmentDeleteView.as_view(), name="assignment-delete"),

    # Include the router URLs
    path("", include(router.urls)),
]