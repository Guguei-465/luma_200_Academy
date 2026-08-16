from django.urls import path
from .views import (
    AttendanceSubmissionCreateView,
    MarkAttendanceView,
    SubmitAttendanceView,
    AttendanceDetailView,
    StudentAttendanceHistoryView,
)

urlpatterns = [
    path("mark/", MarkAttendanceView.as_view(), name="mark-attendance"),
    path("submit/", SubmitAttendanceView.as_view(), name="submit-attendance"),
    path("create/", AttendanceSubmissionCreateView.as_view(), name="attendance-create"),
    path("<int:submission_id>/", AttendanceDetailView.as_view(), name="attendance-detail"),
    path("student/<int:student_id>/", StudentAttendanceHistoryView.as_view(), name="student-attendance-history"),
]