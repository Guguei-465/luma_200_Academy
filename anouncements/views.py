from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
# 📌 Preserved your exact import spelling
from notifiations.models import Notification
from accounts.models import CustomUser

from .models import Announcement
from .serializers import AnnouncementSerializer
from .permissions import IsSuperAdminOrAcademicCoordinator


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()
    ordering = ["-created_at"]
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "message"]
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

        # Guard: skip empty list
        if recipients.exists():
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


    # ✅ ONLY ONE CLEAN RESEND ACTION — NO DUPLICATES!
    @action(detail=True, methods=["post"], url_path="resend")
    def resend(self, request, pk=None):
        try:
            announcement = self.get_object()

            # --- EXACT SAME recipient logic as perform_create ---
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

            created_count = 0
            if recipients.exists():
                notifications = [
                    Notification(
                        recipient=recipient,
                        triggered_by=request.user,
                        notification_type=Notification.NotificationType.ANNOUNCEMENT,
                        title=announcement.title,
                        message=announcement.message,
                    )
                    for recipient in recipients
                ]
                Notification.objects.bulk_create(notifications)
                created_count = len(notifications)

            return Response(
                {"detail": f"✅ Resent successfully! Sent to {created_count} recipients."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            print("❌ RESEND ERROR:", str(e))
            return Response(
                {"detail": f"Failed to resend: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )