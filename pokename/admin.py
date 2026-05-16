from django.contrib import admin

from .models import (
    Matchup,
    Party,
    Pokemon,
    PokemonSet,
    SetMove,
    WeakMatchup,
)


class SetMoveInline(admin.TabularInline):
    model = SetMove
    extra = 4
    max_num = 4


class MatchupInline(admin.TabularInline):
    model = Matchup
    extra = 1


class WeakMatchupInline(admin.TabularInline):
    model = WeakMatchup
    extra = 1


@admin.register(Pokemon)
class PokemonAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "type1",
        "type2",
        "base_hp",
        "base_attack",
        "base_defense",
        "base_sp_attack",
        "base_sp_defense",
        "base_speed",
        "is_virtual_target",
        "can_mega_evolve",
        "mega_evolution_pokemon",
    )
    list_filter = (
        "type1",
        "type2",
        "is_virtual_target",
        "can_mega_evolve",
    )
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(PokemonSet)
class PokemonSetAdmin(admin.ModelAdmin):
    list_display = (
        "pokemon",
        "set_name",
        "ability_name",
        "item_name",
        "nature_up",
        "nature_down",
        "updated_at",
    )
    list_filter = (
        "is_mega_stone",
        "nature_up",
        "nature_down",
    )
    search_fields = (
        "pokemon__name",
        "set_name",
        "ability_name",
        "custom_item_name",
    )
    inlines = [
        SetMoveInline,
        MatchupInline,
        WeakMatchupInline,
    ]


@admin.register(SetMove)
class SetMoveAdmin(admin.ModelAdmin):
    list_display = (
        "pokemon_set",
        "order",
        "move_name",
        "move_type",
        "move_category",
    )
    list_filter = (
        "move_type",
        "move_category",
    )
    search_fields = (
        "move_name",
        "pokemon_set__pokemon__name",
        "pokemon_set__set_name",
    )


@admin.register(Matchup)
class MatchupAdmin(admin.ModelAdmin):
    list_display = (
        "pokemon_set",
        "target_pokemon",
        "method",
    )
    list_filter = ("method",)
    search_fields = (
        "pokemon_set__pokemon__name",
        "target_pokemon__name",
    )


@admin.register(WeakMatchup)
class WeakMatchupAdmin(admin.ModelAdmin):
    list_display = (
        "pokemon_set",
        "target_pokemon",
    )
    search_fields = (
        "pokemon_set__pokemon__name",
        "target_pokemon__name",
    )


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slot1",
        "slot2",
        "slot3",
        "slot4",
        "slot5",
        "slot6",
        "updated_at",
    )
    search_fields = ("name", "memo")