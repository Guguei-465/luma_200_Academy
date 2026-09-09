from datetime import timedelta, datetime

from django.db.models import Count, Sum
from django.db.models.functions import ExtractYear, ExtractMonth
from django.http import HttpResponse
from django.utils import timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from fees.models import StudentFee, FeePayment
from accounts.models import ParentProfile, TeacherProfile
from assignments.models import TeacherAssignment
from classes.models import ClassRoom
from students.models import Student
from subjects.models import Subject

from reports.serializers import (
    ClassCapacityReportSerializer,
    DashboardStatisticsSerializer,
    FeeCollectionByTermSerializer,
    FeeSummarySerializer,
    MonthlyFeeCollectionSerializer,
    NewAdmissionSerializer,
    OutstandingBalanceSerializer,
    ParentChildrenSerializer,
    ParentContactSerializer,
    ParentFeeReportSerializer,
    ParentSummarySerializer,
    SchoolSummarySerializer,
    StudentGenderReportSerializer,
    StudentStatusReportSerializer,
    StudentSummarySerializer,
    StudentsByClassSerializer,
    TeacherSummarySerializer,
    TeacherWorkloadSerializer,
    TeachersByClassSerializer,
    TeachersBySubjectSerializer,
)

from reports.permissions import (
    IsAcademicCoordinator,
    IsAccountant,
)


# =========================================================
# CONSTANTS
# =========================================================

DATE_FORMAT = "%Y-%m-%d"
CURRENCY = "KSh"

REPORT_TITLES = {
    "income": "Income Financial Report",
    "expenses": "Expenses Financial Report",
    "collection": "Fee Collection Report",
    "profit-loss": "Profit & Loss Report",
}


# =========================================================
# HELPERS
# =========================================================

def parse_date_param(date_str):
    """
    Parse a date string using YYYY-MM-DD format.
    Returns None if invalid.
    """
    try:
        return datetime.strptime(
            date_str,
            DATE_FORMAT,
        ).date()
    except (ValueError, TypeError):
        return None


def get_fee_summary(student_fee_qs=None):
    """
    Shared fee summary aggregator.
    """

    qs = (
        student_fee_qs
        if student_fee_qs is not None
        else StudentFee.objects.all()
    )

    agg = qs.aggregate(
        total_fee=Sum("total_fee"),
        amount_paid=Sum("amount_paid"),
        balance=Sum("balance"),
    )

    return {
        key: value or 0
        for key, value in agg.items()
    }


def get_payment_qs(date_from, date_to, term=None):
    """
    Shared payment queryset for reports and exports.
    """

    qs = (
        FeePayment.objects
        .filter(
            payment_date__date__gte=date_from,
            payment_date__date__lte=date_to,
        )
        .select_related(
            "student",
            "student__classroom",
        )
    )

    if term:
        qs = qs.filter(
            student__studentfee__fee_structure__term=term
        ).distinct()

    return qs


# =========================================================
# STUDENT REPORTS
# =========================================================

class StudentSummaryReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        total = Student.objects.count()

        male = Student.objects.filter(
            gender__iexact="Male"
        ).count()

        female = Student.objects.filter(
            gender__iexact="Female"
        ).count()

        return Response(
            StudentSummarySerializer(
                {
                    "total_students": total,
                    "male_students": male,
                    "female_students": female,
                }
            ).data
        )


class StudentsByClassReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        report = (
            Student.objects
            .values(
                "classroom__grade",
                "classroom__stream",
            )
            .annotate(
                total_students=Count("id")
            )
            .order_by(
                "classroom__grade",
                "classroom__stream",
            )
        )

        data = [
            {
                "classroom": (
                    f"{item['classroom__grade']} "
                    f"{item['classroom__stream']}"
                ),
                "total_students": item["total_students"],
            }
            for item in report
        ]

        return Response(
            StudentsByClassSerializer(
                data,
                many=True,
            ).data
        )


class StudentsByGenderReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        report = (
            Student.objects
            .values("gender")
            .annotate(
                total_students=Count("id")
            )
            .order_by("gender")
        )

        return Response(
            StudentGenderReportSerializer(
                report,
                many=True,
            ).data
        )


class NewAdmissionsReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        try:
            days = int(
                request.query_params.get(
                    "days",
                    30,
                )
            )
        except (ValueError, TypeError):
            days = 30

        start_date = (
            timezone.now().date()
            - timedelta(days=days)
        )

        students = (
            Student.objects
            .filter(
                date_admitted__gte=start_date
            )
            .select_related("classroom")
            .order_by("-date_admitted")
        )

        data = [
            {
                "admission_number": s.admission_number,
                "student_name": (
                    f"{s.first_name} {s.last_name}"
                ),
                "classroom": str(s.classroom),
                "date_admitted": s.date_admitted,
            }
            for s in students
        ]

        return Response(
            NewAdmissionSerializer(
                data,
                many=True,
            ).data
        )


class StudentStatusReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        report = (
            Student.objects
            .values("status")
            .annotate(
                total_students=Count("id")
            )
            .order_by("status")
        )

        return Response(
            StudentStatusReportSerializer(
                report,
                many=True,
            ).data
        )


# =========================================================
# TEACHER REPORTS
# =========================================================

class TeacherSummaryReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        total = TeacherProfile.objects.count()

        male = TeacherProfile.objects.filter(
            gender__iexact="Male"
        ).count()

        female = TeacherProfile.objects.filter(
            gender__iexact="Female"
        ).count()

        return Response(
            TeacherSummarySerializer(
                {
                    "total_teachers": total,
                    "male_teachers": male,
                    "female_teachers": female,
                }
            ).data
        )


class TeachersByClassReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        classrooms = (
            ClassRoom.objects
            .select_related(
                "class_teacher__user"
            )
            .order_by(
                "grade",
                "stream",
            )
        )

        data = []

        for classroom in classrooms:

            teacher_name = None

            if classroom.class_teacher:

                teacher_name = (
                    classroom.class_teacher.user
                    .get_full_name()
                    .strip()
                    or classroom.class_teacher.user.username
                )

            data.append(
                {
                    "classroom": str(classroom),
                    "class_teacher": teacher_name,
                }
            )

        return Response(
            TeachersByClassSerializer(
                data,
                many=True,
            ).data
        )


class TeachersBySubjectReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        assignments = (
            TeacherAssignment.objects
            .select_related(
                "teacher__user",
                "subject",
                "classroom",
            )
            .order_by(
                "classroom__grade",
                "classroom__stream",
                "subject__name",
            )
        )

        data = []

        for assignment in assignments:

            teacher_name = (
                assignment.teacher.user
                .get_full_name()
                .strip()
                or assignment.teacher.user.username
            )

            data.append(
                {
                    "teacher": teacher_name,
                    "subject": assignment.subject.name,
                    "classroom": str(
                        assignment.classroom
                    ),
                    "term": assignment.term,
                }
            )

        return Response(
            TeachersBySubjectSerializer(
                data,
                many=True,
            ).data
        )


class TeacherWorkloadReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        workload = (
            TeacherAssignment.objects
            .values(
                "teacher__user__first_name",
                "teacher__user__last_name",
                "teacher__user__username",
            )
            .annotate(
                total_assignments=Count("id"),
                total_classes=Count(
                    "classroom",
                    distinct=True,
                ),
                total_subjects=Count(
                    "subject",
                    distinct=True,
                ),
            )
            .order_by(
                "teacher__user__first_name",
                "teacher__user__last_name",
            )
        )

        data = []

        for item in workload:

            name = (
                f"{item['teacher__user__first_name']} "
                f"{item['teacher__user__last_name']}"
            ).strip()

            name = (
                name
                or item["teacher__user__username"]
            )

            data.append(
                {
                    "teacher": name,
                    "total_assignments": (
                        item["total_assignments"]
                    ),
                    "total_classes": (
                        item["total_classes"]
                    ),
                    "total_subjects": (
                        item["total_subjects"]
                    ),
                }
            )

        return Response(
            TeacherWorkloadSerializer(
                data,
                many=True,
            ).data
        )


# =========================================================
# FEE REPORTS
# =========================================================

class FeeSummaryReport(APIView):

    permission_classes = [
        IsAccountant,
    ]

    def get(self, request):

        return Response(
            FeeSummarySerializer(
                get_fee_summary()
            ).data
        )


class OutstandingBalancesReport(APIView):

    permission_classes = [
        IsAccountant,
    ]

    def get(self, request):

        accounts = (
            StudentFee.objects
            .filter(balance__gt=0)
            .select_related(
                "student",
                "student__classroom",
                "fee_structure",
            )
            .order_by("-balance")
        )

        data = [
            {
                "admission_number": (
                    account.student.admission_number
                ),
                "student_name": (
                    f"{account.student.first_name} "
                    f"{account.student.last_name}"
                ),
                "classroom": str(
                    account.student.classroom
                ),
                "academic_year": (
                    account.fee_structure.academic_year
                ),
                "term": account.fee_structure.term,
                "total_fee": account.total_fee,
                "amount_paid": account.amount_paid,
                "balance": account.balance,
            }
            for account in accounts
        ]

        return Response(
            OutstandingBalanceSerializer(
                data,
                many=True,
            ).data
        )


class FeeCollectionByTermReport(APIView):

    permission_classes = [
        IsAccountant,
    ]

    def get(self, request):

        report = (
            StudentFee.objects
            .values(
                "fee_structure__academic_year",
                "fee_structure__term",
            )
            .annotate(
                total_fee=Sum("total_fee"),
                amount_paid=Sum("amount_paid"),
                balance=Sum("balance"),
            )
            .order_by(
                "-fee_structure__academic_year",
                "fee_structure__term",
            )
        )

        data = [
            {
                "academic_year": (
                    item["fee_structure__academic_year"]
                ),
                "term": item["fee_structure__term"],
                "total_fee": item["total_fee"] or 0,
                "amount_paid": item["amount_paid"] or 0,
                "balance": item["balance"] or 0,
            }
            for item in report
        ]

        return Response(
            FeeCollectionByTermSerializer(
                data,
                many=True,
            ).data
        )


class MonthlyFeeCollectionReport(APIView):

    permission_classes = [
        IsAccountant,
    ]

    def get(self, request):

        report = (
            FeePayment.objects
            .annotate(
                year=ExtractYear("payment_date"),
                month=ExtractMonth("payment_date"),
            )
            .values(
                "year",
                "month",
            )
            .annotate(
                total_payments=Count("id"),
                total_amount=Sum("amount"),
            )
            .order_by(
                "-year",
                "-month",
            )
        )

        return Response(
            MonthlyFeeCollectionSerializer(
                report,
                many=True,
            ).data
        )


# =========================================================
# PARENT REPORTS
# =========================================================

class ParentSummaryReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        total = ParentProfile.objects.count()

        counts = ParentProfile.objects.annotate(
            cc=Count("students")
        )

        one = counts.filter(
            cc=1
        ).count()

        multi = counts.filter(
            cc__gt=1
        ).count()

        return Response(
            ParentSummarySerializer(
                {
                    "total_parents": total,
                    "parents_with_one_child": one,
                    "parents_with_multiple_children": multi,
                }
            ).data
        )


class ParentContactReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        parents = (
            ParentProfile.objects
            .select_related("user")
            .annotate(
                total_children=Count("students")
            )
            .order_by(
                "user__first_name",
                "user__last_name",
            )
        )

        data = []

        for parent in parents:

            name = (
                parent.user
                .get_full_name()
                .strip()
                or parent.user.username
            )

            data.append(
                {
                    "parent_name": name,
                    "phone_number": getattr(
                        parent.user,
                        "phone_number",
                        "",
                    ),
                    "address": parent.address,
                    "occupation": parent.occupation,
                    "total_children": (
                        parent.total_children
                    ),
                }
            )

        return Response(
            ParentContactSerializer(
                data,
                many=True,
            ).data
        )


class ParentChildrenReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        parents = (
            ParentProfile.objects
            .select_related("user")
            .prefetch_related(
                "students__classroom"
            )
            .annotate(
                total_children=Count("students")
            )
            .order_by(
                "user__first_name",
                "user__last_name",
            )
        )

        data = []

        for parent in parents:

            name = (
                parent.user
                .get_full_name()
                .strip()
                or parent.user.username
            )

            children = [
                {
                    "admission_number": (
                        student.admission_number
                    ),
                    "student_name": (
                        f"{student.first_name} "
                        f"{student.last_name}"
                    ),
                    "classroom": str(
                        student.classroom
                    ),
                    "status": student.status,
                }
                for student in parent.students.all()
            ]

            data.append(
                {
                    "parent_name": name,
                    "phone_number": getattr(
                        parent.user,
                        "phone_number",
                        "",
                    ),
                    "total_children": (
                        parent.total_children
                    ),
                    "children": children,
                }
            )

        return Response(
            ParentChildrenSerializer(
                data,
                many=True,
            ).data
        )


class ParentFeeReport(APIView):

    permission_classes = [
        IsAccountant,
    ]

    def get(self, request):

        parents = (
            ParentProfile.objects
            .select_related("user")
            .annotate(
                total_children=Count("students")
            )
            .order_by(
                "user__first_name",
                "user__last_name",
            )
        )

        data = []

        for parent in parents:

            name = (
                parent.user
                .get_full_name()
                .strip()
                or parent.user.username
            )

            summary = get_fee_summary(
                StudentFee.objects.filter(
                    student__parent=parent
                )
            )

            data.append(
                {
                    "parent_name": name,
                    "phone_number": getattr(
                        parent.user,
                        "phone_number",
                        "",
                    ),
                    "total_children": (
                        parent.total_children
                    ),
                    **summary,
                }
            )

        return Response(
            ParentFeeReportSerializer(
                data,
                many=True,
            ).data
        )


class ParentsWithOutstandingBalancesReport(APIView):

    permission_classes = [
        IsAccountant,
    ]

    def get(self, request):

        parents = (
            ParentProfile.objects
            .select_related("user")
            .annotate(
                total_children=Count("students")
            )
            .order_by(
                "user__first_name",
                "user__last_name",
            )
        )

        data = []

        for parent in parents:

            name = (
                parent.user
                .get_full_name()
                .strip()
                or parent.user.username
            )

            summary = get_fee_summary(
                StudentFee.objects.filter(
                    student__parent=parent
                )
            )

            if summary["balance"] > 0:

                data.append(
                    {
                        "parent_name": name,
                        "phone_number": getattr(
                            parent.user,
                            "phone_number",
                            "",
                        ),
                        "total_children": (
                            parent.total_children
                        ),
                        **summary,
                    }
                )

        return Response(
            ParentFeeReportSerializer(
                data,
                many=True,
            ).data
        )


# =========================================================
# CLASS & SCHOOL SUMMARY
# =========================================================

class ClassCapacityReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        rooms = (
            ClassRoom.objects
            .annotate(
                current_students=Count("students")
            )
            .order_by(
                "grade",
                "stream",
            )
        )

        data = [
            {
                "classroom": str(room),
                "capacity": room.capacity,
                "current_students": (
                    room.current_students
                ),
                "available_spaces": (
                    room.capacity
                    - room.current_students
                ),
            }
            for room in rooms
        ]

        return Response(
            ClassCapacityReportSerializer(
                data,
                many=True,
            ).data
        )


class SchoolSummaryReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        return Response(
            SchoolSummarySerializer(
                {
                    "total_students": (
                        Student.objects.count()
                    ),
                    "total_teachers": (
                        TeacherProfile.objects.count()
                    ),
                    "total_classes": (
                        ClassRoom.objects.count()
                    ),
                    "total_subjects": (
                        Subject.objects.count()
                    ),
                }
            ).data
        )


class DashboardStatisticsReport(APIView):

    permission_classes = [
        IsAcademicCoordinator,
    ]

    def get(self, request):

        fs = get_fee_summary()

        data = {
            "students": {
                "total": Student.objects.count(),
                "male": Student.objects.filter(
                    gender__iexact="Male"
                ).count(),
                "female": Student.objects.filter(
                    gender__iexact="Female"
                ).count(),
            },

            "teachers": {
                "total": TeacherProfile.objects.count(),
                "male": TeacherProfile.objects.filter(
                    gender__iexact="Male"
                ).count(),
                "female": TeacherProfile.objects.filter(
                    gender__iexact="Female"
                ).count(),
            },

            "fees": fs,

            "school": {
                "classes": ClassRoom.objects.count(),
                "subjects": Subject.objects.count(),
                "academic_year": timezone.now().year,
                "generated_at": timezone.now(),
            },
        }

        return Response(
            DashboardStatisticsSerializer(
                data
            ).data
        )


# =========================================================
# FINANCIAL REPORTS
# =========================================================

class FinancialReport(APIView):

    permission_classes = [
        IsAccountant,
    ]

    def get(self, request):

        report_type = request.query_params.get(
            "type",
            "income",
        )

        date_from_str = request.query_params.get(
            "date_from"
        )

        date_to_str = request.query_params.get(
            "date_to"
        )

        term = request.query_params.get(
            "term"
        )

        date_from = parse_date_param(
            date_from_str
        )

        date_to = parse_date_param(
            date_to_str
        )

        if not date_from or not date_to:
            return Response(
                {
                    "detail": (
                        "date_from and date_to "
                        "(YYYY-MM-DD) are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if date_from > date_to:
            return Response(
                {
                    "detail": (
                        "Start date cannot be "
                        "after end date."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_report_types = [
            "income",
            "expenses",
            "collection",
            "profit-loss",
        ]

        if report_type not in valid_report_types:
            return Response(
                {
                    "detail": (
                        "Invalid report type. "
                        "Use income, expenses, "
                        "collection or profit-loss."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payments_qs = get_payment_qs(
            date_from,
            date_to,
            term,
        )

        total_income = (
            payments_qs.aggregate(
                t=Sum("amount")
            )["t"]
            or 0
        )

        fee_qs = StudentFee.objects.all()

        if term:
            fee_qs = fee_qs.filter(
                fee_structure__term=term
            )

        total_expected = (
            fee_qs.aggregate(
                t=Sum("total_fee")
            )["t"]
            or 0
        )

        total_paid = (
            fee_qs.aggregate(
                t=Sum("amount_paid")
            )["t"]
            or 0
        )

        total_pending = (
            fee_qs.aggregate(
                t=Sum("balance")
            )["t"]
            or 0
        )

        collection_rate = (
            float(total_paid)
            / float(total_expected)
            * 100
            if total_expected
            else 0
        )

        details = [
            {
                "date": payment.payment_date,
                "student": (
                    f"{payment.student.first_name} "
                    f"{payment.student.last_name}"
                ),
                "admission_number": (
                    payment.student.admission_number
                ),
                "classroom": (
                    str(payment.student.classroom)
                    if payment.student.classroom
                    else "—"
                ),
                "amount": float(
                    payment.amount or 0
                ),
            }
            for payment in payments_qs.order_by(
                "-payment_date"
            )
        ]

        base = {
            "report_type": report_type,
            "date_from": date_from_str,
            "date_to": date_to_str,
            "term": term,
            "collected": float(total_paid),
            "pending": float(total_pending),
            "collection_rate": round(
                collection_rate,
                2,
            ),
        }

        if report_type == "collection":

            return Response(
                {
                    **base,
                    "details": details,
                }
            )

        if report_type == "income":

            return Response(
                {
                    **base,
                    "total_income": float(
                        total_income
                    ),
                    "details": details,
                }
            )

        if report_type == "expenses":

            return Response(
                {
                    **base,
                    "total_expenses": 0,
                    "details": [],
                }
            )

        if report_type == "profit-loss":

            total_expenses = 0

            return Response(
                {
                    **base,
                    "total_income": float(
                        total_income
                    ),
                    "total_expenses": total_expenses,
                    "net_balance": float(
                        total_income
                        - total_expenses
                    ),
                    "details": details,
                }
            )

        return Response(
            {
                "detail": (
                    "Invalid report type."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


# =========================================================
# FINANCIAL REPORT EXPORT
# =========================================================

class FinancialReportExport(APIView):

    permission_classes = [
        IsAccountant,
    ]

    def get(self, request):

        report_type = request.query_params.get(
            "type",
            "income",
        )

        date_from_str = request.query_params.get(
            "date_from"
        )

        date_to_str = request.query_params.get(
            "date_to"
        )

        term = request.query_params.get(
            "term"
        )

        export_format = (
            request.query_params.get(
                "format",
                "csv",
            )
            .lower()
        )

        date_from = parse_date_param(
            date_from_str
        )

        date_to = parse_date_param(
            date_to_str
        )

        if not date_from or not date_to:
            return Response(
                {
                    "detail": (
                        "date_from and date_to "
                        "(YYYY-MM-DD) are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if date_from > date_to:
            return Response(
                {
                    "detail": (
                        "Start date cannot be "
                        "after end date."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_report_types = [
            "income",
            "expenses",
            "collection",
            "profit-loss",
        ]

        if report_type not in valid_report_types:
            return Response(
                {
                    "detail": (
                        "Invalid report type."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_formats = [
            "csv",
            "xlsx",
            "pdf",
        ]

        if export_format not in valid_formats:
            return Response(
                {
                    "detail": (
                        "Invalid export format. "
                        "Use pdf, xlsx or csv."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payments = (
            get_payment_qs(
                date_from,
                date_to,
                term,
            )
            .order_by("-payment_date")
        )

        filename = f"{report_type}_report"

        # =================================================
        # CSV
        # =================================================

        if export_format == "csv":

            import csv

            response = HttpResponse(
                content_type="text/csv"
            )

            response[
                "Content-Disposition"
            ] = (
                f'attachment; '
                f'filename="{filename}.csv"'
            )

            writer = csv.writer(response)

            writer.writerow(
                [
                    "Date",
                    "Student",
                    "Admission Number",
                    "Class",
                    "Amount",
                ]
            )

            for payment in payments:

                student = payment.student

                writer.writerow(
                    [
                        payment.payment_date,
                        (
                            f"{student.first_name} "
                            f"{student.last_name}"
                        ),
                        student.admission_number,
                        (
                            str(student.classroom)
                            if student.classroom
                            else "—"
                        ),
                        payment.amount,
                    ]
                )

            return response

        # =================================================
        # XLSX
        # =================================================

        if export_format == "xlsx":

            try:
                from openpyxl import Workbook

            except ImportError:

                return Response(
                    {
                        "detail": (
                            "openpyxl is not installed."
                        )
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            workbook = Workbook()

            worksheet = workbook.active

            worksheet.title = "Financial Report"

            worksheet.append(
                [
                    "Date",
                    "Student",
                    "Admission Number",
                    "Class",
                    "Amount",
                ]
            )

            for payment in payments:

                student = payment.student

                worksheet.append(
                    [
                        str(
                            payment.payment_date
                        ),
                        (
                            f"{student.first_name} "
                            f"{student.last_name}"
                        ),
                        student.admission_number,
                        (
                            str(student.classroom)
                            if student.classroom
                            else "—"
                        ),
                        float(
                            payment.amount or 0
                        ),
                    ]
                )

            from io import BytesIO

            output = BytesIO()

            workbook.save(output)

            output.seek(0)

            response = HttpResponse(
                output.read(),
                content_type=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )

            response[
                "Content-Disposition"
            ] = (
                f'attachment; '
                f'filename="{filename}.xlsx"'
            )

            return response

        # =================================================
        # PDF
        # =================================================

        if export_format == "pdf":

            try:
                from reportlab.pdfgen import canvas

            except ImportError:

                return Response(
                    {
                        "detail": (
                            "reportlab is not installed."
                        )
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            response = HttpResponse(
                content_type="application/pdf"
            )

            response[
                "Content-Disposition"
            ] = (
                f'attachment; '
                f'filename="{filename}.pdf"'
            )

            pdf = canvas.Canvas(response)

            pdf.setTitle(
                REPORT_TITLES.get(
                    report_type,
                    "Financial Report",
                )
            )

            pdf.drawString(
                50,
                800,
                "Luma 2000 Academy",
            )

            pdf.drawString(
                50,
                780,
                REPORT_TITLES.get(
                    report_type,
                    "Financial Report",
                ),
            )

            pdf.drawString(
                50,
                760,
                (
                    f"Period: "
                    f"{date_from_str} "
                    f"to "
                    f"{date_to_str}"
                ),
            )

            if term:

                pdf.drawString(
                    50,
                    740,
                    f"Term: {term}",
                )

            y = 700

            headers = [
                "Date",
                "Student",
                "Admission",
                "Amount",
            ]

            positions = [
                50,
                150,
                320,
                430,
            ]

            for label, x in zip(
                headers,
                positions,
            ):

                pdf.drawString(
                    x,
                    y,
                    label,
                )

            y -= 20

            for payment in payments:

                if y < 50:

                    pdf.showPage()

                    y = 800

                student = payment.student

                pdf.drawString(
                    50,
                    y,
                    str(
                        payment.payment_date
                    )[:10],
                )

                pdf.drawString(
                    150,
                    y,
                    (
                        f"{student.first_name} "
                        f"{student.last_name}"
                    )[:25],
                )

                pdf.drawString(
                    320,
                    y,
                    str(
                        student.admission_number
                    ),
                )

                pdf.drawString(
                    430,
                    y,
                    (
                        f"{CURRENCY} "
                        f"{payment.amount}"
                    ),
                )

                y -= 18

            pdf.save()

            return response

        return Response(
            {
                "detail": (
                    "Invalid export format."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )