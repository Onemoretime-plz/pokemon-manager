import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .models import MegaEvolution, Matchup, Party, Pokemon, PokemonSet, SetMove, WeakMatchup
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


def build_set_card_data(pokemon_set, mega_active=True):
    """
    型一覧・パーティー詳細で表示しやすい形に変換する。
    メガストーン型の場合は、メガ前/メガ後の表示データも持たせる。
    """
    effective_pokemon = get_effective_pokemon(
        pokemon_set,
        mega_active=mega_active,
    )

    summary = build_stats_summary(
        pokemon_set,
        mega_active=mega_active,
    )
    stats = summary["actual_stats"]

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

    base_summary = build_stats_summary(
        pokemon_set,
        mega_active=False,
    )
    base_pokemon = get_effective_pokemon(
        pokemon_set,
        mega_active=False,
    )

    mega_pokemon = get_effective_pokemon(
        pokemon_set,
        mega_active=True,
    )
    mega_summary = build_stats_summary(
        pokemon_set,
        mega_active=True,
    )

    return {
        "set": pokemon_set,
        "pokemon": effective_pokemon,
        "original_pokemon": pokemon_set.pokemon,
        "is_mega_active": mega_active and pokemon_set.is_mega_stone and pokemon_set.selected_mega_evolution is not None,
        "type1_class": get_type_class(effective_pokemon.type1),
        "type2_class": get_type_class(effective_pokemon.type2) if effective_pokemon.type2 else "",
        "stats": stats,
        "physical_bulk": summary["physical_bulk"],
        "special_bulk": summary["special_bulk"],
        "overall_bulk": summary["overall_bulk"],
        "speed_for_sort": summary["speed_for_sort"],
        "moves": moves,

        # メガ切替表示用
        "base_display": {
            "name": base_pokemon.name,
            "icon_url": base_pokemon.icon_image.url if base_pokemon.icon_image else "",
            "type1": base_pokemon.type1,
            "type2": base_pokemon.type2 or "",
            "type1_class": get_type_class(base_pokemon.type1),
            "type2_class": get_type_class(base_pokemon.type2) if base_pokemon.type2 else "",
            "ability": pokemon_set.ability_name,
            "stats": base_summary["actual_stats"],
        },
        "mega_display": {
            "name": mega_pokemon.name,
            "icon_url": mega_pokemon.icon_image.url if mega_pokemon.icon_image else "",
            "type1": mega_pokemon.type1,
            "type2": mega_pokemon.type2 or "",
            "type1_class": get_type_class(mega_pokemon.type1),
            "type2_class": get_type_class(mega_pokemon.type2) if mega_pokemon.type2 else "",
            "ability": mega_pokemon.ability1 or pokemon_set.ability_name,
            "stats": mega_summary["actual_stats"],
        },
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

    if request.method == "POST":
        party.name = request.POST.get("name", "").strip() or party.name
        party.memo = request.POST.get("memo", "").strip()
        party.save(update_fields=["name", "memo", "updated_at"])

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

    available_sets = (
        PokemonSet.objects
        .select_related(
            "pokemon",
            "selected_mega_evolution",
            "selected_mega_evolution__mega_pokemon",
        )
        .order_by("pokemon__national_dex_no", "pokemon__name", "set_name")
    )

    context = {
        "party": party,
        "slot_cards": slot_cards,
        "diagnosis": diagnosis,
        "available_sets": available_sets,
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

@require_POST
def set_party_slot_api(request, party_id):
    """
    パーティースロットに型を登録するAPI。

    受け取るJSON例：
    {
        "slot_number": 1,
        "set_id": 5
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
    set_id = payload.get("set_id")

    if slot_number not in [1, 2, 3, 4, 5, 6]:
        return JsonResponse(
            {"error": "Invalid slot_number"},
            status=400,
        )

    if not set_id:
        return JsonResponse(
            {"error": "set_id is required"},
            status=400,
        )

    party = get_object_or_404(Party, id=party_id)
    pokemon_set = get_object_or_404(PokemonSet, id=set_id)

    slot_field = f"slot{slot_number}"
    setattr(party, slot_field, pokemon_set)
    party.save(update_fields=[slot_field, "updated_at"])

    return JsonResponse(
        {
            "success": True,
            "slot_number": slot_number,
            "set_id": pokemon_set.id,
        }
    )

def get_type_choices_for_template():
    return [
        "ノーマル",
        "ほのお",
        "みず",
        "でんき",
        "くさ",
        "こおり",
        "かくとう",
        "どく",
        "じめん",
        "ひこう",
        "エスパー",
        "むし",
        "いわ",
        "ゴースト",
        "ドラゴン",
        "あく",
        "はがね",
        "フェアリー",
    ]


def get_nature_stat_choices_for_template():
    return [
        ("none", "なし"),
        ("attack", "攻撃"),
        ("defense", "防御"),
        ("sp_attack", "特攻"),
        ("sp_defense", "特防"),
        ("speed", "素早さ"),
    ]


def get_move_category_choices_for_template():
    return [
        ("attack", "攻撃技"),
        ("status", "変化技"),
    ]

def get_matchup_method_choices_for_template():
    return [
        ("switch_in", "後出し可"),
        ("face_to_face", "対面処理"),
        ("outspeed", "上から処理"),
        ("chip_required", "削り前提"),
        ("unstable", "やや不安定"),
    ]

def build_move_form_rows(pokemon_set=None):
    """
    技1〜4の入力欄用データを作る。
    """
    existing_moves = []

    if pokemon_set:
        existing_moves = list(pokemon_set.moves.all())

    rows = []

    for index in range(4):
        move = existing_moves[index] if index < len(existing_moves) else None

        rows.append(
            {
                "number": index + 1,
                "move_name": move.move_name if move else "",
                "move_type": move.move_type if move else "ノーマル",
                "move_category": move.move_category if move else "attack",
            }
        )

    return rows

def set_form(request, set_id=None):
    """
    型の新規登録・編集画面。

    まずは基本情報と技4つまで対応する。
    役割対象・苦手対象は次工程で追加する。
    """
    if set_id:
        pokemon_set = get_object_or_404(
            PokemonSet.objects.select_related(
                "pokemon",
                "selected_mega_evolution",
            ).prefetch_related("moves"),
            id=set_id,
        )
        page_title = "型編集"
    else:
        pokemon_set = None
        page_title = "型登録"

    pokemons = Pokemon.objects.order_by("national_dex_no", "name")
    mega_evolutions = MegaEvolution.objects.select_related(
        "base_pokemon",
        "mega_pokemon",
    ).order_by("base_pokemon__national_dex_no", "base_pokemon__name")

    if request.method == "POST":
        pokemon_id = request.POST.get("pokemon")
        pokemon = get_object_or_404(Pokemon, id=pokemon_id)

        is_mega_stone = request.POST.get("is_mega_stone") == "on"
        selected_mega_evolution = None

        selected_mega_evolution_id = request.POST.get("selected_mega_evolution")

        if is_mega_stone and selected_mega_evolution_id:
            selected_mega_evolution = get_object_or_404(
                MegaEvolution,
                id=selected_mega_evolution_id,
            )

        if pokemon_set is None:
            pokemon_set = PokemonSet()

        pokemon_set.pokemon = pokemon
        pokemon_set.set_name = request.POST.get("set_name", "").strip()
        pokemon_set.ability_name = request.POST.get("ability_name", "").strip()
        pokemon_set.is_mega_stone = is_mega_stone
        pokemon_set.selected_mega_evolution = selected_mega_evolution
        pokemon_set.custom_item_name = request.POST.get("custom_item_name", "").strip()

        pokemon_set.nature_up = request.POST.get("nature_up", "none")
        pokemon_set.nature_down = request.POST.get("nature_down", "none")

        pokemon_set.point_hp = int(request.POST.get("point_hp") or 0)
        pokemon_set.point_attack = int(request.POST.get("point_attack") or 0)
        pokemon_set.point_defense = int(request.POST.get("point_defense") or 0)
        pokemon_set.point_sp_attack = int(request.POST.get("point_sp_attack") or 0)
        pokemon_set.point_sp_defense = int(request.POST.get("point_sp_defense") or 0)
        pokemon_set.point_speed = int(request.POST.get("point_speed") or 0)

        pokemon_set.memo = request.POST.get("memo", "").strip()

        pokemon_set.full_clean()
        pokemon_set.save()

        # いったん既存技を削除して、4枠を再作成する。
        pokemon_set.moves.all().delete()

        for number in range(1, 5):
            move_name = request.POST.get(f"move_name_{number}", "").strip()
            move_type = request.POST.get(f"move_type_{number}", "").strip()
            move_category = request.POST.get(f"move_category_{number}", "attack")

            if not move_name:
                continue

            SetMove.objects.create(
                pokemon_set=pokemon_set,
                move_name=move_name,
                move_type=move_type,
                move_category=move_category,
            )


                # 役割対象を再作成する。
        pokemon_set.matchups.all().delete()

        matchup_count = int(request.POST.get("matchup_count") or 0)

        for number in range(1, matchup_count + 1):
            target_pokemon_id = request.POST.get(f"matchup_target_{number}", "")
            method = request.POST.get(f"matchup_method_{number}", "face_to_face")
            memo = request.POST.get(f"matchup_memo_{number}", "").strip()

            if not target_pokemon_id:
                continue

            target_pokemon = get_object_or_404(Pokemon, id=target_pokemon_id)

            Matchup.objects.create(
                pokemon_set=pokemon_set,
                target_pokemon=target_pokemon,
                method=method,
                memo=memo,
            )
            method = request.POST.get(f"matchup_method_{number}", "face_to_face")
            memo = request.POST.get(f"matchup_memo_{number}", "").strip()

            if not target_pokemon_id:
                continue

            target_pokemon = get_object_or_404(Pokemon, id=target_pokemon_id)

            Matchup.objects.create(
                pokemon_set=pokemon_set,
                target_pokemon=target_pokemon,
                method=method,
                memo=memo,
            )

        # 苦手対象を再作成する。
        pokemon_set.weak_matchups.all().delete()

        weak_matchup_count = int(request.POST.get("weak_matchup_count") or 0)

        for number in range(1, weak_matchup_count + 1):
            target_pokemon_id = request.POST.get(f"weak_target_{number}", "")
            memo = request.POST.get(f"weak_memo_{number}", "").strip()

            if not target_pokemon_id:
                continue

            target_pokemon = get_object_or_404(Pokemon, id=target_pokemon_id)

            WeakMatchup.objects.create(
                pokemon_set=pokemon_set,
                target_pokemon=target_pokemon,
                memo=memo,
            )
            memo = request.POST.get(f"weak_memo_{number}", "").strip()

            if not target_pokemon_id:
                continue

            target_pokemon = get_object_or_404(Pokemon, id=target_pokemon_id)

            WeakMatchup.objects.create(
                pokemon_set=pokemon_set,
                target_pokemon=target_pokemon,
                memo=memo,
            )



        return redirect("pokemane:set_list")

    pokemon_ability_map = {}
    pokemon_mega_map = {}
    pokemon_icon_map = {}
    pokemon_stats_map = {}

    for pokemon in pokemons:
        pokemon_stats_map[str(pokemon.id)] = {
            "hp": pokemon.base_hp,
            "attack": pokemon.base_attack,
            "defense": pokemon.base_defense,
            "sp_attack": pokemon.base_sp_attack,
            "sp_defense": pokemon.base_sp_defense,
            "speed": pokemon.base_speed,
        }

    for pokemon in pokemons:
        pokemon_icon_map[str(pokemon.id)] = {
            "name": pokemon.name,
            "icon_url": pokemon.icon_image.url if pokemon.icon_image else "",
        }

    for pokemon in pokemons:
        abilities = pokemon.ability_options()

        pokemon_ability_map[str(pokemon.id)] = abilities

    for mega in mega_evolutions:
        base_id = str(mega.base_pokemon_id)

        if base_id not in pokemon_mega_map:
            pokemon_mega_map[base_id] = []

        pokemon_mega_map[base_id].append(
            {
                "id": mega.id,
                "label": f"{mega.mega_pokemon.name}"
                + (f"（{mega.form_name}）" if mega.form_name else ""),
            }
        )

    context = {
        "page_title": page_title,
        "pokemon_set": pokemon_set,
        "pokemons": pokemons,
        "mega_evolutions": mega_evolutions,
        "type_choices": get_type_choices_for_template(),
        "nature_stat_choices": get_nature_stat_choices_for_template(),
        "move_category_choices": get_move_category_choices_for_template(),
        "move_rows": build_move_form_rows(pokemon_set),
        "pokemon_ability_map_json": json.dumps(pokemon_ability_map, ensure_ascii=False),
        "pokemon_mega_map_json": json.dumps(pokemon_mega_map, ensure_ascii=False),
        "matchup_method_choices": get_matchup_method_choices_for_template(),
        "matchup_rows": build_matchup_form_rows(pokemon_set),
        "weak_matchup_rows": build_weak_matchup_form_rows(pokemon_set),
        "pokemon_icon_map_json": json.dumps(pokemon_icon_map, ensure_ascii=False),
        "pokemon_stats_map_json": json.dumps(pokemon_stats_map, ensure_ascii=False),

    }

    return render(request, "pokemane/set_form.html", context)

def build_matchup_form_rows(pokemon_set=None):
    existing_matchups = []

    if pokemon_set:
        existing_matchups = list(
            pokemon_set.matchups.select_related("target_pokemon").all()
        )

    rows = []

    for index, matchup in enumerate(existing_matchups, start=1):
        rows.append(
            {
                "number": index,
                "target_pokemon_id": matchup.target_pokemon_id,
                "method": matchup.method,
                "memo": matchup.memo,
            }
        )

    if not rows:
        rows.append(
            {
                "number": 1,
                "target_pokemon_id": "",
                "method": "face_to_face",
                "memo": "",
            }
        )

    return rows


def build_weak_matchup_form_rows(pokemon_set=None):
    existing_weak_matchups = []

    if pokemon_set:
        existing_weak_matchups = list(
            pokemon_set.weak_matchups.select_related("target_pokemon").all()
        )

    rows = []

    for index, weak_matchup in enumerate(existing_weak_matchups, start=1):
        rows.append(
            {
                "number": index,
                "target_pokemon_id": weak_matchup.target_pokemon_id,
                "memo": weak_matchup.memo,
            }
        )

    if not rows:
        rows.append(
            {
                "number": 1,
                "target_pokemon_id": "",
                "memo": "",
            }
        )

    return rows

@require_POST
def set_delete(request, set_id):
    pokemon_set = get_object_or_404(PokemonSet, id=set_id)
    pokemon_set.delete()

    return redirect("pokemane:set_list")

@require_POST
def party_delete(request, party_id):
    party = get_object_or_404(Party, id=party_id)
    party.delete()

    return redirect("pokemane:party_list")