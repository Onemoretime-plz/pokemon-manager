import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render

from .models import Party, Pokemon, PokemonSet
from .services.diagnosis import diagnose_party, diagnose_slots
from .services.stats import build_stats_summary, get_effective_pokemon
from .services.type_styles import get_type_class



SORT_LABELS = {
    "pokemon_name": "ポケモン名順",
    "speed_desc": "素早さ実数値降順",
    "speed_asc": "素早さ実数値昇順",
    "attack_desc": "こうげき実数値降順",
    "sp_attack_desc": "とくこう実数値降順",
    "physical_bulk_desc": "物理耐久指数降順",
    "special_bulk_desc": "特殊耐久指数降順",
    "overall_bulk_desc": "総合耐久指数降順",
}


def build_set_card_data(pokemon_set):
    """
    型一覧画面で表示・並べ替えしやすい形に変換する。
    """
    summary = build_stats_summary(pokemon_set, mega_active=True)
    stats = summary["actual_stats"]

    effective_pokemon = get_effective_pokemon(pokemon_set, mega_active=True)

    moves = []
    for move in pokemon_set.moves.all():
        if not move.move_name:
            continue

        moves.append(
            {
                "name": move.move_name,
                "type": move.move_type,
                "category": move.move_category,
                "type_class": get_type_class(move.move_type),
            }
        )

    return {
        "set": pokemon_set,
        "pokemon": effective_pokemon,
        "original_pokemon": pokemon_set.pokemon,
        "is_mega_active": pokemon_set.is_mega_stone and pokemon_set.selected_mega_evolution is not None,
        "type1_class": get_type_class(effective_pokemon.type1),
        "type2_class": get_type_class(effective_pokemon.type2) if effective_pokemon.type2 else "",
        "stats": stats,
        "physical_bulk": summary["physical_bulk"],
        "special_bulk": summary["special_bulk"],
        "overall_bulk": summary["overall_bulk"],
        "speed_for_sort": summary["speed_for_sort"],
        "moves": moves,
    }


def set_list(request):
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "pokemon_name")

    pokemon_sets = (
        PokemonSet.objects
        .select_related(
            "pokemon",
            "selected_mega_evolution",
            "selected_mega_evolution__mega_pokemon",
        )
        .prefetch_related("moves")
    )

    if query:
        pokemon_sets = pokemon_sets.filter(
            pokemon__name__icontains=query
        ) | pokemon_sets.filter(
            set_name__icontains=query
        ) | pokemon_sets.filter(
            ability_name__icontains=query
        ) | pokemon_sets.filter(
            custom_item_name__icontains=query
        )

    cards = [build_set_card_data(pokemon_set) for pokemon_set in pokemon_sets]

    if sort == "speed_desc":
        cards.sort(key=lambda card: card["speed_for_sort"], reverse=True)
    elif sort == "speed_asc":
        cards.sort(key=lambda card: card["speed_for_sort"])
    elif sort == "attack_desc":
        cards.sort(key=lambda card: card["stats"]["attack"], reverse=True)
    elif sort == "sp_attack_desc":
        cards.sort(key=lambda card: card["stats"]["sp_attack"], reverse=True)
    elif sort == "physical_bulk_desc":
        cards.sort(key=lambda card: card["physical_bulk"], reverse=True)
    elif sort == "special_bulk_desc":
        cards.sort(key=lambda card: card["special_bulk"], reverse=True)
    elif sort == "overall_bulk_desc":
        cards.sort(key=lambda card: card["overall_bulk"], reverse=True)
    else:
        sort = "pokemon_name"
        cards.sort(key=lambda card: card["pokemon"].name)

    context = {
        "cards": cards,
        "query": query,
        "sort": sort,
        "sort_label": SORT_LABELS.get(sort, "ポケモン名順"),
        "sort_labels": SORT_LABELS,
    }

    return render(request, "pokemane/set_list.html", context)

POKEMON_SORT_LABELS = {
    "dex_no": "図鑑No順",
    "name": "名前順",
    "hp_desc": "HP降順",
    "hp_asc": "HP昇順",
    "attack_desc": "こうげき降順",
    "attack_asc": "こうげき昇順",
    "defense_desc": "ぼうぎょ降順",
    "defense_asc": "ぼうぎょ昇順",
    "sp_attack_desc": "とくこう降順",
    "sp_attack_asc": "とくこう昇順",
    "sp_defense_desc": "とくぼう降順",
    "sp_defense_asc": "とくぼう昇順",
    "speed_desc": "すばやさ降順",
    "speed_asc": "すばやさ昇順",
}


def build_pokemon_card_data(pokemon):
    return {
        "pokemon": pokemon,
        "type1_class": get_type_class(pokemon.type1),
        "type2_class": get_type_class(pokemon.type2) if pokemon.type2 else "",
    }


def pokemon_list(request):
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "dex_no")

    pokemons = Pokemon.objects.select_related(
        "mega_evolution_pokemon",
        "pre_mega_pokemon",
    )

    if query:
        pokemons = pokemons.filter(name__icontains=query)

    sort_map = {
        "dex_no": "national_dex_no",
        "name": "name",
        "hp_desc": "-base_hp",
        "hp_asc": "base_hp",
        "attack_desc": "-base_attack",
        "attack_asc": "base_attack",
        "defense_desc": "-base_defense",
        "defense_asc": "base_defense",
        "sp_attack_desc": "-base_sp_attack",
        "sp_attack_asc": "base_sp_attack",
        "sp_defense_desc": "-base_sp_defense",
        "sp_defense_asc": "base_sp_defense",
        "speed_desc": "-base_speed",
        "speed_asc": "base_speed",
    }
    order_by = sort_map.get(sort, "national_dex_no")
    pokemons = pokemons.order_by(order_by, "name")

    cards = [build_pokemon_card_data(pokemon) for pokemon in pokemons]

    context = {
        "cards": cards,
        "query": query,
        "sort": sort,
        "sort_label": POKEMON_SORT_LABELS.get(sort, "図鑑No順"),
        "sort_labels": POKEMON_SORT_LABELS,
    }

    return render(request, "pokemane/pokemon_list.html", context)

def build_party_card_data(party):
    slots = []

    for pokemon_set in party.slots():
        if pokemon_set is None:
            slots.append(None)
            continue

        effective_pokemon = get_effective_pokemon(pokemon_set, mega_active=True)

        slots.append(
            {
                "set": pokemon_set,
                "pokemon": effective_pokemon,
                "is_mega": pokemon_set.is_mega_stone,
            }
        )

    return {
        "party": party,
        "slots": slots,
    }


def party_list(request):
    query = request.GET.get("q", "").strip()

    parties = (
        Party.objects
        .select_related(
            "slot1__pokemon",
            "slot1__pokemon__mega_evolution_pokemon",
            "slot2__pokemon",
            "slot2__pokemon__mega_evolution_pokemon",
            "slot3__pokemon",
            "slot3__pokemon__mega_evolution_pokemon",
            "slot4__pokemon",
            "slot4__pokemon__mega_evolution_pokemon",
            "slot5__pokemon",
            "slot5__pokemon__mega_evolution_pokemon",
            "slot6__pokemon",
            "slot6__pokemon__mega_evolution_pokemon",
        )
        .order_by("-updated_at")
    )

    if query:
        parties = parties.filter(name__icontains=query)

    cards = [build_party_card_data(party) for party in parties]

    context = {
        "cards": cards,
        "query": query,
    }

    return render(request, "pokemane/party_list.html", context)

def party_detail(request, party_id):
    party = get_object_or_404(
        Party.objects.select_related(
            "slot1__pokemon",
            "slot1__selected_mega_evolution",
            "slot1__selected_mega_evolution__mega_pokemon",
            "slot2__pokemon",
            "slot2__selected_mega_evolution",
            "slot2__selected_mega_evolution__mega_pokemon",
            "slot3__pokemon",
            "slot3__selected_mega_evolution",
            "slot3__selected_mega_evolution__mega_pokemon",
            "slot4__pokemon",
            "slot4__selected_mega_evolution",
            "slot4__selected_mega_evolution__mega_pokemon",
            "slot5__pokemon",
            "slot5__selected_mega_evolution",
            "slot5__selected_mega_evolution__mega_pokemon",
            "slot6__pokemon",
            "slot6__selected_mega_evolution",
            "slot6__selected_mega_evolution__mega_pokemon",
        ),
        id=party_id,
    )

    slot_cards = []

    for index, pokemon_set in enumerate(party.slots(), start=1):
        if pokemon_set is None:
            slot_cards.append(
                {
                    "slot_number": index,
                    "is_empty": True,
                    "card": None,
                }
            )
            continue

        slot_cards.append(
            {
                "slot_number": index,
                "is_empty": False,
                "card": build_set_card_data(pokemon_set),
            }
        )

    diagnosis = diagnose_party(party)

    context = {
        "party": party,
        "slot_cards": slot_cards,
        "diagnosis": diagnosis,
    }

    return render(request, "pokemane/party_detail.html", context)

@require_POST
def diagnosis_slots_api(request):
    """
    JavaScript fetch用の診断API。

    受け取るJSON例：
    {
        "slots": [
            {"set_id": 1, "mega_active": true},
            {"set_id": 2, "mega_active": false}
        ]
    }

    返却：
    {
        "html": "<div>...</div>"
    }
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400,
        )

    slots = payload.get("slots", [])

    diagnosis = diagnose_slots(slots)

    html = render_to_string(
        "pokemane/partials/diagnosis_result.html",
        {
            "diagnosis": diagnosis,
        },
        request=request,
    )

    return JsonResponse(
        {
            "html": html,
        }
    )


@require_POST
def clear_party_slot_api(request, party_id):
    """
    パーティースロットを空にするAPI。

    受け取るJSON例：
    {
        "slot_number": 1
    }
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400,
        )

    slot_number = payload.get("slot_number")

    if slot_number not in [1, 2, 3, 4, 5, 6]:
        return JsonResponse(
            {"error": "Invalid slot_number"},
            status=400,
        )

    party = get_object_or_404(Party, id=party_id)

    slot_field = f"slot{slot_number}"
    setattr(party, slot_field, None)
    party.save(update_fields=[slot_field, "updated_at"])

    return JsonResponse(
        {
            "success": True,
            "slot_number": slot_number,
        }
    )