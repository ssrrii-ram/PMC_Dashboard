from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard, name="home"),
    path("data-entry/", views.data_entry, name="data_entry"),
    path("data-entry/edit/<str:model_name>/<int:pk>/", views.edit_entry, name="edit_entry"),
    path("data-entry/delete/<str:model_name>/<int:pk>/", views.delete_entry, name="delete_entry"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_user, name="logout"),
    path("profile/", views.profile, name="profile"),
]
