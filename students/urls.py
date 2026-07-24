from django.urls import path

from .views import (
    StudentListView,
    StudentDetailView,
    StudentCreateView,
    StudentTransferDetailView,
    StudentTransferListView,
    StudentTransferView,
    StudentUpdateView,
    StudentDeleteView,
)

urlpatterns = [
    path("", StudentListView.as_view(), name="student-list"),
    path("<int:pk>/", StudentDetailView.as_view(), name="student-detail"),
    path("create/", StudentCreateView.as_view(), name="student-create"),
    path("update/<int:pk>/", StudentUpdateView.as_view(), name="student-update"),
    path("delete/<int:pk>/", StudentDeleteView.as_view(), name="student-delete"),
     
    # Student Transfers
    path("transfer/", StudentTransferView.as_view(),name="student-transfer",),
    path("transfers/", StudentTransferListView.as_view(),name="student-transfer-list",),
    path("transfers/<int:pk>/", StudentTransferDetailView.as_view(),name="student-transfer-detail",),
]