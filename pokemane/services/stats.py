from math import floor


SCARF_ITEM_NAME = "こだわりスカーフ"


def get_effective_pokemon(pokemon_set, mega_active=True):
    """
    型に対して、実際に計算に使うPokemonを返す。

    - メガストーン持ち
    - mega_active=True
    - メガ進化先が登録済み

    の場合は、メガ進化後Pokemonを返す。
    それ以外は通常のpokemonを返す。
    """
    pokemon = pokemon_set.pokemon

    if (
        mega_active
        and pokemon_set.is_mega_stone
        and pokemon.mega_evolution_pokemon is not None
    ):
        return pokemon.mega_evolution_pokemon

    return pokemon


def get_nature_modifier(stat_name, pokemon_set):
    """
    性格補正を返す。

    stat_name:
    - attack
    - defense
    - sp_attack
    - sp_defense
    - speed

    HPには性格補正をかけない。
    """
    if stat_name == pokemon_set.nature_up:
        return 1.1

    if stat_name == pokemon_set.nature_down:
        return 0.9

    return 1.0


def calculate_hp(base_hp, point_hp):
    """
    HP実数値を計算する。

    ポケモンチャンピオンズ仕様：
    HP = 種族値 + 75 + 能力ポイント

    端数は切り捨て。
    """
    return floor(base_hp + 75 + point_hp)


def calculate_non_hp_stat(base_stat, point, modifier=1.0):
    """
    HP以外の実数値を計算する。

    ポケモンチャンピオンズ仕様：
    実数値 = (種族値 + 20 + 能力ポイント) × 能力補正

    端数は切り捨て。
    """
    return floor((base_stat + 20 + point) * modifier)


def calculate_actual_stats(pokemon_set, mega_active=True):
    """
    型の実数値を辞書で返す。

    戻り値：
    {
        "hp": 185,
        "attack": 182,
        "defense": 115,
        "sp_attack": 90,
        "sp_defense": 105,
        "speed": 169,
    }
    """
    pokemon = get_effective_pokemon(pokemon_set, mega_active=mega_active)

    return {
        "hp": calculate_hp(
            pokemon.base_hp,
            pokemon_set.point_hp,
        ),
        "attack": calculate_non_hp_stat(
            pokemon.base_attack,
            pokemon_set.point_attack,
            get_nature_modifier("attack", pokemon_set),
        ),
        "defense": calculate_non_hp_stat(
            pokemon.base_defense,
            pokemon_set.point_defense,
            get_nature_modifier("defense", pokemon_set),
        ),
        "sp_attack": calculate_non_hp_stat(
            pokemon.base_sp_attack,
            pokemon_set.point_sp_attack,
            get_nature_modifier("sp_attack", pokemon_set),
        ),
        "sp_defense": calculate_non_hp_stat(
            pokemon.base_sp_defense,
            pokemon_set.point_sp_defense,
            get_nature_modifier("sp_defense", pokemon_set),
        ),
        "speed": calculate_non_hp_stat(
            pokemon.base_speed,
            pokemon_set.point_speed,
            get_nature_modifier("speed", pokemon_set),
        ),
    }


def calculate_physical_bulk(actual_stats):
    """
    物理耐久指数 = HP実数値 × 防御実数値
    """
    return actual_stats["hp"] * actual_stats["defense"]


def calculate_special_bulk(actual_stats):
    """
    特殊耐久指数 = HP実数値 × 特防実数値
    """
    return actual_stats["hp"] * actual_stats["sp_defense"]


def calculate_overall_bulk(actual_stats):
    """
    総合耐久指数 =
    floor((HP × 防御 × 特防) ÷ (防御 + 特防))
    """
    hp = actual_stats["hp"]
    defense = actual_stats["defense"]
    sp_defense = actual_stats["sp_defense"]

    denominator = defense + sp_defense

    if denominator == 0:
        return 0

    return floor((hp * defense * sp_defense) / denominator)


def is_choice_scarf(pokemon_set):
    """
    持ち物が「こだわりスカーフ」かどうかを判定する。

    MVPでは、手入力の持ち物名と完全一致で判定する。
    """
    if pokemon_set.is_mega_stone:
        return False

    return pokemon_set.custom_item_name == SCARF_ITEM_NAME


def calculate_speed_for_sort(pokemon_set, mega_active=True):
    """
    型一覧ソート用の素早さを返す。

    - 通常は素早さ実数値
    - 持ち物が「こだわりスカーフ」の場合のみ1.5倍
    - 端数切り捨て
    """
    actual_stats = calculate_actual_stats(
        pokemon_set,
        mega_active=mega_active,
    )

    speed = actual_stats["speed"]

    if is_choice_scarf(pokemon_set):
        return floor(speed * 1.5)

    return speed


def build_stats_summary(pokemon_set, mega_active=True):
    """
    型カード表示やソートで使いやすいように、
    実数値と耐久指数をまとめて返す。
    """
    actual_stats = calculate_actual_stats(
        pokemon_set,
        mega_active=mega_active,
    )

    return {
        "actual_stats": actual_stats,
        "physical_bulk": calculate_physical_bulk(actual_stats),
        "special_bulk": calculate_special_bulk(actual_stats),
        "overall_bulk": calculate_overall_bulk(actual_stats),
        "speed_for_sort": calculate_speed_for_sort(
            pokemon_set,
            mega_active=mega_active,
        ),
    }