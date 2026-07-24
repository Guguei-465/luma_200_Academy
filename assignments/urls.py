from django.urls import path
from .views import (
    TeacherAssignmentListView,
    TeacherAssignmentDetailView,
    TeacherAssignmentCreateView,
    TeacherAssignmentUpdateView,
    TeacherAssignmentDeleteView,
)

urlpatterns = [
    path("", TeacherAssignmentListView.as_view(), name="assignment-list"),
    path("<int:pk>/", TeacherAssignmentDetailView.as_view(), name="assignment-detail"),
    path("create/", TeacherAssignmentCreateView.as_view(), name="assignment-create"),
    path("update/<int:pk>/", TeacherAssignmentUpdateView.as_view(), name="assignment-update"),
    path("delete/<int:pk>/", TeacherAssignmentDeleteView.as_view(), name="assignment-delete"),
]
