from decimal import Decimal
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Max, Min
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from anouncements.models import Announcement
from dashboard.permissions import IsAcademicCoordinator, IsDashboardUser, IsSuperAdmin, IsTeacher
from results.models import Result
from students.models import Student
from assignments.models import TeacherProfile, TeacherAssignment
from parents.models import ParentProfile, ParentStudent
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
        position = 1

        for student in students:
            average = round(student["average_score"], 2)

            if average >= 90:
                grade = "EE1"
            elif average >= 75:
                grade = "EE2"
            elif average >= 58:
                grade = "ME1"
            elif average >= 41:
                grade = "ME2"
            elif average >= 31:
                grade = "AE1"
            elif average >= 21:
                grade = "AE2"
            elif average >= 11:
                grade = "BE1"
            elif average >= 1:
                grade = "BE2"
            else:
                grade = "N/A"

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

        serializer = TopStudentSerializer(data, many=True)
        return Response(serializer.data)


class DashboardAPIView(APIView):
    """
    Main Dashboard Statistics
    """

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
        present = Attendance.objects.filter(status="Present").count()

        if total_attendance > 0:
            attendance_today = round((present / total_attendance) * 100, 2)
        else:
            attendance_today = Decimal("0.00")

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
                "student_name": (
                    f"{payment.student_fee.student.first_name} "
                    f"{payment.student_fee.student.last_name}"
                ),
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
                "created_by": (
                    announcement.created_by.get_full_name()
                    if announcement.created_by
                    else "System"
                ),
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

        students = ParentStudent.objects.filter(parent=parent).select_related("student")
        student_list = [item.student for item in students]
        children_count = len(student_list)

        fee_summary = StudentFee.objects.filter(
            student__in=student_list
        ).aggregate(total_balance=Sum("balance"))

        total_fee_balance = fee_summary["total_balance"] or Decimal("0.00")

        attendance = Attendance.objects.filter(student__in=student_list)
        total = attendance.count()
        present = attendance.filter(status=Attendance.Status.PRESENT).count()

        overall_attendance = round((present / total) * 100, 2) if total > 0 else Decimal("0.00")

        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
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

        parent_students = (
            ParentStudent.objects
            .filter(parent=parent)
            .select_related(
                "student",
                "student__classroom",
                "student__classroom__class_teacher",
                "student__classroom__class_teacher__user",
            )
        )

        data = []

        for item in parent_students:
            student = item.student
            teacher = student.classroom.class_teacher if student.classroom else None

            attendance = Attendance.objects.filter(student=student)
            total = attendance.count()
            present = attendance.filter(status=Attendance.Status.PRESENT).count()
            attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

            fee_balance = (
                StudentFee.objects.filter(student=student)
                .aggregate(balance=Sum("balance"))["balance"] or 0
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
                "grade": student.classroom.grade,
                "stream": student.classroom.stream,
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

        parent_student = get_object_or_404(
            ParentStudent.objects.select_related(
                "student",
                "student__classroom",
                "student__classroom__class_teacher",
                "student__classroom__class_teacher__user",
            ),
            parent=parent,
            student_id=id,
        )

        student = parent_student.student
        teacher = student.classroom.class_teacher

        attendance = Attendance.objects.filter(student=student)
        total = attendance.count()
        present = attendance.filter(status=Attendance.Status.PRESENT).count()
        attendance_percentage = round((present / total) * 100, 2) if total else 0

        fee_balance = (
            StudentFee.objects.filter(student=student)
            .aggregate(balance=Sum("balance"))["balance"] or 0
        )

        latest_result = (
            StudentTermResult.objects.filter(student=student)
            .order_by("-id").first()
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
            "class_teacher": teacher.user.get_full_name() if teacher else None,
            "teacher_phone": teacher.user.phone_number if teacher else None,
            "relationship": parent_student.relationship,
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

        assignments = TeacherAssignment.objects.filter(
            teacher=teacher,
            is_active=True,
        )

        total_assignments = assignments.count()
        total_subjects = assignments.values("subject").distinct().count()
        total_classes = assignments.values("classroom").distinct().count()

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
            "total_assignments": total_assignments,
            "total_subjects": total_subjects,
            "total_classes": total_classes,
            "pending_results": pending_results,
        }

        return Response(data)


# ==========================================
# Teacher Students
# ==========================================

class TeacherStudentsAPIView(APIView):

    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):

        teacher = request.user.teacher_profile

        assignments = TeacherAssignment.objects.filter(
            teacher=teacher,
            is_active=True,
        )

        if is_class_teacher(request.user):
            classroom_ids = assignments.filter(
                is_class_teacher=True,
            ).values_list("classroom_id", flat=True)
        else:
            classroom_ids = assignments.values_list("classroom_id", flat=True)

        students = (
            Student.objects
            .filter(classroom_id__in=classroom_ids)
            .select_related("classroom")
            .distinct()
            .order_by("first_name", "last_name")
        )

        data = [
            {
                "id": student.id,
                "photo": student.photo,
                "admission_number": student.admission_number,
                "assessment_number": student.assessment_number,
                "student_name": f"{student.first_name} {student.last_name}",
                "classroom": f"{student.classroom.grade} {student.classroom.stream}",
                "gender": student.gender,
                "status": "Active",
            }
            for student in students
        ]

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
