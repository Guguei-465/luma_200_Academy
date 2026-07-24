from rest_framework import serializers



class TopStudentSerializer(serializers.Serializer):

    position = serializers.IntegerField()

    photo = serializers.ImageField(
        allow_null=True,
    )

    assessment_number = serializers.CharField()

    admission_number = serializers.CharField()

    student_name = serializers.CharField()

    classroom = serializers.CharField()

    average_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    grade = serializers.CharField()


class DashboardSerializer(serializers.Serializer):
    # Students
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    boys = serializers.IntegerField()
    girls = serializers.IntegerField()

    # Teachers
    total_teachers = serializers.IntegerField()

    # Classes
    total_classes = serializers.IntegerField()

    # Subjects
    total_subjects = serializers.IntegerField()

    # Parents
    total_parents = serializers.IntegerField()

    # Attendance
    attendance_today = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    # Fees
    total_fee = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    total_paid = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    total_balance = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    # Exams
    total_exams = serializers.IntegerField()

    # Results
    total_results = serializers.IntegerField()

    # Notifications
    unread_notifications = serializers.IntegerField()

class TopClassSerializer(serializers.Serializer):

    position = serializers.IntegerField()

    classroom = serializers.CharField()

    average_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    total_students = serializers.IntegerField()


class RecentPaymentSerializer(serializers.Serializer):

    receipt_number = serializers.CharField()

    student_name = serializers.CharField()

    admission_number = serializers.CharField()

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    payment_method = serializers.CharField()

    payment_date = serializers.DateField()

    payment_status = serializers.CharField()

class RecentAdmissionSerializer(serializers.Serializer):

    photo = serializers.ImageField(
        allow_null=True,
    )

    admission_number = serializers.CharField()

    assessment_number = serializers.CharField(
        allow_null=True,
    )

    student_name = serializers.CharField()

    classroom = serializers.CharField()

    date_admitted = serializers.DateField()


class AttendanceSummarySerializer(serializers.Serializer):

    present = serializers.IntegerField()

    absent = serializers.IntegerField()

    excused = serializers.IntegerField()

    total = serializers.IntegerField()

    attendance_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )


class DashboardFeeSummarySerializer(serializers.Serializer):

    expected_fee = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    collected_fee = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    outstanding_fee = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    collection_percentage = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    total_transactions = serializers.IntegerField()


class ExamPerformanceSerializer(serializers.Serializer):

    total_exams = serializers.IntegerField()

    published_results = serializers.IntegerField()

    pending_results = serializers.IntegerField()

    overall_average = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    highest_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    lowest_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )


class UpcomingNotificationSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    title = serializers.CharField()

    message = serializers.CharField()

    priority = serializers.CharField()

    target = serializers.CharField()

    created_at = serializers.DateTimeField()

    created_by = serializers.CharField()





