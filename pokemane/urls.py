from django.urls import path

from . import views

app_name = "pokemane"

urlpatterns = [
    path("pokemon/", views.pokemon_list, name="pokemon_list"),
    path("sets/", views.set_list, name="set_list"),
    path("parties/", views.party_list, name="party_list"),
    path("parties/<int:party_id>/", views.party_detail, name="party_detail"),
    path("api/diagnosis/", views.diagnosis_slots_api, name="diagnosis_slots_api"),
    path(
        "api/parties/<int:party_id>/clear-slot/",
        views.clear_party_slot_api,
        name="clear_party_slot_api",
    ),
    path(
        "api/parties/<int:party_id>/set-slot/",
        views.set_party_slot_api,
        name="set_party_slot_api",
    ),
]