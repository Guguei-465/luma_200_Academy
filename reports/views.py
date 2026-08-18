from django.shortcuts import render
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import timedelta, datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.db.models.functions import ExtractYear, ExtractMonth

from fees.models import StudentFee, FeePayment
from accounts.models import ParentProfile, TeacherProfile
from assignments.models import TeacherAssignment
from classes.models import ClassRoom
from reports.serializers import (
    ClassCapacityReportSerializer, DashboardStatisticsSerializer,
    FeeCollectionByTermSerializer, FeeSummarySerializer,
    MonthlyFeeCollectionSerializer, NewAdmissionSerializer,
    OutstandingBalanceSerializer, ParentChildrenSerializer,
    ParentContactSerializer, ParentFeeReportSerializer,
    ParentSummarySerializer, SchoolSummarySerializer,
    StudentGenderReportSerializer, StudentStatusReportSerializer,
    StudentSummarySerializer, StudentsByClassSerializer,
    TeacherSummarySerializer, TeacherWorkloadSerializer,
    TeachersByClassSerializer, TeachersBySubjectSerializer,
)
from students.models import Student
from subjects.models import Subject
<<<<<<< HEAD
from reports.permissions import (
    IsAcademicCoordinator,
    IsAccountant,
)


# =========================================================
# SECURITY NOTE
#
# reports/permissions.py already defined proper role-scoped
# permission classes (IsAccountant, IsAcademicCoordinator,
# etc.) but NONE of them were ever imported/used below — every
# view here used only IsAuthenticated. That meant ANY logged-in
# user of ANY role, including a Parent, could pull financial
# reports/exports and bulk parent-contact/fee reports containing
# every OTHER family's name, phone, address, children, and fee
# balance — a severe violation of the spec's parent-isolation
# rule (T4) and general "backend must enforce role permissions
# on every view" rule. Every view below now uses the correct
# role restriction:
#   - Student/Teacher/parent-contact management reports ->
#     IsAcademicCoordinator (Super Admin + Academic Coordinator)
#   - Anything involving money (fee reports, financial reports/
#     exports, parent fee/balance reports) -> IsAccountant
#     (Super Admin + Accountant)
# =========================================================
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d

# === Constants ===
DATE_FORMAT = "%Y-%m-%d"
CURRENCY = "KSh"
REPORT_TITLES = {
    "income": "Income Financial Report",
    "expenses": "Expenses Financial Report",
    "collection": "Fee Collection Report",
    "profit-loss": "Profit & Loss Report",
}

# === Helpers ===
def parse_date_param(date_str):
    """Parse date string with explicit format validation."""
    try:
        return datetime.strptime(date_str, DATE_FORMAT).date()
    except (ValueError, TypeError):
        return None

def get_fee_summary(student_fee_qs=None):
    """Shared fee summary aggregator."""
    qs = student_fee_qs or StudentFee.objects.all()
    agg = qs.aggregate(total_fee=Sum("total_fee"), amount_paid=Sum("amount_paid"), balance=Sum("balance"))
    return {k: v or 0 for k, v in agg.items()}

def get_payment_qs(date_from, date_to, term=None):
    """Shared payment queryset for reports & exports."""
    qs = FeePayment.objects.filter(
        payment_date__date__gte=date_from,
        payment_date__date__lte=date_to,
    ).select_related("student", "student__classroom")
    if term:
        qs = qs.filter(student__studentfee__fee_structure__term=term).distinct()
    return qs

# =========================================================
# STUDENT REPORTS
# =========================================================
class StudentSummaryReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        total = Student.objects.count()
        male = Student.objects.filter(gender__iexact="Male").count()
        female = Student.objects.filter(gender__iexact="Female").count()
        return Response(StudentSummarySerializer({
            "total_students": total, "male_students": male, "female_students": female,
        }).data)

class StudentsByClassReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        report = (
            Student.objects.values("classroom__grade", "classroom__stream")
            .annotate(total_students=Count("id"))
            .order_by("classroom__grade", "classroom__stream")
        )
        data = [
            {"classroom": f"{i['classroom__grade']} {i['classroom__stream']}",
             "total_students": i["total_students"]}
            for i in report
        ]
        return Response(StudentsByClassSerializer(data, many=True).data)

class StudentsByGenderReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        report = Student.objects.values("gender").annotate(
            total_students=Count("id")
        ).order_by("gender")
        return Response(StudentGenderReportSerializer(report, many=True).data)

class NewAdmissionsReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        days = int(request.query_params.get("days", 30))
        start_date = timezone.now().date() - timedelta(days=days)
        students = Student.objects.filter(
            date_admitted__gte=start_date
        ).select_related("classroom").order_by("-date_admitted")
        data = [
            {"admission_number": s.admission_number,
             "student_name": f"{s.first_name} {s.last_name}",
             "classroom": str(s.classroom), "date_admitted": s.date_admitted}
            for s in students
        ]
        return Response(NewAdmissionSerializer(data, many=True).data)

class StudentStatusReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        report = Student.objects.values("status").annotate(
            total_students=Count("id")
        ).order_by("status")
        return Response(StudentStatusReportSerializer(report, many=True).data)

# =========================================================
# TEACHER REPORTS
# =========================================================
class TeacherSummaryReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        total = TeacherProfile.objects.count()
        male = TeacherProfile.objects.filter(gender__iexact="Male").count()
        female = TeacherProfile.objects.filter(gender__iexact="Female").count()
        return Response(TeacherSummarySerializer({
            "total_teachers": total, "male_teachers": male, "female_teachers": female,
        }).data)

class TeachersByClassReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        classrooms = ClassRoom.objects.select_related(
            "class_teacher__user"
        ).order_by("grade", "stream")
        data = []
        for cl in classrooms:
            t = None
            if cl.class_teacher:
                t = cl.class_teacher.user.get_full_name().strip() or cl.class_teacher.user.username
            data.append({"classroom": str(cl), "class_teacher": t})
        return Response(TeachersByClassSerializer(data, many=True).data)

class TeachersBySubjectReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        assignments = TeacherAssignment.objects.select_related(
            "teacher__user", "subject", "classroom"
        ).order_by("classroom__grade", "classroom__stream", "subject__name")
        data = []
        for a in assignments:
            tn = a.teacher.user.get_full_name().strip() or a.teacher.user.username
            data.append({"teacher": tn, "subject": a.subject.name,
                         "classroom": str(a.classroom), "term": a.term})
        return Response(TeachersBySubjectSerializer(data, many=True).data)

class TeacherWorkloadReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        workload = TeacherAssignment.objects.values(
            "teacher__user__first_name", "teacher__user__last_name", "teacher__user__username"
        ).annotate(
            total_assignments=Count("id"),
            total_classes=Count("classroom", distinct=True),
            total_subjects=Count("subject", distinct=True),
        ).order_by("teacher__user__first_name", "teacher__user__last_name")
        data = []
        for i in workload:
            name = f"{i['teacher__user__first_name']} {i['teacher__user__last_name']}".strip()
            name = name or i["teacher__user__username"]
            data.append({"teacher": name, "total_assignments": i["total_assignments"],
                         "total_classes": i["total_classes"], "total_subjects": i["total_subjects"]})
        return Response(TeacherWorkloadSerializer(data, many=True).data)

# =========================================================
# FEE REPORTS
# =========================================================
class FeeSummaryReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAccountant]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        return Response(FeeSummarySerializer(get_fee_summary()).data)

class OutstandingBalancesReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAccountant]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        accounts = StudentFee.objects.filter(balance__gt=0).select_related(
            "student", "student__classroom", "fee_structure"
        ).order_by("-balance")
        data = [
            {
                "admission_number": a.student.admission_number,
                "student_name": f"{a.student.first_name} {a.student.last_name}",
                "classroom": str(a.student.classroom),
                "academic_year": a.fee_structure.academic_year,
                "term": a.fee_structure.term,
                "total_fee": a.total_fee, "amount_paid": a.amount_paid, "balance": a.balance,
            }
            for a in accounts
        ]
        return Response(OutstandingBalanceSerializer(data, many=True).data)

class FeeCollectionByTermReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAccountant]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        report = StudentFee.objects.values(
            "fee_structure__academic_year", "fee_structure__term"
        ).annotate(
            total_fee=Sum("total_fee"), amount_paid=Sum("amount_paid"), balance=Sum("balance")
        ).order_by("-fee_structure__academic_year", "fee_structure__term")
        data = [
            {
                "academic_year": i["fee_structure__academic_year"],
                "term": i["fee_structure__term"],
                "total_fee": i["total_fee"] or 0,
                "amount_paid": i["amount_paid"] or 0,
                "balance": i["balance"] or 0,
            }
            for i in report
        ]
        return Response(FeeCollectionByTermSerializer(data, many=True).data)

class MonthlyFeeCollectionReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAccountant]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        report = FeePayment.objects.annotate(
            year=ExtractYear("payment_date"), month=ExtractMonth("payment_date")
        ).values("year", "month").annotate(
            total_payments=Count("id"), total_amount=Sum("amount")
        ).order_by("-year", "-month")
        return Response(MonthlyFeeCollectionSerializer(report, many=True).data)

# =========================================================
# PARENT REPORTS
# =========================================================
class ParentSummaryReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        total = ParentProfile.objects.count()
        counts = ParentProfile.objects.annotate(cc=Count("students"))
        one = counts.filter(cc=1).count()
        multi = counts.filter(cc__gt=1).count()
        return Response(ParentSummarySerializer({
            "total_parents": total, "parents_with_one_child": one,
            "parents_with_multiple_children": multi,
        }).data)

class ParentContactReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        parents = ParentProfile.objects.select_related("user").annotate(
            total_children=Count("students")
        ).order_by("user__first_name", "user__last_name")
        data = []
        for p in parents:
            name = p.user.get_full_name().strip() or p.user.username
            data.append({
                "parent_name": name, "phone_number": getattr(p.user, "phone_number", ""),
                "address": p.address, "occupation": p.occupation, "total_children": p.total_children,
            })
        return Response(ParentContactSerializer(data, many=True).data)

class ParentChildrenReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        parents = ParentProfile.objects.select_related("user").prefetch_related(
            "students__classroom"
        ).annotate(total_children=Count("students")).order_by("user__first_name", "user__last_name")
        data = []
        for p in parents:
            name = p.user.get_full_name().strip() or p.user.username
            children = [
                {"admission_number": s.admission_number,
                 "student_name": f"{s.first_name} {s.last_name}",
                 "classroom": str(s.classroom), "status": s.status}
                for s in p.students.all()
            ]
            data.append({
                "parent_name": name, "phone_number": getattr(p.user, "phone_number", ""),
                "total_children": p.total_children, "children": children,
            })
        return Response(ParentChildrenSerializer(data, many=True).data)

class ParentFeeReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAccountant]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        parents = ParentProfile.objects.select_related("user").annotate(
            total_children=Count("students")
        ).order_by("user__first_name", "user__last_name")
        data = []
        for p in parents:
            name = p.user.get_full_name().strip() or p.user.username
            summary = get_fee_summary(StudentFee.objects.filter(student__parent=p))
            data.append({
                "parent_name": name, "phone_number": getattr(p.user, "phone_number", ""),
                "total_children": p.total_children, **summary,
            })
        return Response(ParentFeeReportSerializer(data, many=True).data)

class ParentsWithOutstandingBalancesReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAccountant]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        parents = ParentProfile.objects.select_related("user").annotate(
            total_children=Count("students")
        ).order_by("user__first_name", "user__last_name")
        data = []
        for p in parents:
            name = p.user.get_full_name().strip() or p.user.username
            summary = get_fee_summary(StudentFee.objects.filter(student__parent=p))
            if summary["balance"] > 0:
                data.append({
                    "parent_name": name, "phone_number": getattr(p.user, "phone_number", ""),
                    "total_children": p.total_children, **summary,
                })
        return Response(ParentFeeReportSerializer(data, many=True).data)

# =========================================================
# CLASS & SCHOOL SUMMARY
# =========================================================
class ClassCapacityReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        rooms = ClassRoom.objects.annotate(
            current_students=Count("students")
        ).order_by("grade", "stream")
        data = [
            {"classroom": str(r), "capacity": r.capacity,
             "current_students": r.current_students,
             "available_spaces": r.capacity - r.current_students}
            for r in rooms
        ]
        return Response(ClassCapacityReportSerializer(data, many=True).data)

class SchoolSummaryReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        return Response(SchoolSummarySerializer({
            "total_students": Student.objects.count(),
            "total_teachers": TeacherProfile.objects.count(),
            "total_classes": ClassRoom.objects.count(),
            "total_subjects": Subject.objects.count(),
        }).data)

class DashboardStatisticsReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAcademicCoordinator]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        fs = get_fee_summary()
        data = {
            "students": {
                "total": Student.objects.count(),
                "male": Student.objects.filter(gender__iexact="Male").count(),
                "female": Student.objects.filter(gender__iexact="Female").count(),
            },
            "teachers": {
                "total": TeacherProfile.objects.count(),
                "male": TeacherProfile.objects.filter(gender__iexact="Male").count(),
                "female": TeacherProfile.objects.filter(gender__iexact="Female").count(),
            },
            "fees": fs,
            "school": {
                "classes": ClassRoom.objects.count(),
                "subjects": Subject.objects.count(),
                "academic_year": timezone.now().year,
                "generated_at": timezone.now(),
            },
        }
        return Response(DashboardStatisticsSerializer(data).data)

# =========================================================
# FINANCIAL REPORTS
# =========================================================
class FinancialReport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAccountant]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        report_type = request.query_params.get("type", "income")
        date_from_str = request.query_params.get("date_from")
        date_to_str = request.query_params.get("date_to")
        term = request.query_params.get("term")

        date_from = parse_date_param(date_from_str)
        date_to = parse_date_param(date_to_str)
        if not date_from or not date_to:
            return Response({"detail": "date_from and date_to (YYYY-MM-DD) are required."}, status=400)
        if date_from > date_to:
            return Response({"detail": "Start date cannot be after end date."}, status=400)

        payments_qs = get_payment_qs(date_from, date_to, term)
        total_income = payments_qs.aggregate(t=Sum("amount"))["t"] or 0

        fee_qs = StudentFee.objects.all()
        if term:
            fee_qs = fee_qs.filter(fee_structure__term=term)
        total_expected = fee_qs.aggregate(t=Sum("total_fee"))["t"] or 0
        total_paid = fee_qs.aggregate(t=Sum("amount_paid"))["t"] or 0
        total_pending = fee_qs.aggregate(t=Sum("balance"))["t"] or 0
        collection_rate = (float(total_paid) / float(total_expected) * 100) if total_expected else 0

        details = [
            {
                "date": p.payment_date,
                "student": f"{p.student.first_name} {p.student.last_name}",
                "admission_number": p.student.admission_number,
                "classroom": str(p.student.classroom) if p.student.classroom else "—",
                "amount": float(p.amount or 0),
            }
            for p in payments_qs.order_by("-payment_date")
        ]

        base = {
            "report_type": report_type, "date_from": date_from_str, "date_to": date_to_str,
            "term": term, "collected": float(total_paid), "pending": float(total_pending),
            "collection_rate": round(collection_rate, 2),
        }

        if report_type == "collection":
            return Response({**base, "details": details})
        elif report_type == "income":
            return Response({**base, "total_income": float(total_income), "details": details})
        elif report_type == "expenses":
            return Response({**base, "total_expenses": 0, "details": []})
        elif report_type == "profit-loss":
            total_expenses = 0
            return Response({
                **base, "total_income": float(total_income),
                "total_expenses": total_expenses, "net_balance": float(total_income - total_expenses),
                "details": details,
            })
        return Response({"detail": "Invalid report type. Use income, expenses, collection or profit-loss."}, status=400)

# =========================================================
# FINANCIAL REPORT EXPORT
# =========================================================
class FinancialReportExport(APIView):
<<<<<<< HEAD
    permission_classes = [IsAccountant]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
    def get(self, request):
        report_type = request.query_params.get("type", "income")
        date_from_str = request.query_params.get("date_from")
        date_to_str = request.query_params.get("date_to")
        term = request.query_params.get("term")
        export_format = request.query_params.get("format", "csv").lower()

        date_from = parse_date_param(date_from_str)
        date_to = parse_date_param(date_to_str)
        if not date_from or not date_to:
            return Response({"detail": "date_from and date_to (YYYY-MM-DD) are required."}, status=400)

        payments = get_payment_qs(date_from, date_to, term).order_by("-payment_date")

        filename = f"{report_type}_report"

        if export_format == "csv":
            import csv
            resp = HttpResponse(content_type="text/csv")
            resp["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
            w = csv.writer(resp)
            w.writerow(["Date", "Student", "Admission Number", "Class", "Amount"])
            for p in payments:
                s = p.student
                w.writerow([
                    p.payment_date, f"{s.first_name} {s.last_name}",
                    s.admission_number, str(s.classroom) if s.classroom else "—", p.amount,
                ])
            return resp

        elif export_format == "xlsx":
            try:
                from openpyxl import Workbook
            except ImportError:
                return Response({"detail": "openpyxl is not installed."}, status=500)
            wb = Workbook()
            ws = wb.active
            ws.title = "Financial Report"
            ws.append(["Date", "Student", "Admission Number", "Class", "Amount"])
            for p in payments:
                s = p.student
                ws.append([
                    str(p.payment_date), f"{s.first_name} {s.last_name}",
                    s.admission_number, str(s.classroom) if s.classroom else "—",
                    float(p.amount or 0),
                ])
            from io import BytesIO
            out = BytesIO()
            wb.save(out)
            out.seek(0)
            resp = HttpResponse(
                out.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            resp["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
            return resp

        elif export_format == "pdf":
            try:
                from reportlab.pdfgen import canvas
            except ImportError:
                return Response({"detail": "reportlab is not installed."}, status=500)
            resp = HttpResponse(content_type="application/pdf")
            resp["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
            pdf = canvas.Canvas(resp)
            pdf.setTitle(REPORT_TITLES.get(report_type, "Financial Report"))
            pdf.drawString(50, 800, "Luma 2000 Academy")
            pdf.drawString(50, 780, REPORT_TITLES.get(report_type, "Financial Report"))
            pdf.drawString(50, 760, f"Period: {date_from_str} to {date_to_str}")
            if term:
                pdf.drawString(50, 740, f"Term: {term}")
            y = 700
            for label, x in zip(["Date", "Student", "Admission", "Amount"], [50, 150, 320, 430]):
                pdf.drawString(x, y, label)
            y -= 20
            for p in payments:
                s = p.student
                if y < 50:
                    pdf.showPage()
                    y = 800
                pdf.drawString(50, y, str(p.payment_date)[:10])
                pdf.drawString(150, y, f"{s.first_name} {s.last_name}"[:25])
                pdf.drawString(320, y, str(s.admission_number))
                pdf.drawString(430, y, f"{CURRENCY} {p.amount}")
                y -= 18
            pdf.save()
            return resp

        return Response({"detail": "Invalid export format. Use pdf, xlsx or csv."}, status=400)