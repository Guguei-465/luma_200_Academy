from django.urls import path

from .views import (
    AttendanceSubmissionCreateView,
    MarkAttendanceView,
    SubmitAttendanceView,
    AttendanceDetailView,
    StudentAttendanceHistoryView,
    TeacherAttendanceHistoryView,
<<<<<<< HEAD
    AttendanceReportView,
=======
>>>>>>> origin/main
)


urlpatterns = [

    # ========================================================
    # LOAD + SAVE ATTENDANCE
    # ========================================================

    path(
        "mark/",
        MarkAttendanceView.as_view(),
        name="mark-attendance",
    ),

    # ========================================================
    # CREATE TODAY'S ATTENDANCE SESSION
    # ========================================================

    path(
        "create/",
        AttendanceSubmissionCreateView.as_view(),
        name="attendance-create",
    ),

    # ========================================================
    # LEGACY ENDPOINT
    #
    # Not required by the new workflow.
    # ========================================================

    path(
        "submit/",
        SubmitAttendanceView.as_view(),
        name="submit-attendance",
    ),

    # ========================================================
    # ADMIN / COORDINATOR DETAIL
    # ========================================================

    path(
        "<int:submission_id>/",
        AttendanceDetailView.as_view(),
        name="attendance-detail",
    ),

    # ========================================================
    # STUDENT HISTORY
    # ========================================================

    path(
        "student/<int:student_id>/",
        StudentAttendanceHistoryView.as_view(),
        name="student-attendance-history",
    ),

    # ========================================================
    # TEACHER HISTORY
    # ========================================================

    path(
        "teacher/history/",
        TeacherAttendanceHistoryView.as_view(),
        name="teacher-attendance-history",
    ),
<<<<<<< HEAD

    # ========================================================
    # ADMIN / COORDINATOR REPORT
    # ========================================================

    path(
        "report/",
        AttendanceReportView.as_view(),
        name="attendance-report",
    ),
=======
>>>>>>> origin/main
]