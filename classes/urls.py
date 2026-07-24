from django.urls import path
from .views import (
    ClassRoomListView,
    ClassRoomDetailView,
    ClassRoomCreateView,
    ClassRoomUpdateView,
    ClassRoomDeleteView,
)

urlpatterns = [
    path("", ClassRoomListView.as_view(), name="classroom-list"),
    path("<int:pk>/", ClassRoomDetailView.as_view(), name="classroom-detail"),
    path("create/", ClassRoomCreateView.as_view(), name="classroom-create"),
    path("update/<int:pk>/", ClassRoomUpdateView.as_view(), name="classroom-update"),
    path("delete/<int:pk>/", ClassRoomDeleteView.as_view(), name="classroom-delete"),
]