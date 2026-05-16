from collections import defaultdict

from pokemane.models import Pokemon, PokemonSet
from pokemane.services.stats import get_effective_pokemon
from pokemane.services.type_matchups import (
    TYPE_NAMES,
    calculate_defensive_multiplier,
)
from pokemane.services.type_styles import get_type_class


MATCHUP_METHOD_ORDER = [
    "switch_in",
    "face_to_face",
    "outspeed",
    "chip_required",
    "unstable",
]


MATCHUP_METHOD_LABELS = {
    "switch_in": "後出し可",
    "face_to_face": "対面処理",
    "outspeed": "上から処理",
    "chip_required": "削り前提",
    "unstable": "やや不安定",
}


def get_party_sets_from_slots(slots):
    """
    slots から PokemonSet のリストを作る。

    slots の想定：
    [
        {"set_id": 1, "mega_active": true},
        {"set_id": 2, "mega_active": false},
    ]

    ただし、初期実装では party.slots() から作る通常表示にも使うため、
    None は除外する。
    """
    set_ids = []

    for slot in slots:
        if not slot:
            continue

        set_id = slot.get("set_id")
        if set_id:
            set_ids.append(set_id)

    pokemon_sets = (
        PokemonSet.objects
        .filter(id__in=set_ids)
        .select_related(
            "pokemon",
            "selected_mega_evolution",
            "selected_mega_evolution__mega_pokemon",
        )
        .prefetch_related(
            "matchups__target_pokemon",
            "weak_matchups__target_pokemon",
        )
    )

    pokemon_set_map = {
        pokemon_set.id: pokemon_set
        for pokemon_set in pokemon_sets
    }

    ordered_sets = []

    for slot in slots:
        if not slot:
            continue

        set_id = slot.get("set_id")
        pokemon_set = pokemon_set_map.get(set_id)

        if pokemon_set:
            ordered_sets.append(
                {
                    "set": pokemon_set,
                    "mega_active": slot.get("mega_active", True),
                }
            )

    return ordered_sets


def get_party_sets_from_party(party):
    """
    Partyモデルから診断用の型リストを作る。

    パーティー詳細画面の初期表示では、メガストーン型はメガ後扱いにする。
    """
    slots = []

    for pokemon_set in party.slots():
        if pokemon_set is None:
            continue

        slots.append(
            {
                "set_id": pokemon_set.id,
                "mega_active": True,
            }
        )

    return get_party_sets_from_slots(slots)


def build_party_summary(ordered_sets):
    """
    パーティー概要表示用。
    """
    members = []

    for item in ordered_sets:
        pokemon_set = item["set"]
        mega_active = item["mega_active"]

        effective_pokemon = get_effective_pokemon(
            pokemon_set,
            mega_active=mega_active,
        )

        members.append(
            {
                "set": pokemon_set,
                "pokemon": effective_pokemon,
                "mega_active": mega_active and pokemon_set.is_mega_stone,
            }
        )

    return members


def build_good_matchups(ordered_sets):
    """
    比較的得意なポケモンを、役割遂行方法ごとにまとめる。
    """
    grouped = {
        method: []
        for method in MATCHUP_METHOD_ORDER
    }

    seen = {
        method: set()
        for method in MATCHUP_METHOD_ORDER
    }

    for item in ordered_sets:
        pokemon_set = item["set"]

        for matchup in pokemon_set.matchups.all():
            method = matchup.method
            target = matchup.target_pokemon

            if method not in grouped:
                continue

            if target.id in seen[method]:
                continue

            grouped[method].append(target)
            seen[method].add(target.id)

    return [
        {
            "method": method,
            "label": MATCHUP_METHOD_LABELS[method],
            "targets": grouped[method],
        }
        for method in MATCHUP_METHOD_ORDER
    ]


def build_bad_matchups(ordered_sets):
    """
    比較的苦手なポケモンを、苦手登録回数が多い順にまとめる。

    表示例：
    ブリジュラス → 苦手登録した味方型アイコン一覧
    """
    grouped = defaultdict(list)

    for item in ordered_sets:
        pokemon_set = item["set"]

        for weak in pokemon_set.weak_matchups.all():
            target = weak.target_pokemon
            grouped[target].append(pokemon_set)

    result = []

    for target, weak_sets in grouped.items():
        result.append(
            {
                "target": target,
                "weak_sets": weak_sets,
                "count": len(weak_sets),
            }
        )

    result.sort(
        key=lambda row: (-row["count"], row["target"].name)
    )

    return result


def build_coverage_holes(good_matchups, bad_matchups):
    """
    構築の穴を判定する。

    条件：
    苦手対象として登録されている
    かつ
    パーティー内の誰からも役割対象として登録されていない
    """
    covered_target_ids = set()

    for group in good_matchups:
        for target in group["targets"]:
            covered_target_ids.add(target.id)

    holes = []

    for bad in bad_matchups:
        target = bad["target"]

        if target.id not in covered_target_ids:
            holes.append(
                {
                    "target": target,
                    "weak_sets": bad["weak_sets"],
                    "count": bad["count"],
                }
            )

    holes.sort(
        key=lambda row: (-row["count"], row["target"].name)
    )

    return holes


def build_virtual_target_diagnosis(good_matchups, bad_matchups):
    """
    仮想敵フラグONのポケモンについて、
    対応あり・苦手登録あり・未登録・穴を分類する。
    """
    virtual_targets = list(
        Pokemon.objects
        .filter(is_virtual_target=True)
        .order_by("name")
    )

    covered_ids = set()
    weak_ids = set()

    for group in good_matchups:
        for target in group["targets"]:
            covered_ids.add(target.id)

    for bad in bad_matchups:
        weak_ids.add(bad["target"].id)

    covered = []
    weak = []
    unregistered = []
    holes = []

    for target in virtual_targets:
        is_covered = target.id in covered_ids
        is_weak = target.id in weak_ids

        if is_covered:
            covered.append(target)

        if is_weak:
            weak.append(target)

        if not is_covered and not is_weak:
            unregistered.append(target)

        if is_weak and not is_covered:
            holes.append(target)

    return {
        "covered": covered,
        "weak": weak,
        "unregistered": unregistered,
        "holes": holes,
    }

def build_type_display_item(type_name):
    """
    診断画面でタイプ名をタイプ色付きで表示するためのデータを作る。
    """
    return {
        "name": type_name,
        "type_class": get_type_class(type_name),
    }

def build_type_display_item(type_name):
    """
    診断画面でタイプ名をタイプ色付きで表示するためのデータを作る。
    """
    return {
        "name": type_name,
        "type_class": get_type_class(type_name),
    }

def build_defensive_type_coverage(ordered_sets):
    """
    防御側タイプ一貫を診断する。

    等倍以上：
    登録済みポケモン全員に等倍以上で通る攻撃タイプ。
    ただし、抜群以上に分類されるタイプは表示上除外する。

    抜群以上：
    登録済みポケモン全員に抜群以上で通る攻撃タイプ。

    要注意：
    登録済みポケモン全員には一貫していないが、
    3体以上に抜群を取れる攻撃タイプ。
    ただし、抜群以上に表示されるタイプは除外する。
    """
    if not ordered_sets:
        return {
            "neutral_or_more": [],
            "super_effective_all": [],
            "caution": [],
            "ground_immunes": [],
            "electric_immunes": [],
            "details": [],
        }

    # ここでは、判定用として文字列のまま扱う
    neutral_or_more_names = []
    super_effective_all_names = []
    caution = []
    details = []

    ground_immunes = []
    electric_immunes = []

    for attack_type in TYPE_NAMES:
        rows = []
        neutral_or_more_count = 0
        super_effective_count = 0
        immune_count = 0

        for item in ordered_sets:
            pokemon_set = item["set"]
            mega_active = item["mega_active"]

            effective_pokemon = get_effective_pokemon(
                pokemon_set,
                mega_active=mega_active,
            )

            multiplier = calculate_defensive_multiplier(
                attack_type,
                effective_pokemon,
                pokemon_set.ability_name,
            )

            if multiplier >= 1:
                neutral_or_more_count += 1

            if multiplier >= 2:
                super_effective_count += 1

            if multiplier == 0:
                immune_count += 1

                if attack_type == "じめん":
                    ground_immunes.append(
                        {
                            "set": pokemon_set,
                            "pokemon": effective_pokemon,
                        }
                    )

                if attack_type == "でんき":
                    electric_immunes.append(
                        {
                            "set": pokemon_set,
                            "pokemon": effective_pokemon,
                        }
                    )

            rows.append(
                {
                    "set": pokemon_set,
                    "pokemon": effective_pokemon,
                    "multiplier": multiplier,
                }
            )

        member_count = len(ordered_sets)

        is_neutral_or_more_all = neutral_or_more_count == member_count
        is_super_effective_all = super_effective_count == member_count

        if is_neutral_or_more_all:
            neutral_or_more_names.append(attack_type)

        if is_super_effective_all:
            super_effective_all_names.append(attack_type)

        details.append(
            {
                "attack_type": attack_type,
                "neutral_or_more_count": neutral_or_more_count,
                "super_effective_count": super_effective_count,
                "immune_count": immune_count,
                "rows": rows,
            }
        )

    super_effective_all_set = set(super_effective_all_names)

    # 抜群以上は等倍以上にも含まれるため、表示上は等倍以上から除外する
    neutral_or_more_names = [
        type_name
        for type_name in neutral_or_more_names
        if type_name not in super_effective_all_set
    ]

    for row in details:
        attack_type = row["attack_type"]

        if attack_type in super_effective_all_set:
            continue

        if row["super_effective_count"] >= 3:
            caution.append(
                {
                    "name": attack_type,
                    "type_class": get_type_class(attack_type),
                    "super_effective_count": row["super_effective_count"],
                }
            )

    return {
        "neutral_or_more": [
            build_type_display_item(type_name)
            for type_name in neutral_or_more_names
        ],
        "super_effective_all": [
            build_type_display_item(type_name)
            for type_name in super_effective_all_names
        ],
        "caution": caution,
        "ground_immunes": ground_immunes,
        "electric_immunes": electric_immunes,
        "details": details,
    }


def diagnose_party_from_ordered_sets(ordered_sets):
    party_summary = build_party_summary(ordered_sets)
    good_matchups = build_good_matchups(ordered_sets)
    bad_matchups = build_bad_matchups(ordered_sets)
    coverage_holes = build_coverage_holes(good_matchups, bad_matchups)
    virtual_target_diagnosis = build_virtual_target_diagnosis(
        good_matchups,
        bad_matchups,
    )
    defensive_type_coverage = build_defensive_type_coverage(ordered_sets)

    return {
        "party_summary": party_summary,
        "coverage_holes": coverage_holes,
        "good_matchups": good_matchups,
        "bad_matchups": bad_matchups,
        "virtual_target_diagnosis": virtual_target_diagnosis,
        "defensive_type_coverage": defensive_type_coverage,
    }

def diagnose_party(party):
    """
    Partyモデルから診断結果を返す。
    """
    ordered_sets = get_party_sets_from_party(party)
    return diagnose_party_from_ordered_sets(ordered_sets)


def diagnose_slots(slots):
    """
    JavaScript fetch用。
    slotsから診断結果を返す。
    """
    ordered_sets = get_party_sets_from_slots(slots)
    return diagnose_party_from_ordered_sets(ordered_sets)