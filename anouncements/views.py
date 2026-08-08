from django.db.models import Q
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
# 📌 DO NOT CHANGE — kept your exact import name
from notifiations.models import Notification
from accounts.models import CustomUser

from .models import Announcement
from .serializers import AnnouncementSerializer
from .permissions import IsSuperAdminOrAcademicCoordinator


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()  # Explicit queryset added
    ordering = ["-created_at"]  # Newest announcements first
    pagination_class = PageNumberPagination  # Prevent huge list loads
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "message"]  # Enable search by title/message
    ordering_fields = ["created_at", "priority"]

    def get_queryset(self):
        user = self.request.user

        if user.role == CustomUser.Role.PARENT:
            return super().get_queryset().filter(
                is_active=True
            ).filter(
                Q(target=Announcement.Target.ALL_USERS) |
                Q(target=Announcement.Target.PARENTS)
            )

        elif user.role == CustomUser.Role.TEACHER:
            return super().get_queryset().filter(
                is_active=True
            ).filter(
                Q(target=Announcement.Target.ALL_USERS) |
                Q(target=Announcement.Target.STAFF) |
                Q(target=Announcement.Target.TEACHERS)
            )

        # All other staff/accountant/admin
        return super().get_queryset().filter(
            is_active=True
        ).filter(
            Q(target=Announcement.Target.ALL_USERS) |
            Q(target=Announcement.Target.STAFF)
        )

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsSuperAdminOrAcademicCoordinator]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # Save announcement with creator
        announcement = serializer.save(created_by=self.request.user)

        # Resolve correct recipients
        if announcement.target == Announcement.Target.ALL_USERS:
            recipients = CustomUser.objects.filter(is_active=True)
        elif announcement.target == Announcement.Target.PARENTS:
            recipients = CustomUser.objects.filter(role=CustomUser.Role.PARENT, is_active=True)
        elif announcement.target == Announcement.Target.TEACHERS:
            recipients = CustomUser.objects.filter(role=CustomUser.Role.TEACHER, is_active=True)
        elif announcement.target == Announcement.Target.STAFF:
            recipients = CustomUser.objects.filter(
                role__in=[
                    CustomUser.Role.SUPER_ADMIN,
                    CustomUser.Role.ACADEMIC_COORDINATOR,
                    CustomUser.Role.ACCOUNTANT,
                    CustomUser.Role.TEACHER,
                ],
                is_active=True
            )
        else:
            recipients = CustomUser.objects.none()

        # Fixed loop variable bug — assign to correct recipient
        if recipients.exists():  # Guard: skip empty list
            notifications = [
                Notification(
                    recipient=recipient,
                    triggered_by=self.request.user,
                    notification_type=Notification.NotificationType.ANNOUNCEMENT,
                    title=announcement.title,
                    message=announcement.message,
                )
                for recipient in recipients
            ]
            Notification.objects.bulk_create(notifications)


    # ✅ ADD THIS: creates /<pk>/resend/ POST route
    @action(detail=True, methods=["post"], url_path="resend")
    def resend(self, request, pk=None):
        announcement = self.get_object()
        # Re-run your existing notification bulk-create logic here
        recipients = self.get_recipients_for_target(announcement.target) # reuse your target logic
        if recipients.exists():
            notifications = [
                Notification(
                    recipient=recipient,
                    triggered_by=request.user,
                    notification_type=Notification.NotificationType.ANNOUNCEMENT,
                    title=announcement.title,
                    message=announcement.message
                )
                for recipient in recipients
            ]
            Notification.objects.bulk_create(notifications)
        return Response({"detail": "✅ Resent successfully"})
