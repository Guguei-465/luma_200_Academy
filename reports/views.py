from django.shortcuts import render
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from fees.models import (
    StudentFee,
    FeePayment,
)
from datetime import datetime
from django.http import HttpResponse
from django.db.models.functions import ExtractYear, ExtractMonth
from accounts.models import ParentProfile, TeacherProfile
from assignments.models import TeacherAssignment
from classes.models import ClassRoom
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
from students.models import Student
from subjects.models import Subject

# Create your views here. 
class StudentSummaryReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        total_students = Student.objects.count()

        male_students = Student.objects.filter(
            gender__iexact="Male"
        ).count()

        female_students = Student.objects.filter(
            gender__iexact="Female"
        ).count()

        serializer = StudentSummarySerializer({
            "total_students": total_students,
            "male_students": male_students,
            "female_students": female_students,
        })

        return Response(serializer.data)


class StudentsByClassReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        report = (
            Student.objects
            .values("classroom__grade", "classroom__stream")
            .annotate(total_students=Count("id"))
            .order_by("classroom__grade", "classroom__stream")
        )

        data = [
            {
                "classroom": f"{item['classroom__grade']} {item['classroom__stream']}",
                "total_students": item["total_students"],
            }
            for item in report
        ]

        serializer = StudentsByClassSerializer(data, many=True)
        return Response(serializer.data)
    
class StudentsByGenderReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        report = (
            Student.objects
            .values("gender")
            .annotate(total_students=Count("id"))
            .order_by("gender")
        )

        serializer = StudentGenderReportSerializer(report, many=True)
        return Response(serializer.data)


class NewAdmissionsReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 30))

        start_date = timezone.now().date() - timedelta(days=days)

        students = Student.objects.filter(
            date_admitted__gte=start_date
        ).select_related("classroom").order_by("-date_admitted")

        data = [
            {
                "admission_number": student.admission_number,
                "student_name": f"{student.first_name} {student.last_name}",
                "classroom": str(student.classroom),
                "date_admitted": student.date_admitted,
            }
            for student in students
        ]

        serializer = NewAdmissionSerializer(data, many=True)
        return Response(serializer.data)
    
class TeacherSummaryReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        total_teachers = TeacherProfile.objects.count()

        male_teachers = TeacherProfile.objects.filter(
            gender__iexact="Male"
        ).count()

        female_teachers = TeacherProfile.objects.filter(
            gender__iexact="Female"
        ).count()

        serializer = TeacherSummarySerializer({
            "total_teachers": total_teachers,
            "male_teachers": male_teachers,
            "female_teachers": female_teachers,
        })

        return Response(serializer.data)


class TeachersByClassReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        classrooms = (
            ClassRoom.objects
            .select_related("class_teacher__user")
            .order_by("grade", "stream")
        )

        data = []

        for classroom in classrooms:
            teacher = None

            if classroom.class_teacher:
                teacher = classroom.class_teacher.user.get_full_name()

                if not teacher.strip():
                    teacher = classroom.class_teacher.user.username

            data.append({
                "classroom": str(classroom),
                "class_teacher": teacher,
            })

        serializer = TeachersByClassSerializer(data, many=True)
        return Response(serializer.data)


class TeachersBySubjectReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        assignments = (
            TeacherAssignment.objects
            .select_related(
                "teacher__user",
                "subject",
                "classroom"
            )
            .order_by(
                "classroom__grade",
                "classroom__stream",
                "subject__name"
            )
        )

        data = []

        for assignment in assignments:
            teacher_name = assignment.teacher.user.get_full_name()

            if not teacher_name.strip():
                teacher_name = assignment.teacher.user.username

            data.append({
                "teacher": teacher_name,
                "subject": assignment.subject.name,
                "classroom": str(assignment.classroom),
                "term": assignment.term,
            })

        serializer = TeachersBySubjectSerializer(data, many=True)
        return Response(serializer.data)


class TeacherWorkloadReport(APIView):
    permission_classes = [IsAuthenticated]

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
                total_classes=Count("classroom", distinct=True),
                total_subjects=Count("subject", distinct=True),
            )
            .order_by(
                "teacher__user__first_name",
                "teacher__user__last_name",
            )
        )

        data = []

        for item in workload:
            full_name = (
                f"{item['teacher__user__first_name']} "
                f"{item['teacher__user__last_name']}"
            ).strip()

            if not full_name:
                full_name = item["teacher__user__username"]

            data.append({
                "teacher": full_name,
                "total_assignments": item["total_assignments"],
                "total_classes": item["total_classes"],
                "total_subjects": item["total_subjects"],
            })

        serializer = TeacherWorkloadSerializer(data, many=True)
        return Response(serializer.data)



class FeeSummaryReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        summary = StudentFee.objects.aggregate(
            total_fee=Sum("total_fee"),
            amount_paid=Sum("amount_paid"),
            balance=Sum("balance"),
        )

        serializer = FeeSummarySerializer({
            "total_fee": summary["total_fee"] or 0,
            "amount_paid": summary["amount_paid"] or 0,
            "balance": summary["balance"] or 0,
        })

        return Response(serializer.data)


class OutstandingBalancesReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student_fees = (
            StudentFee.objects
            .filter(balance__gt=0)
            .select_related(
                "student",
                "student__classroom",
                "fee_structure",
            )
            .order_by("-balance")
        )

        data = []

        for account in student_fees:
            data.append({
                "admission_number": account.student.admission_number,
                "student_name": (
                    f"{account.student.first_name} "
                    f"{account.student.last_name}"
                ),
                "classroom": str(account.student.classroom),
                "academic_year": account.fee_structure.academic_year,
                "term": account.fee_structure.term,
                "total_fee": account.total_fee,
                "amount_paid": account.amount_paid,
                "balance": account.balance,
            })

        serializer = OutstandingBalanceSerializer(data, many=True)
        return Response(serializer.data)


class FeeCollectionByTermReport(APIView):
    permission_classes = [IsAuthenticated]

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

        data = []

        for item in report:
            data.append({
                "academic_year": item["fee_structure__academic_year"],
                "term": item["fee_structure__term"],
                "total_fee": item["total_fee"] or 0,
                "amount_paid": item["amount_paid"] or 0,
                "balance": item["balance"] or 0,
            })

        serializer = FeeCollectionByTermSerializer(data, many=True)
        return Response(serializer.data)

class MonthlyFeeCollectionReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        report = (
            FeePayment.objects
            .annotate(
                year=ExtractYear("payment_date"),
                month=ExtractMonth("payment_date"),
            )
            .values("year", "month")
            .annotate(
                total_payments=Count("id"),
                total_amount=Sum("amount"),
            )
            .order_by("-year", "-month")
        )

        serializer = MonthlyFeeCollectionSerializer(
            report,
            many=True
        )

        return Response(serializer.data)
    
class SchoolSummaryReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = SchoolSummarySerializer({
            "total_students": Student.objects.count(),
            "total_teachers": TeacherProfile.objects.count(),
            "total_classes": ClassRoom.objects.count(),
            "total_subjects": Subject.objects.count(),
        })

        return Response(serializer.data)


class DashboardStatisticsReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        fee_summary = StudentFee.objects.aggregate(
            total_fee=Sum("total_fee"),
            amount_paid=Sum("amount_paid"),
            balance=Sum("balance"),
        )

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

            "fees": {
                "total_fee": fee_summary["total_fee"] or 0,
                "amount_paid": fee_summary["amount_paid"] or 0,
                "balance": fee_summary["balance"] or 0,
            },

            "school": {
                "classes": ClassRoom.objects.count(),
                "subjects": Subject.objects.count(),
                "academic_year": timezone.now().year,
                "generated_at": timezone.now(),
            },
        }

        serializer = DashboardStatisticsSerializer(data)

        return Response(serializer.data)

# perents views
class ParentSummaryReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        total_parents = ParentProfile.objects.count()

        parent_counts = (
            ParentProfile.objects
            .annotate(total_children=Count("students"))
        )

        parents_with_one_child = parent_counts.filter(
            total_children=1
        ).count()

        parents_with_multiple_children = parent_counts.filter(
            total_children__gt=1
        ).count()

        serializer = ParentSummarySerializer({
            "total_parents": total_parents,
            "parents_with_one_child": parents_with_one_child,
            "parents_with_multiple_children": parents_with_multiple_children,
        })

        return Response(serializer.data)


class ParentContactReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        parents = (
            ParentProfile.objects
            .select_related("user")
            .annotate(total_children=Count("students"))
            .order_by("user__first_name", "user__last_name")
        )

        data = []

        for parent in parents:
            full_name = parent.user.get_full_name()
            if not full_name.strip():
                full_name = parent.user.username

            data.append({
                "parent_name": full_name,
                "phone_number": parent.user.phone_number,
                "address": parent.address,
                "occupation": parent.occupation,
                "total_children": parent.total_children,
            })

        serializer = ParentContactSerializer(data, many=True)
        return Response(serializer.data)


class ParentChildrenReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        parents = (
            ParentProfile.objects
            .select_related("user")
            .prefetch_related("students__classroom")
            .annotate(total_children=Count("students"))
            .order_by("user__first_name", "user__last_name")
        )

        data = []

        for parent in parents:

            full_name = parent.user.get_full_name()
            if not full_name.strip():
                full_name = parent.user.username

            children = []

            for student in parent.students.all():
                children.append({
                    "admission_number": student.admission_number,
                    "student_name": f"{student.first_name} {student.last_name}",
                    "classroom": str(student.classroom),
                    "status": student.status,
                })

            data.append({
                "parent_name": full_name,
                "phone_number": parent.user.phone_number,
                "total_children": parent.total_children,
                "children": children,
            })

        serializer = ParentChildrenSerializer(data, many=True)
        return Response(serializer.data)


class ParentFeeReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        parents = (
            ParentProfile.objects
            .select_related("user")
            .annotate(total_children=Count("students"))
            .order_by("user__first_name", "user__last_name")
        )

        data = []

        for parent in parents:

            full_name = parent.user.get_full_name()
            if not full_name.strip():
                full_name = parent.user.username

            summary = StudentFee.objects.filter(
                student__parent=parent
            ).aggregate(
                total_fee=Sum("total_fee"),
                amount_paid=Sum("amount_paid"),
                balance=Sum("balance"),
            )

            data.append({
                "parent_name": full_name,
                "phone_number": parent.user.phone_number,
                "total_children": parent.total_children,
                "total_fee": summary["total_fee"] or 0,
                "amount_paid": summary["amount_paid"] or 0,
                "balance": summary["balance"] or 0,
            })

        serializer = ParentFeeReportSerializer(data, many=True)
        return Response(serializer.data)


class ParentsWithOutstandingBalancesReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        parents = (
            ParentProfile.objects
            .select_related("user")
            .annotate(total_children=Count("students"))
            .order_by("user__first_name", "user__last_name")
        )

        data = []

        for parent in parents:

            summary = StudentFee.objects.filter(
                student__parent=parent
            ).aggregate(
                total_fee=Sum("total_fee"),
                amount_paid=Sum("amount_paid"),
                balance=Sum("balance"),
            )

            balance = summary["balance"] or 0

            if balance <= 0:
                continue

            full_name = parent.user.get_full_name()
            if not full_name.strip():
                full_name = parent.user.username

            data.append({
                "parent_name": full_name,
                "phone_number": parent.user.phone_number,
                "total_children": parent.total_children,
                "total_fee": summary["total_fee"] or 0,
                "amount_paid": summary["amount_paid"] or 0,
                "balance": balance,
            })

        serializer = ParentFeeReportSerializer(data, many=True)
        return Response(serializer.data)

# class?students
class ClassCapacityReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        classrooms = (
            ClassRoom.objects
            .annotate(current_students=Count("students"))
            .order_by("grade", "stream")
        )

        data = []

        for classroom in classrooms:
            data.append({
                "classroom": str(classroom),
                "capacity": classroom.capacity,
                "current_students": classroom.current_students,
                "available_spaces": classroom.capacity - classroom.current_students,
            })

        serializer = ClassCapacityReportSerializer(
            data,
            many=True
        )

        return Response(serializer.data)


class StudentStatusReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        report = (
            Student.objects
            .values("status")
            .annotate(total_students=Count("id"))
            .order_by("status")
        )

        serializer = StudentStatusReportSerializer(
            report,
            many=True
        )

        return Response(serializer.data)

# =========================================================
# FINANCIAL REPORT
# =========================================================

class FinancialReport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        report_type = request.query_params.get(
            "type",
            "income"
        )

        date_from = request.query_params.get(
            "date_from"
        )

        date_to = request.query_params.get(
            "date_to"
        )

        term = request.query_params.get(
            "term"
        )

        # -------------------------------------------------
        # VALIDATE DATES
        # -------------------------------------------------

        if not date_from or not date_to:
            return Response(
                {
                    "detail": "date_from and date_to are required."
                },
                status=400,
            )

        try:
            start_date = datetime.strptime(
                date_from,
                "%Y-%m-%d"
            ).date()

            end_date = datetime.strptime(
                date_to,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return Response(
                {
                    "detail": "Dates must use YYYY-MM-DD format."
                },
                status=400,
            )

        if start_date > end_date:
            return Response(
                {
                    "detail": "Start date cannot be after end date."
                },
                status=400,
            )

        # -------------------------------------------------
        # FEE PAYMENTS
        # -------------------------------------------------

        payments = FeePayment.objects.filter(
            payment_date__date__gte=start_date,
            payment_date__date__lte=end_date,
        ).select_related(
            "student",
            "student__classroom",
        )

        # -------------------------------------------------
        # FILTER BY TERM
        # -------------------------------------------------

        if term:
            payments = payments.filter(
                student__studentfee__fee_structure__term=term
            ).distinct()

        # -------------------------------------------------
        # TOTAL INCOME
        # -------------------------------------------------

        total_income = payments.aggregate(
            total=Sum("amount")
        )["total"] or 0

        # -------------------------------------------------
        # DETAILS
        # -------------------------------------------------

        details = []

        for payment in payments.order_by("-payment_date"):

            student = payment.student

            details.append({
                "date": payment.payment_date,
                "student": (
                    f"{student.first_name} "
                    f"{student.last_name}"
                ),
                "admission_number": (
                    student.admission_number
                ),
                "classroom": (
                    str(student.classroom)
                    if student.classroom
                    else "—"
                ),
                "amount": float(
                    payment.amount or 0
                ),
            })

        # -------------------------------------------------
        # COLLECTION STATUS
        # -------------------------------------------------

        fee_filter = {}

        if term:
            fee_filter[
                "fee_structure__term"
            ] = term

        student_fees = StudentFee.objects.filter(
            **fee_filter
        )

        total_expected = student_fees.aggregate(
            total=Sum("total_fee")
        )["total"] or 0

        total_paid = student_fees.aggregate(
            total=Sum("amount_paid")
        )["total"] or 0

        total_pending = student_fees.aggregate(
            total=Sum("balance")
        )["total"] or 0

        collection_rate = 0

        if total_expected:
            collection_rate = (
                float(total_paid)
                / float(total_expected)
            ) * 100

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        if report_type == "collection":

            return Response({
                "report_type": "collection",
                "date_from": date_from,
                "date_to": date_to,
                "term": term,

                "collected": float(total_paid),
                "pending": float(total_pending),

                "collection_rate": round(
                    collection_rate,
                    2
                ),

                "details": details,
            })

        # -------------------------------------------------
        # INCOME
        # -------------------------------------------------

        if report_type == "income":

            return Response({
                "report_type": "income",
                "date_from": date_from,
                "date_to": date_to,
                "term": term,

                "total_income": float(
                    total_income
                ),

                "collected": float(
                    total_paid
                ),

                "pending": float(
                    total_pending
                ),

                "collection_rate": round(
                    collection_rate,
                    2
                ),

                "details": details,
            })

        # -------------------------------------------------
        # EXPENSES
        # -------------------------------------------------

        if report_type == "expenses":

            return Response({
                "report_type": "expenses",
                "date_from": date_from,
                "date_to": date_to,
                "term": term,

                "total_expenses": 0,

                "details": [],
            })

        # -------------------------------------------------
        # PROFIT / LOSS
        # -------------------------------------------------

        if report_type == "profit-loss":

            total_expenses = 0

            net_balance = (
                float(total_income)
                - total_expenses
            )

            return Response({
                "report_type": "profit-loss",
                "date_from": date_from,
                "date_to": date_to,
                "term": term,

                "total_income": float(
                    total_income
                ),

                "total_expenses": float(
                    total_expenses
                ),

                "net_balance": float(
                    net_balance
                ),

                "details": details,
            })

        return Response(
            {
                "detail": (
                    "Invalid report type. "
                    "Use income, expenses, "
                    "collection or profit-loss."
                )
            },
            status=400,
        )


# =========================================================
# FINANCIAL REPORT EXPORT
# =========================================================

class FinancialReportExport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        report_type = request.query_params.get(
            "type",
            "income"
        )

        date_from = request.query_params.get(
            "date_from"
        )

        date_to = request.query_params.get(
            "date_to"
        )

        term = request.query_params.get(
            "term"
        )

        export_format = request.query_params.get(
            "format",
            "csv"
        ).lower()

        if not date_from or not date_to:
            return Response(
                {
                    "detail": (
                        "date_from and date_to "
                        "are required."
                    )
                },
                status=400,
            )

        # -------------------------------------------------
        # GET PAYMENTS
        # -------------------------------------------------

        payments = FeePayment.objects.filter(
            payment_date__date__gte=date_from,
            payment_date__date__lte=date_to,
        ).select_related(
            "student",
            "student__classroom",
        )

        # -------------------------------------------------
        # TERM
        # -------------------------------------------------

        if term:
            payments = payments.filter(
                student__studentfee__fee_structure__term=term
            ).distinct()

        # -------------------------------------------------
        # CSV
        # -------------------------------------------------

        if export_format == "csv":

            import csv

            response = HttpResponse(
                content_type="text/csv"
            )

            response[
                "Content-Disposition"
            ] = (
                f'attachment; filename="{report_type}_report.csv"'
            )

            writer = csv.writer(response)

            writer.writerow([
                "Date",
                "Student",
                "Admission Number",
                "Class",
                "Amount",
            ])

            for payment in payments.order_by(
                "-payment_date"
            ):

                student = payment.student

                writer.writerow([
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
                ])

            return response

        # -------------------------------------------------
        # XLSX
        # -------------------------------------------------

        if export_format == "xlsx":

            try:
                from openpyxl import Workbook
            except ImportError:
                return Response(
                    {
                        "detail":
                        "openpyxl is not installed."
                    },
                    status=500,
                )

            workbook = Workbook()

            worksheet = workbook.active
            worksheet.title = "Financial Report"

            worksheet.append([
                "Date",
                "Student",
                "Admission Number",
                "Class",
                "Amount",
            ])

            for payment in payments.order_by(
                "-payment_date"
            ):

                student = payment.student

                worksheet.append([
                    str(payment.payment_date),
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
                    float(payment.amount or 0),
                ])

            from io import BytesIO

            output = BytesIO()

            workbook.save(output)

            output.seek(0)

            response = HttpResponse(
                output.read(),
                content_type=(
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
            )

            response[
                "Content-Disposition"
            ] = (
                f'attachment; filename="{report_type}_report.xlsx"'
            )

            return response

        # -------------------------------------------------
        # PDF
        # -------------------------------------------------

        if export_format == "pdf":

            try:
                from reportlab.pdfgen import canvas
            except ImportError:
                return Response(
                    {
                        "detail":
                        "reportlab is not installed."
                    },
                    status=500,
                )

            response = HttpResponse(
                content_type="application/pdf"
            )

            response[
                "Content-Disposition"
            ] = (
                f'attachment; filename="{report_type}_report.pdf"'
            )

            pdf = canvas.Canvas(response)

            pdf.setTitle(
                f"{report_type.title()} Financial Report"
            )

            pdf.drawString(
                50,
                800,
                "Luma 2000 Academy"
            )

            pdf.drawString(
                50,
                780,
                f"{report_type.title()} Financial Report"
            )

            pdf.drawString(
                50,
                760,
                f"Period: {date_from} to {date_to}"
            )

            if term:
                pdf.drawString(
                    50,
                    740,
                    f"Term: {term}"
                )

            y = 700

            pdf.drawString(
                50,
                y,
                "Date"
            )

            pdf.drawString(
                150,
                y,
                "Student"
            )

            pdf.drawString(
                320,
                y,
                "Admission"
            )

            pdf.drawString(
                430,
                y,
                "Amount"
            )

            y -= 20

            for payment in payments.order_by(
                "-payment_date"
            ):

                student = payment.student

                pdf.drawString(
                    50,
                    y,
                    str(payment.payment_date)[:10]
                )

                pdf.drawString(
                    150,
                    y,
                    (
                        f"{student.first_name} "
                        f"{student.last_name}"
                    )[:25]
                )

                pdf.drawString(
                    320,
                    y,
                    str(
                        student.admission_number
                    )
                )

                pdf.drawString(
                    430,
                    y,
                    f"KSh {payment.amount}"
                )

                y -= 18

                if y < 50:
                    pdf.showPage()
                    y = 800

            pdf.save()

            return response

        return Response(
            {
                "detail": (
                    "Invalid export format. "
                    "Use pdf, xlsx or csv."
                )
            },
            status=400,
        )
