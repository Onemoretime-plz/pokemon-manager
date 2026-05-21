from django.urls import path

from . import views

app_name = "pokemane"

urlpatterns = [
    path("pokemon/", views.pokemon_list, name="pokemon_list"),
    path("sets/", views.set_list, name="set_list"),
    path("sets/new/", views.set_form, name="set_create"),
    path("sets/<int:set_id>/edit/", views.set_form, name="set_edit"),
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
    path("sets/<int:set_id>/delete/", views.set_delete, name="set_delete"),
    path("parties/<int:party_id>/delete/", views.party_delete, name="party_delete"),
    path("pokemon/new/", views.pokemon_form, name="pokemon_create"),
    path("pokemon/<int:pokemon_id>/edit/", views.pokemon_form, name="pokemon_edit"),
    path("pokemon/<int:pokemon_id>/delete/", views.pokemon_delete, name="pokemon_delete"),
    path(
    "api/parties/<int:party_id>/move-slot/",
    views.move_party_slot_api,
    name="move_party_slot_api",
    ),
]