from django.urls import path

from . import views

app_name = "pokemane"

urlpatterns = [
    path("pokemon/", views.pokemon_list, name="pokemon_list"),
    path("sets/", views.set_list, name="set_list"),
    path("parties/", views.party_list, name="party_list"),
]