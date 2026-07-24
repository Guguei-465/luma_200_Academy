from django.urls import path
from .views import ClassCapacityReport, DashboardStatisticsReport, FeeCollectionByTermReport, FeeSummaryReport, MonthlyFeeCollectionReport, NewAdmissionsReport, OutstandingBalancesReport, ParentChildrenReport, ParentContactReport, ParentFeeReport, ParentSummaryReport, ParentsWithOutstandingBalancesReport, SchoolSummaryReport, StudentStatusReport, StudentSummaryReport, StudentsByClassReport, StudentsByGenderReport, TeacherSummaryReport, TeacherWorkloadReport, TeachersByClassReport, TeachersBySubjectReport

urlpatterns = [
    # student 
    path("students/summary/",StudentSummaryReport.as_view(), name="student-summary-report",),
    path("students/by-class/", StudentsByClassReport.as_view(), name="students-by-class-report",),      
    path("students/by-gender/", StudentsByGenderReport.as_view(), name="students-by-gender-report",),
    path("students/new-admissions/", NewAdmissionsReport.as_view(), name="new-admissions-report",),
    # teachers
    path("teachers/summary/", TeacherSummaryReport.as_view(), name="teacher-summary-report",),
    path("teachers/by-class/", TeachersByClassReport.as_view(), name="teachers-by-class-report",),
    path("teachers/by-subject/", TeachersBySubjectReport.as_view(), name="teachers-by-subject-report",),   
    path( "teachers/workload/", TeacherWorkloadReport.as_view(), name="teacher-workload-report",),
    # fees 
    path( "fees/summary/", FeeSummaryReport.as_view(),name="fee-summary-report",),
    path("fees/outstanding/", OutstandingBalancesReport.as_view(), name="outstanding-balances-report",),
    path("fees/by-term/", FeeCollectionByTermReport.as_view(), name="fee-collection-by-term-report",),
    path( "fees/monthly-collection/",  MonthlyFeeCollectionReport.as_view(), name="monthly-fee-collection-report",),
    # general reports urls
    path("school/summary/", SchoolSummaryReport.as_view(), name="school-summary-report",),
    path("dashboard/", DashboardStatisticsReport.as_view(), name="dashboard-statistics-report",),
    # parents reports urls
    path("parents/summary/", ParentSummaryReport.as_view(), name="parent-summary-report",),
    path("parents/contacts/", ParentContactReport.as_view(), name="parent-contact-report",),
    path("parents/children/", ParentChildrenReport.as_view(), name="parent-children-report",),
    path("parents/fees/",ParentFeeReport.as_view(),name="parent-fee-report",),
    path("parents/outstanding-balances/", ParentsWithOutstandingBalancesReport.as_view(), name="parents-outstanding-balances-report",),
    # student?class
    path("school/class-capacity/", ClassCapacityReport.as_view(), name="class-capacity-report",),
    path("students/status/", StudentStatusReport.as_view(), name="student-status-report",),  
] 