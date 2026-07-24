from django.urls import path

from .views import (
    AttendanceSubmissionCreateView,
    MarkAttendanceView,
    SubmitAttendanceView,
    PendingAttendanceListView,
    ApproveAttendanceView,
    ReturnAttendanceView,
    AttendanceDetailView,
    StudentAttendanceHistoryView,
)

urlpatterns = [

    # =====================================
    # Teacher
    # =====================================

    # Mark attendance
    path(
        "mark/",
        MarkAttendanceView.as_view(),
        name="mark-attendance",
    ),

    # Submit attendance for approval
    path(
        "submit/",
        SubmitAttendanceView.as_view(),
        name="submit-attendance",
    ),

    # =====================================
    # Academic Coordinator / Super Admin
    # =====================================

    # View pending attendance
    path(
        "pending/",
        PendingAttendanceListView.as_view(),
        name="pending-attendance",
    ),

    # Approve attendance
    path(
        "approve/",
        ApproveAttendanceView.as_view(),
        name="approve-attendance",
    ),

    # Return attendance for correction
    path(
        "return/",
        ReturnAttendanceView.as_view(),
        name="return-attendance",
    ),

    # =====================================
    # Reports / History
    # =====================================

    # Attendance details for one submission
    path(
        "<int:submission_id>/",
        AttendanceDetailView.as_view(),
        name="attendance-detail",
    ),

    # Student attendance history
    path(
        "student/<int:student_id>/",
        StudentAttendanceHistoryView.as_view(),
        name="student-attendance-history",
    ),

    path(
    "create/",
    AttendanceSubmissionCreateView.as_view(),
    name="attendance-create",
),
]



