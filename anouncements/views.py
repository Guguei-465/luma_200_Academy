from django.db.models import Q

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from notifiations.models import Notification
from accounts.models import CustomUser

from .models import Announcement
from .serializers import AnnouncementSerializer
from .permissions import IsSuperAdminOrAcademicCoordinator


class AnnouncementViewSet(viewsets.ModelViewSet):

    serializer_class = AnnouncementSerializer


    def get_queryset(self):

        user = self.request.user

        if user.role == CustomUser.Role.PARENT:
            return Announcement.objects.filter(
                is_active=True
            ).filter(
                Q(target=Announcement.Target.ALL_USERS) |
                Q(target=Announcement.Target.PARENTS)
            )


        elif user.role == CustomUser.Role.TEACHER:
            return Announcement.objects.filter(
                is_active=True
            ).filter(
                Q(target=Announcement.Target.ALL_USERS) |
                Q(target=Announcement.Target.STAFF) |
                Q(target=Announcement.Target.TEACHERS)
            )


        return Announcement.objects.filter(
            is_active=True
        ).filter(
            Q(target=Announcement.Target.ALL_USERS) |
            Q(target=Announcement.Target.STAFF)
        )


    def get_permissions(self):

        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [
                IsSuperAdminOrAcademicCoordinator,
            ]

        else:
            permission_classes = [
                IsAuthenticated,
            ]

        return [
            permission()
            for permission in permission_classes
        ]


    def perform_create(self, serializer):

        announcement = serializer.save(
            created_by=self.request.user
        )


        if announcement.target == Announcement.Target.ALL_USERS:

            recipients = CustomUser.objects.filter(
                is_active=True
            )


        elif announcement.target == Announcement.Target.PARENTS:

            recipients = CustomUser.objects.filter(
                role=CustomUser.Role.PARENT,
                is_active=True
            )


        elif announcement.target == Announcement.Target.TEACHERS:

            recipients = CustomUser.objects.filter(
                role=CustomUser.Role.TEACHER,
                is_active=True
            )


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


        notifications = [
            Notification(
                recipient=user,
                triggered_by=self.request.user,
                notification_type=Notification.NotificationType.ANNOUNCEMENT,
                title=announcement.title,
                message=announcement.message,
            )
            for user in recipients
        ]


        Notification.objects.bulk_create(
            notifications
        )