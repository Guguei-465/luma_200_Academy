from decimal import Decimal
from django.utils import timezone
from django.db.models import Count, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from anouncements.models import Announcement
from dashboard.permissions import IsAcademicCoordinator, IsDashboardUser, IsSuperAdmin
from results.models import Result
from students.models import Student
from assignments.models import TeacherProfile
from parents.models import ParentProfile
from classes.models import ClassRoom
from subjects.models import Subject
from attendance.models import Attendance
from fees.models import FeePayment, StudentFee
from exams.models import Exam
from notifiations.models import Notification
from .serializers import AttendanceSummarySerializer, DashboardFeeSummarySerializer, DashboardSerializer, ExamPerformanceSerializer, RecentPaymentSerializer, TopStudentSerializer, UpcomingNotificationSerializer
from django.db.models import Avg, Max, Min
from results.models import Result
from results.utils import calculate_cbc_grade

grade, description = calculate_cbc_grade(82)


class TopOutstandingStudentsAPIView(APIView):

    permission_classes = [IsDashboardUser]

    def get(self, request):

        students = (
            Result.objects
            .values(
                "student",
                "student__photo",
                "student__assessment_number",
                "student__admission_number",
                "student__first_name",
                "student__last_name",
                "student__classroom__grade",
            )
            .annotate(
                average_score=Avg("marks")
            )
            .exclude(average_score=None)
            .order_by("-average_score")[:10]
        )

        data = []

        position = 1

        for student in students:

            average = round(student["average_score"], 2)

            if average >= 90:
                grade = "EE1"
            elif average >= 75:
                grade = "EE2"
            elif average >= 58:
                grade = "ME1"
            elif average>=41:
                grade = "ME2"
            elif average >=31:
                grade="AE1"
            elif average >=21:
                grade="AE2"
            elif average >=11:
                grade="BE1"
            elif average >=1:
                grade ="BE2"
            else:
                return "no grade cam be below zero(0)"

            data.append({
                "position": position,
                "photo": student["student__photo"],
                "assessment_number": student["student__assessment_number"],
                "admission_number": student["student__admission_number"],
                "student_name": (
                    f'{student["student__first_name"]} '
                    f'{student["student__last_name"]}'
                ),
                "classroom": student["student__classroom__grade"],
                "average_score": average,
                "grade": grade,
            })

            position += 1

        serializer = TopStudentSerializer(
            data,
            many=True,
        )

        return Response(serializer.data)

class DashboardAPIView(APIView):
    """
    Main Dashboard Statistics
    """

    permission_classes = [IsAcademicCoordinator, IsSuperAdmin]

    def get(self, request):

        # =====================================
        # Students
        # =====================================

        total_students = Student.objects.count()

        active_students = Student.objects.filter(
            status=Student.Status.ACTIVE
        ).count()

        boys = Student.objects.filter(
            gender=Student.Gender.MALE
        ).count()

        girls = Student.objects.filter(
            gender=Student.Gender.FEMALE
        ).count()

        # =====================================
        # Teachers
        # =====================================

        total_teachers = TeacherProfile.objects.count()

        # =====================================
        # Parents
        # =====================================

        total_parents = ParentProfile.objects.count()

        # =====================================
        # Classes
        # =====================================

        total_classes = ClassRoom.objects.count()

        # =====================================
        # Subjects
        # =====================================

        total_subjects = Subject.objects.count()

        # =====================================
        # Fees
        # =====================================

        fees = StudentFee.objects.aggregate(
            total_fee=Sum("total_fee"),
            total_paid=Sum("amount_paid"),
            total_balance=Sum("balance"),
        )

        # =====================================
        # Attendance
        # =====================================

        total_attendance = Attendance.objects.count()

        present = Attendance.objects.filter(
            status="Present"
        ).count()

        if total_attendance > 0:
            attendance_today = round(
                (present / total_attendance) * 100,
                2,
            )
        else:
            attendance_today = Decimal("0.00")

        # =====================================
        # Exams
        # =====================================

        total_exams = Exam.objects.count()

        # =====================================
        # Results
        # =====================================

        total_results = Result.objects.count()

        # =====================================
        # Notifications
        # =====================================

        unread_notifications = Notification.objects.filter(
            is_read=False
        ).count()

        data = {
            "total_students": total_students,
            "active_students": active_students,
            "boys": boys,
            "girls": girls,
            "total_teachers": total_teachers,
            "total_classes": total_classes,
            "total_subjects": total_subjects,
            "total_parents": total_parents,
            "attendance_today": attendance_today,
            "total_fee": fees["total_fee"] or Decimal("0.00"),
            "total_paid": fees["total_paid"] or Decimal("0.00"),
            "total_balance": fees["total_balance"] or Decimal("0.00"),
            "total_exams": total_exams,
            "total_results": total_results,
            "unread_notifications": unread_notifications,
        }

        serializer = DashboardSerializer(data)

        return Response(serializer.data)


from django.db.models import Avg, Count

from .serializers import TopClassSerializer


class TopPerformingClassesAPIView(APIView):

    permission_classes = [IsDashboardUser]

    def get(self, request):

        classes = (
            Result.objects
            .values(
                "student__classroom",
                "student__classroom__grade",
            )
            .annotate(
                average_score=Avg("marks"),
                total_students=Count(
                    "student",
                    distinct=True,
                ),
            )
            .order_by("-average_score")
        )

        data = []

        position = 1

        for classroom in classes:

            data.append({
                "position": position,
                "classroom": classroom[
                    "student__classroom__grade"
                ],
                "average_score": round(
                    classroom["average_score"],
                    2,
                ),
                "total_students": classroom[
                    "total_students"
                ],
            })

            position += 1

        serializer = TopClassSerializer(
            data,
            many=True,
        )

        return Response(serializer.data)


class RecentFeePaymentsAPIView(APIView):

    permission_classes = [IsDashboardUser]

    def get(self, request):

        payments = (
            FeePayment.objects
            .select_related(
                "student_fee__student",
            )
            .order_by("-payment_date")[:10]
        )

        data = []

        for payment in payments:

            data.append({
                "receipt_number": payment.receipt_number,
                "student_name": (
                    f"{payment.student_fee.student.first_name} "
                    f"{payment.student_fee.student.last_name}"
                ),
                "admission_number": payment.student_fee.student.admission_number,
                "amount": payment.amount,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date,
                "payment_status": payment.payment_status,
            })

        serializer = RecentPaymentSerializer(
            data,
            many=True,
        )

        return Response(serializer.data)


from .serializers import RecentAdmissionSerializer


class RecentAdmissionsAPIView(APIView):

    permission_classes = [IsDashboardUser]

    def get(self, request):

        students = (
            Student.objects
            .select_related("classroom")
            .order_by("-date_admitted")[:10]
        )

        data = []

        for student in students:

            data.append({
                "photo": student.photo,
                "admission_number": student.admission_number,
                "assessment_number": student.assessment_number,
                "student_name": (
                    f"{student.first_name} "
                    f"{student.last_name}"
                ),
                "classroom": str(student.classroom),
                "date_admitted": student.date_admitted,
            })

        serializer = RecentAdmissionSerializer(
            data,
            many=True,
        )

        return Response(serializer.data)
    
class TodayAttendanceSummaryAPIView(APIView):

    permission_classes = [IsDashboardUser]

    def get(self, request):

        today = timezone.localdate()

        attendance = Attendance.objects.filter(
            marked_at__date=today
        )

        present = attendance.filter(
            status=Attendance.Status.PRESENT
        ).count()

        absent = attendance.filter(
            status=Attendance.Status.ABSENT
        ).count()

        excused = attendance.filter(
            status=Attendance.Status.EXCUSED
        ).count()

        total = attendance.count()

        if total > 0:
            percentage = round(
                (present / total) * 100,
                2,
            )
        else:
            percentage = 0

        serializer = AttendanceSummarySerializer(
            {
                "present": present,
                "absent": absent,
                "excused": excused,
                "total": total,
                "attendance_percentage": percentage,
            }
        )

        return Response(serializer.data)    
    

class DashboardFeeSummaryAPIView(APIView):

    permission_classes = [IsDashboardUser]

    def get(self, request):

        fees = StudentFee.objects.aggregate(
            expected_fee=Sum("total_fee"),
            collected_fee=Sum("amount_paid"),
            outstanding_fee=Sum("balance"),
        )

        expected = fees["expected_fee"] or Decimal("0.00")
        collected = fees["collected_fee"] or Decimal("0.00")
        outstanding = fees["outstanding_fee"] or Decimal("0.00")

        if expected > 0:
            percentage = round(
                (collected / expected) * 100,
                2,
            )
        else:
            percentage = Decimal("0.00")

        total_transactions = FeePayment.objects.count()

        serializer = DashboardFeeSummarySerializer(
            {
                "expected_fee": expected,
                "collected_fee": collected,
                "outstanding_fee": outstanding,
                "collection_percentage": percentage,
                "total_transactions": total_transactions,
            }
        )

        return Response(serializer.data)


class ExamPerformanceDashboardAPIView(APIView):

    permission_classes = [IsDashboardUser]

    def get(self, request):

        total_exams = Exam.objects.count()

        published_results = Result.objects.count()

        pending_results = max(
            total_exams - published_results,
            0,
        )

        stats = Result.objects.aggregate(
            overall_average=Avg("marks"),
            highest_score=Max("marks"),
            lowest_score=Min("marks"),
        )

        serializer = ExamPerformanceSerializer(
            {
                "total_exams": total_exams,
                "published_results": published_results,
                "pending_results": pending_results,
                "overall_average": (
                    stats["overall_average"]
                    or Decimal("0.00")
                ),
                "highest_score": (
                    stats["highest_score"]
                    or Decimal("0.00")
                ),
                "lowest_score": (
                    stats["lowest_score"]
                    or Decimal("0.00")
                ),
            }
        )

        return Response(serializer.data)


class UpcomingNotificationsAPIView(APIView):

    permission_classes = [IsDashboardUser]

    def get(self, request):

        announcements = (
            Announcement.objects
            .select_related("created_by")
            .order_by("-created_at")[:10]
        )

        data = []

        for announcement in announcements:

            creator = (
                announcement.created_by.get_full_name()
                if announcement.created_by
                else "System"
            )

            data.append({
                "id": announcement.id,
                "title": announcement.title,
                "message": announcement.message,
                "priority": announcement.priority,
                "target": announcement.target,
                "created_at": announcement.created_at,
                "created_by": creator,
            })

        serializer = UpcomingNotificationSerializer(
            data,
            many=True,
        )

        return Response(serializer.data)