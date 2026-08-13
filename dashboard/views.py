from decimal import Decimal
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Max, Min
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from timetable.models import Timetable
from anouncements.models import Announcement
from dashboard.permissions import IsAcademicCoordinator, IsDashboardUser, IsSuperAdmin, IsTeacher
from results.models import Result
from students.models import Student
from assignments.models import TeacherProfile, TeacherAssignment
from accounts.models import ParentProfile
from classes.models import ClassRoom
from subjects.models import Subject
from attendance.models import Attendance
from fees.models import FeePayment, StudentFee
from exams.models import Exam
from notifiations.models import Notification
from results.models import StudentResult, StudentTermResult, ResultSubmission, Assessment
from .serializers import (
    AttendanceSummarySerializer,
    DashboardFeeSummarySerializer,
    DashboardSerializer,
    ExamPerformanceSerializer,
    RecentPaymentSerializer,
    TopStudentSerializer,
    UpcomingNotificationSerializer,
    TopClassSerializer,
    RecentAdmissionSerializer,
    ParentDashboardSerializer,
    ParentChildSerializer,
    ParentChildDetailsSerializer,
    TeacherStudentSerializer,
    TeacherStudentDetailsSerializer,
    TeacherStudentResultUpdateSerializer,
    TeacherDashboardSerializer,
)


# ==========================================
# Helper Functions
# ==========================================

def is_class_teacher(user):
    if not hasattr(user, "teacher_profile"):
        return False
    return ClassRoom.objects.filter(
        class_teacher=user.teacher_profile
    ).exists()


def calculate_grade(marks):
    """Calculate grade from marks."""
    if marks >= 90:
        return "EE1"
    elif marks >= 75:
        return "EE2"
    elif marks >= 58:
        return "ME1"
    elif marks >= 41:
        return "ME2"
    elif marks >= 31:
        return "AE1"
    elif marks >= 21:
        return "AE2"
    elif marks >= 11:
        return "BE1"
    elif marks >= 1:
        return "BE2"
    return "N/A"


def calculate_student_subject_result(student, assessment):
    return None


def calculate_student_term_result(student, classroom, term, academic_year):
    return None


def calculate_class_positions(classroom, term, academic_year):
    return None


# ==========================================
# API Views
# ==========================================

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
            .annotate(average_score=Avg("marks"))
            .exclude(average_score=None)
            .order_by("-average_score")[:10]
        )

        data = []
        for position, student in enumerate(students, start=1):
            average = round(student["average_score"], 2)
            grade = calculate_grade(average)

            data.append({
                "position": position,
                "photo": student["student__photo"],
                "assessment_number": student["student__assessment_number"],
                "admission_number": student["student__admission_number"],
                "student_name": f'{student["student__first_name"]} {student["student__last_name"]}',
                "classroom": student["student__classroom__grade"],
                "average_score": average,
                "grade": grade,
            })

        serializer = TopStudentSerializer(data, many=True)
        return Response(serializer.data)


class DashboardAPIView(APIView):
    """Main Dashboard Statistics"""
    permission_classes = [IsAcademicCoordinator, IsSuperAdmin]

    def get(self, request):
        total_students = Student.objects.count()
        active_students = Student.objects.filter(status=Student.Status.ACTIVE).count()
        boys = Student.objects.filter(gender=Student.Gender.MALE).count()
        girls = Student.objects.filter(gender=Student.Gender.FEMALE).count()
        total_teachers = TeacherProfile.objects.count()
        total_parents = ParentProfile.objects.count()
        total_classes = ClassRoom.objects.count()
        total_subjects = Subject.objects.count()

        fees = StudentFee.objects.aggregate(
            total_fee=Sum("total_fee"),
            total_paid=Sum("amount_paid"),
            total_balance=Sum("balance"),
        )

        total_attendance = Attendance.objects.count()
        present = Attendance.objects.filter(status=Attendance.Status.PRESENT).count()
        attendance_today = round((present / total_attendance) * 100, 2) if total_attendance > 0 else Decimal("0.00")

        total_exams = Exam.objects.count()
        total_results = Result.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()

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


class TopPerformingClassesAPIView(APIView):
    permission_classes = [IsDashboardUser]

    def get(self, request):
        classes = (
            Result.objects
            .values("student__classroom", "student__classroom__grade")
            .annotate(
                average_score=Avg("marks"),
                total_students=Count("student", distinct=True),
            )
            .order_by("-average_score")
        )

        data = [
            {
                "position": position,
                "classroom": classroom["student__classroom__grade"],
                "average_score": round(classroom["average_score"], 2),
                "total_students": classroom["total_students"],
            }
            for position, classroom in enumerate(classes, start=1)
        ]

        serializer = TopClassSerializer(data, many=True)
        return Response(serializer.data)


class RecentFeePaymentsAPIView(APIView):
    permission_classes = [IsDashboardUser]

    def get(self, request):
        payments = (
            FeePayment.objects
            .select_related("student_fee__student")
            .order_by("-payment_date")[:10]
        )

        data = [
            {
                "receipt_number": payment.receipt_number,
                "student_name": f"{payment.student_fee.student.first_name} {payment.student_fee.student.last_name}",
                "admission_number": payment.student_fee.student.admission_number,
                "amount": payment.amount,
                "payment_method": payment.payment_method,
                "payment_date": payment.payment_date,
                "payment_status": payment.payment_status,
            }
            for payment in payments
        ]

        serializer = RecentPaymentSerializer(data, many=True)
        return Response(serializer.data)


class RecentAdmissionsAPIView(APIView):
    permission_classes = [IsDashboardUser]

    def get(self, request):
        students = (
            Student.objects
            .select_related("classroom")
            .order_by("-date_admitted")[:10]
        )

        data = [
            {
                "photo": student.photo,
                "admission_number": student.admission_number,
                "assessment_number": student.assessment_number,
                "student_name": f"{student.first_name} {student.last_name}",
                "classroom": str(student.classroom),
                "date_admitted": student.date_admitted,
            }
            for student in students
        ]

        serializer = RecentAdmissionSerializer(data, many=True)
        return Response(serializer.data)


class TodayAttendanceSummaryAPIView(APIView):
    permission_classes = [IsDashboardUser]

    def get(self, request):
        today = timezone.localdate()
        attendance = Attendance.objects.filter(marked_at__date=today)

        present = attendance.filter(status=Attendance.Status.PRESENT).count()
        absent = attendance.filter(status=Attendance.Status.ABSENT).count()
        excused = attendance.filter(status=Attendance.Status.EXCUSED).count()
        total = attendance.count()

        percentage = round((present / total) * 100, 2) if total > 0 else 0

        serializer = AttendanceSummarySerializer({
            "present": present,
            "absent": absent,
            "excused": excused,
            "total": total,
            "attendance_percentage": percentage,
        })
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
        percentage = round((collected / expected) * 100, 2) if expected > 0 else Decimal("0.00")
        total_transactions = FeePayment.objects.count()

        serializer = DashboardFeeSummarySerializer({
            "expected_fee": expected,
            "collected_fee": collected,
            "outstanding_fee": outstanding,
            "collection_percentage": percentage,
            "total_transactions": total_transactions,
        })
        return Response(serializer.data)


class ExamPerformanceDashboardAPIView(APIView):
    permission_classes = [IsDashboardUser]

    def get(self, request):
        total_exams = Exam.objects.count()
        published_results = Result.objects.count()
        pending_results = max(total_exams - published_results, 0)

        stats = Result.objects.aggregate(
            overall_average=Avg("marks"),
            highest_score=Max("marks"),
            lowest_score=Min("marks"),
        )

        serializer = ExamPerformanceSerializer({
            "total_exams": total_exams,
            "published_results": published_results,
            "pending_results": pending_results,
            "overall_average": stats["overall_average"] or Decimal("0.00"),
            "highest_score": stats["highest_score"] or Decimal("0.00"),
            "lowest_score": stats["lowest_score"] or Decimal("0.00"),
        })
        return Response(serializer.data)


class UpcomingNotificationsAPIView(APIView):
    permission_classes = [IsDashboardUser]

    def get(self, request):
        announcements = (
            Announcement.objects
            .select_related("created_by")
            .order_by("-created_at")[:10]
        )

        data = [
            {
                "id": announcement.id,
                "title": announcement.title,
                "message": announcement.message,
                "priority": announcement.priority,
                "target": announcement.target,
                "created_at": announcement.created_at,
                "created_by": announcement.created_by.get_full_name() if announcement.created_by else "System",
            }
            for announcement in announcements
        ]

        serializer = UpcomingNotificationSerializer(data, many=True)
        return Response(serializer.data)


class ParentDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        parent = ParentProfile.objects.filter(user=request.user).first()
        if not parent:
            return Response({"detail": "Parent profile not found."}, status=404)

        students = Student.objects.filter(parent=parent)
        children_count = students.count()

        fee_summary = StudentFee.objects.filter(student__in=students).aggregate(
            total_balance=Sum("balance")
        )
        total_fee_balance = fee_summary["total_balance"] or Decimal("0.00")

        attendance = Attendance.objects.filter(student__in=students)
        total = attendance.count()
        present = attendance.filter(status=Attendance.Status.PRESENT).count()
        overall_attendance = round((present / total) * 100, 2) if total > 0 else Decimal("0.00")

        unread_notifications = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()

        announcements = Announcement.objects.order_by("-created_at")[:5]

        serializer = ParentDashboardSerializer({
            "parent_name": request.user.get_full_name(),
            "children_count": children_count,
            "total_fee_balance": total_fee_balance,
            "overall_attendance": overall_attendance,
            "unread_notifications": unread_notifications,
            "announcements": announcements,
        })
        return Response(serializer.data)


class ParentChildrenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        parent = ParentProfile.objects.filter(user=request.user).first()
        if not parent:
            return Response([])

        students = (
            Student.objects
            .filter(parent=parent)
            .select_related(
                "classroom",
                "classroom__class_teacher",
                "classroom__class_teacher__user",
            )
        )

        data = []
        for student in students:
            teacher = student.classroom.class_teacher if student.classroom else None

            attendance = Attendance.objects.filter(student=student)
            total = attendance.count()
            present = attendance.filter(status=Attendance.Status.PRESENT).count()
            attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

            fee_balance = (
                StudentFee.objects.filter(student=student)
                .aggregate(balance=Sum("balance"))["balance"] or Decimal("0.00")
            )

            latest_result = (
                StudentTermResult.objects.filter(student=student)
                .order_by("-id").first()
            )

            data.append({
                "id": student.id,
                "photo": student.photo,
                "admission_number": student.admission_number,
                "assessment_number": student.assessment_number,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "grade": student.classroom.grade if student.classroom else None,
                "stream": student.classroom.stream if student.classroom else None,
                "class_teacher": teacher.user.get_full_name() if teacher else None,
                "teacher_phone": teacher.user.phone_number if teacher else None,
                "attendance_percentage": attendance_percentage,
                "latest_grade": latest_result.overall_grade if latest_result else "-",
                "fee_balance": fee_balance,
                "status": student.status,
            })

        serializer = ParentChildSerializer(data, many=True)
        return Response(serializer.data)


class ParentChildDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        parent = get_object_or_404(ParentProfile, user=request.user)
        student = get_object_or_404(
            Student.objects.select_related(
                "classroom",
                "classroom__class_teacher",
                "classroom__class_teacher__user",
            ),
            id=id,
            parent=parent,
        )

        classroom = student.classroom
        teacher = classroom.class_teacher if classroom else None

        attendance = Attendance.objects.filter(student=student)
        total = attendance.count()
        present = attendance.filter(status=Attendance.Status.PRESENT).count()
        attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

        fee_balance = (
            StudentFee.objects.filter(student=student)
            .aggregate(balance=Sum("balance"))["balance"] or Decimal("0.00")
        )

        latest_result = (
            StudentTermResult.objects.filter(student=student)
            .order_by("-id").first()
        )

        data = {
            "id": student.id,
            "photo": student.photo.url if student.photo else None,
            "admission_number": student.admission_number,
            "assessment_number": student.assessment_number,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "gender": student.gender,
            "date_of_birth": student.date_of_birth,
            "grade": classroom.grade if classroom else None,
            "stream": classroom.stream if classroom else None,
            "class_teacher": teacher.user.get_full_name() if teacher else None,
            "teacher_phone": teacher.user.phone_number if teacher else None,
            "relationship": "Parent",
            "date_admitted": student.date_admitted,
            "status": student.status,
            "attendance_percentage": attendance_percentage,
            "latest_grade": latest_result.overall_grade if latest_result else "-",
            "fee_balance": fee_balance,
        }

        serializer = ParentChildDetailsSerializer(data)
        return Response(serializer.data)


class TeacherDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        teacher = request.user.teacher_profile
        assignments = TeacherAssignment.objects.filter(teacher=teacher, is_active=True)

        data = {
            "teacher_name": request.user.get_full_name(),
            "is_class_teacher": is_class_teacher(request.user),
            "total_assignments": assignments.count(),
            "total_subjects": assignments.values("subject").distinct().count(),
            "total_classes": assignments.values("classroom").distinct().count(),
            "pending_results": ResultSubmission.objects.filter(
                submitted_by=request.user,
                approval_status__in=[
                    ResultSubmission.ApprovalStatus.DRAFT,
                    ResultSubmission.ApprovalStatus.RETURNED,
                ],
            ).count(),
        }
        return Response(data)


# ==========================================
# Teacher Students — COMPLETED
# ==========================================

class TeacherStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        teacher = request.user.teacher_profile
        assignments = TeacherAssignment.objects.filter(teacher=teacher, is_active=True)

        # Get all classrooms this teacher teaches
        classroom_ids = assignments.values_list("classroom", flat=True).distinct()
        subject_ids = assignments.values_list("subject", flat=True).distinct()

        # Get all students in those classrooms
        students = (
            Student.objects
            .filter(classroom__in=classroom_ids)
            .select_related("classroom", "parent")
            .order_by("classroom__grade", "last_name", "first_name")
        )

        data = []
        for student in students:
            # Attendance
            attendance = Attendance.objects.filter(student=student)
            total = attendance.count()
            present = attendance.filter(status=Attendance.Status.PRESENT).count()
            attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

            # Latest term result
            latest_result = (
                StudentTermResult.objects.filter(student=student)
                .order_by("-id").first()
            )

            data.append({
                "id": student.id,
                "photo": student.photo.url if student.photo else None,
                "admission_number": student.admission_number,
                "assessment_number": student.assessment_number,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "grade": student.classroom.grade,
                "stream": student.classroom.stream,
                "attendance_percentage": attendance_percentage,
                "latest_grade": latest_result.overall_grade if latest_result else "-",
                "status": student.status,
            })

        serializer = TeacherStudentSerializer(data, many=True)
        return Response(serializer.data)

# ==========================================
# Teacher Student Details
# ==========================================

class TeacherStudentDetailsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request, pk):

        teacher = request.user.teacher_profile

        classroom_ids = TeacherAssignment.objects.filter(
            teacher=teacher,
            is_active=True,
        ).values_list("classroom_id", flat=True)

        student = get_object_or_404(
            Student.objects.select_related("classroom"),
            pk=pk,
            classroom_id__in=classroom_ids,
        )

        data = {
            "id": student.id,
            "photo": student.photo,
            "admission_number": student.admission_number,
            "assessment_number": student.assessment_number,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "gender": student.gender,
            "date_of_birth": student.date_of_birth,
            "grade": student.classroom.grade,
            "stream": student.classroom.stream,
            "date_admitted": student.date_admitted,
            "parent_name": student.parent_name,
            "parent_phone": student.parent_phone,
            "attendance_percentage": 0,
            "latest_grade": "-",
            "class_teacher": is_class_teacher(request.user),
        }

        serializer = TeacherStudentDetailsSerializer(data)
        return Response(serializer.data)


# ==========================================
# Teacher Student Results
# ==========================================

class TeacherStudentResultsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request, pk):

        teacher = request.user.teacher_profile

        classroom_ids = TeacherAssignment.objects.filter(
            teacher=teacher,
            is_active=True,
        ).values_list("classroom_id", flat=True)

        student = get_object_or_404(
            Student,
            pk=pk,
            classroom_id__in=classroom_ids,
        )

        results = (
            StudentResult.objects
            .filter(student=student)
            .select_related("subject", "grade")
            .order_by("subject__name")
        )

        data = [
            {
                "id": result.id,
                "subject": result.subject.name,
                "score": result.average_score,
                "grade": result.grade.level if result.grade else "-",
                "cbc_code": result.cbc_code,
                "description": result.cbc_description,
            }
            for result in results
        ]

        return Response(data)


# ==========================================
# Teacher Update Student Result
# ==========================================

class TeacherUpdateStudentResultAPIView(APIView):

    permission_classes = [IsAuthenticated, IsTeacher]

    def patch(self, request, pk):

        result = get_object_or_404(StudentResult, pk=pk)
        teacher = request.user.teacher_profile

        assignment_exists = TeacherAssignment.objects.filter(
            teacher=teacher,
            subject=result.subject,
            classroom=result.classroom,
            is_active=True,
        ).exists()

        if not assignment_exists:
            return Response(
                {"detail": "You are not assigned to teach this subject."},
                status=403,
            )

        serializer = TeacherStudentResultUpdateSerializer(
            result,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


# ==========================================
# Teacher Assessments
# ==========================================

class TeacherAssessmentListAPIView(APIView):

    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):

        teacher = request.user.teacher_profile

        assignments = TeacherAssignment.objects.filter(
            teacher=teacher,
            is_active=True,
        )

        assessments = Assessment.objects.filter(
            classroom__in=assignments.values("classroom"),
            subject__in=assignments.values("subject"),
        ).select_related(
            "assessment_type", "classroom", "subject"
        ).order_by("-assessment_date")

        data = [
            {
                "id": assessment.id,
                "assessment_type": assessment.assessment_type.name,
                "subject": assessment.subject.name,
                "classroom": str(assessment.classroom),
                "term": assessment.term,
                "academic_year": assessment.academic_year,
                "assessment_date": assessment.assessment_date,
                "total_marks": assessment.total_marks,
            }
            for assessment in assessments
        ]

        return Response(data)


# ==========================================
# Assessment Mark Entry
# ==========================================

class TeacherAssessmentDetailsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request, pk):

        assessment = get_object_or_404(
            Assessment.objects.select_related(
                "classroom", "subject", "assessment_type"
            ),
            pk=pk,
        )

        students = Student.objects.filter(
            classroom=assessment.classroom,
        ).order_by("first_name", "last_name")

        data = [
            {
                "student_id": student.id,
                "admission_number": student.admission_number,
                "student_name": f"{student.first_name} {student.last_name}",
                "marks": "",
                "status": "Pending",
            }
            for student in students
        ]

        return Response({
            "assessment": {
                "id": assessment.id,
                "subject": assessment.subject.name,
                "assessment_type": assessment.assessment_type.name,
                "classroom": str(assessment.classroom),
                "term": assessment.term,
                "academic_year": assessment.academic_year,
                "total_marks": assessment.total_marks,
            },
            "students": data,
        })


# ==========================================
# Save Assessment Marks
# ==========================================

class TeacherSaveAssessmentMarksAPIView(APIView):

    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request, pk):

        assessment = get_object_or_404(Assessment, pk=pk)

        submission, _ = ResultSubmission.objects.get_or_create(
            assessment=assessment,
            defaults={"submitted_by": request.user},
        )

        for item in request.data.get("students", []):

            student = Student.objects.get(pk=item["student_id"])
            marks = item["marks"]
            grade = calculate_grade(marks)

            Result.objects.update_or_create(
                submission=submission,
                student=student,
                defaults={
                    "marks": marks,
                    "weighted_marks": marks,
                    "grade": grade,
                    "cbc_code": grade.level if grade else "",
                    "cbc_description": grade.description if grade else "",
                    "grade_remarks": grade.remarks if grade else "",
                    "entered_by": request.user,
                    "last_modified_by": request.user,
                    "status": Result.ResultStatus.PRESENT,
                },
            )
            calculate_student_subject_result(student, assessment)
            calculate_student_term_result(
                student,
                assessment.classroom,
                assessment.term,
                assessment.academic_year,
            )
            calculate_class_positions(
                assessment.classroom,
                assessment.term,
                assessment.academic_year,
            )

        return Response({"message": "Marks saved successfully."})


class TeacherDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):

        teacher = request.user.teacher_profile

        assignments = TeacherAssignment.objects.filter(
            teacher=teacher,
            is_active=True,
        )

        assigned_classes = assignments.values(
            "classroom"
        ).distinct().count()

        assigned_subjects = assignments.values(
            "subject"
        ).distinct().count()

        total_students = Student.objects.filter(
            classroom__in=assignments.values("classroom")
        ).distinct().count()

        today = timezone.localdate().strftime("%A")

        today_lessons = Timetable.objects.filter(
            assignment__teacher=teacher,
            day=today,
            is_active=True,
        ).count()

        pending_results = ResultSubmission.objects.filter(
            submitted_by=request.user,
            approval_status__in=[
                ResultSubmission.ApprovalStatus.DRAFT,
                ResultSubmission.ApprovalStatus.RETURNED,
            ],
        ).count()

        data = {
            "teacher_name": request.user.get_full_name(),
            "is_class_teacher": is_class_teacher(request.user),
            "assigned_classes": assigned_classes,
            "assigned_subjects": assigned_subjects,
            "total_students": total_students,
            "today_lessons": today_lessons,
            "pending_results": pending_results,
        }

        serializer = TeacherDashboardSerializer(data)

        return Response(serializer.data)

# =====================================================
# PARENT REPORT CARDS
# =====================================================

class ParentReportCardsAPIView(APIView):
    """
    Returns report cards belonging only to the
    children of the currently logged-in parent.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # =============================================
        # Find logged-in parent's profile
        # =============================================

        parent = ParentProfile.objects.filter(
            user=request.user
        ).first()

        if not parent:
            return Response(
                {
                    "detail": "Parent profile not found."
                },
                status=404
            )

        # =============================================
        # Get ONLY this parent's children
        # =============================================

        students = Student.objects.filter(
            parent=parent
        ).select_related(
            "classroom"
        )

        # =============================================
        # Get term results for those children
        # =============================================

        term_results = (
            StudentTermResult.objects
            .filter(
                student__in=students
            )
            .select_related(
                "student",
                "student__classroom",
                "overall_grade",
            )
            .order_by(
                "-academic_year",
                "-term",
                "student__first_name",
                "student__last_name",
            )
        )

        data = []

        for result in term_results:

            student = result.student
            classroom = student.classroom

            data.append({
                "student_id": student.id,

                "first_name": student.first_name,

                "last_name": student.last_name,

                "photo": student.photo,

                "admission_number": student.admission_number,

                "assessment_number": student.assessment_number,

                "grade": (
                    classroom.grade
                    if classroom
                    else ""
                ),

                "stream": (
                    classroom.stream
                    if classroom
                    else ""
                ),

                "academic_year": result.academic_year,

                "term": result.term,

                "average_score": result.average_marks,

                "grade_letter": (
                    result.overall_grade.level
                    if result.overall_grade
                    else result.cbc_code or "—"
                ),

                "total_marks": result.total_marks,

                "total_subjects": result.total_subjects,

                "position": result.position,

                "attendance_percentage": (
                    result.attendance_percentage
                ),

                "class_teacher_comment": (
                    result.class_teacher_comment
                ),

                "headteacher_comment": (
                    result.headteacher_comment
                ),
            })

        return Response(data)
    