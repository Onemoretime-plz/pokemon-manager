from django.urls import path

from . import views

app_name = "pokemane"

urlpatterns = [
    path("sets/", views.set_list, name="set_list"),
]