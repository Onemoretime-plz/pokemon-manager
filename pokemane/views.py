from django.shortcuts import render

from .models import Pokemon, PokemonSet
from .services.stats import build_stats_summary
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

    effective_pokemon = pokemon_set.pokemon
    if pokemon_set.is_mega_stone and pokemon_set.pokemon.mega_evolution_pokemon:
        effective_pokemon = pokemon_set.pokemon.mega_evolution_pokemon

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
        "is_mega_active": pokemon_set.is_mega_stone and pokemon_set.pokemon.mega_evolution_pokemon is not None,
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
        .select_related("pokemon", "pokemon__mega_evolution_pokemon")
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
    sort = request.GET.get("sort", "name")

    pokemons = Pokemon.objects.select_related(
        "mega_evolution_pokemon",
        "pre_mega_pokemon",
    )

    if query:
        pokemons = pokemons.filter(name__icontains=query)

    sort_map = {
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

    order_by = sort_map.get(sort, "name")
    pokemons = pokemons.order_by(order_by, "name")

    cards = [build_pokemon_card_data(pokemon) for pokemon in pokemons]

    context = {
        "cards": cards,
        "query": query,
        "sort": sort,
        "sort_label": POKEMON_SORT_LABELS.get(sort, "名前順"),
        "sort_labels": POKEMON_SORT_LABELS,
    }

    return render(request, "pokemane/pokemon_list.html", context)