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

router.register(
    r"teacher-profile",
    TeacherProfileViewSet,
    basename="teacher-profile"
)


urlpatterns = [

    # =================================================
    # ASSIGNMENTS
    # =================================================

    path(
        "",
        TeacherAssignmentListView.as_view(),
        name="assignment-list",
    ),

    path(
        "create/",
        TeacherAssignmentCreateView.as_view(),
        name="assignment-create",
    ),

    path(
        "<int:pk>/",
        TeacherAssignmentDetailView.as_view(),
        name="assignment-detail",
    ),

    path(
        "update/<int:pk>/",
        TeacherAssignmentUpdateView.as_view(),
        name="assignment-update",
    ),

    path(
        "delete/<int:pk>/",
        TeacherAssignmentDeleteView.as_view(),
        name="assignment-delete",
    ),

    # =================================================
    # TEACHER PROFILE
    # =================================================

    path(
        "",
        include(router.urls),
    ),
]