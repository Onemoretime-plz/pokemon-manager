from django.core.exceptions import ValidationError
from django.db import models


TYPE_CHOICES = [
    ("ノーマル", "ノーマル"),
    ("ほのお", "ほのお"),
    ("みず", "みず"),
    ("でんき", "でんき"),
    ("くさ", "くさ"),
    ("こおり", "こおり"),
    ("かくとう", "かくとう"),
    ("どく", "どく"),
    ("じめん", "じめん"),
    ("ひこう", "ひこう"),
    ("エスパー", "エスパー"),
    ("むし", "むし"),
    ("いわ", "いわ"),
    ("ゴースト", "ゴースト"),
    ("ドラゴン", "ドラゴン"),
    ("あく", "あく"),
    ("はがね", "はがね"),
    ("フェアリー", "フェアリー"),
]


STAT_CHOICES = [
    ("none", "補正なし"),
    ("attack", "こうげき"),
    ("defense", "ぼうぎょ"),
    ("sp_attack", "とくこう"),
    ("sp_defense", "とくぼう"),
    ("speed", "すばやさ"),
]


MOVE_CATEGORY_CHOICES = [
    ("attack", "攻撃技"),
    ("status", "変化技"),
]


MATCHUP_METHOD_CHOICES = [
    ("switch_in", "後出し可"),
    ("face_to_face", "対面処理"),
    ("outspeed", "上から処理"),
    ("chip_required", "削り前提"),
    ("unstable", "やや不安定"),
]


class Pokemon(models.Model):
    name = models.CharField("ポケモン名", max_length=50, unique=True)

    national_dex_no = models.PositiveIntegerField(
        "全国図鑑No",
        blank=True,
        null=True,
        db_index=True,
    )

    type1 = models.CharField("タイプ1", max_length=20, choices=TYPE_CHOICES)
    type2 = models.CharField(
        "タイプ2",
        max_length=20,
        choices=TYPE_CHOICES,
        blank=True,
        null=True,
    )

    base_hp = models.PositiveIntegerField("HP種族値")
    base_attack = models.PositiveIntegerField("攻撃種族値")
    base_defense = models.PositiveIntegerField("防御種族値")
    base_sp_attack = models.PositiveIntegerField("特攻種族値")
    base_sp_defense = models.PositiveIntegerField("特防種族値")
    base_speed = models.PositiveIntegerField("素早さ種族値")

    weight_kg = models.DecimalField(
        "体重kg",
        max_digits=6,
        decimal_places=1,
        blank=True,
        null=True,
    )

    ability1 = models.CharField(
        "特性1",
        max_length=50,
        blank=True,
    )
    ability2 = models.CharField(
        "特性2",
        max_length=50,
        blank=True,
    )
    hidden_ability = models.CharField(
        "夢特性",
        max_length=50,
        blank=True,
    )

    icon_image = models.ImageField(
        "アイコン画像",
        upload_to="pokemon_icons/",
        blank=True,
        null=True,
    )

    is_virtual_target = models.BooleanField("仮想敵にする", default=False)

    can_mega_evolve = models.BooleanField("メガ進化可能", default=False)

    mega_evolution_pokemon = models.ForeignKey(
        "self",
        verbose_name="メガ進化先ポケモン",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pre_mega_sources",
    )

    pre_mega_pokemon = models.ForeignKey(
        "self",
        verbose_name="メガ進化前ポケモン",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="mega_forms",
    )

    class Meta:
        verbose_name = "ポケモン"
        verbose_name_plural = "ポケモン"
        ordering = ["national_dex_no", "name"]

    def ability_options(self):
        """
        このポケモンが持ちうる特性名をリストで返す。
        空欄は除外する。
        """
        return [
            ability
            for ability in [
                self.ability1,
                self.ability2,
                self.hidden_ability,
            ]
            if ability
        ]

    def __str__(self):
        return self.name

class MegaEvolution(models.Model):
    base_pokemon = models.ForeignKey(
        Pokemon,
        verbose_name="メガ進化前ポケモン",
        on_delete=models.CASCADE,
        related_name="mega_evolution_options",
    )

    mega_pokemon = models.ForeignKey(
        Pokemon,
        verbose_name="メガ進化後ポケモン",
        on_delete=models.CASCADE,
        related_name="mega_form_options",
    )

    form_name = models.CharField(
        "フォーム名",
        max_length=50,
        blank=True,
        help_text="例：X、Y、通常など",
    )

    class Meta:
        verbose_name = "メガ進化"
        verbose_name_plural = "メガ進化"
        unique_together = ("base_pokemon", "mega_pokemon")
        ordering = ["base_pokemon__name", "mega_pokemon__name"]

    def __str__(self):
        if self.form_name:
            return f"{self.base_pokemon.name} → {self.mega_pokemon.name}（{self.form_name}）"
        return f"{self.base_pokemon.name} → {self.mega_pokemon.name}"

    def clean(self):
        if self.base_pokemon_id == self.mega_pokemon_id:
            raise ValidationError("メガ進化前とメガ進化後に同じポケモンは指定できません。")

class PokemonSet(models.Model):
    pokemon = models.ForeignKey(
        Pokemon,
        verbose_name="ポケモン",
        on_delete=models.CASCADE,
        related_name="sets",
    )

    set_name = models.CharField("型名", max_length=100)

    ability_name = models.CharField("特性", max_length=50)

    is_mega_stone = models.BooleanField("メガストーン", default=False)
    custom_item_name = models.CharField(
        "持ち物名",
        max_length=100,
        blank=True,
    )

    selected_mega_evolution = models.ForeignKey(
        MegaEvolution,
        verbose_name="選択メガ進化先",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pokemon_sets",
    )

    nature_up = models.CharField(
        "上昇補正",
        max_length=20,
        choices=STAT_CHOICES,
        default="none",
    )
    nature_down = models.CharField(
        "下降補正",
        max_length=20,
        choices=STAT_CHOICES,
        default="none",
    )

    point_hp = models.PositiveIntegerField("HP能力ポイント", default=0)
    point_attack = models.PositiveIntegerField("攻撃能力ポイント", default=0)
    point_defense = models.PositiveIntegerField("防御能力ポイント", default=0)
    point_sp_attack = models.PositiveIntegerField("特攻能力ポイント", default=0)
    point_sp_defense = models.PositiveIntegerField("特防能力ポイント", default=0)
    point_speed = models.PositiveIntegerField("素早さ能力ポイント", default=0)

    memo = models.TextField("メモ", blank=True)

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        verbose_name = "ポケモンの型"
        verbose_name_plural = "ポケモンの型"
        ordering = ["pokemon__name", "set_name"]

    def __str__(self):
        return f"{self.pokemon.name} - {self.set_name}"

    def clean(self):
        points = [
            self.point_hp,
            self.point_attack,
            self.point_defense,
            self.point_sp_attack,
            self.point_sp_defense,
            self.point_speed,
        ]

        for point in points:
            if point > 32:
                raise ValidationError("能力ポイントは各ステータス最大32までです。")

        if sum(points) > 66:
            raise ValidationError("能力ポイントの合計は最大66までです。")

        if self.nature_up != "none" and self.nature_up == self.nature_down:
            raise ValidationError("上昇補正と下降補正に同じステータスは指定できません。")

        if self.is_mega_stone:
            if self.selected_mega_evolution is None:
                raise ValidationError("メガストーンを設定する場合は、メガ進化先を選択してください。")

            if self.selected_mega_evolution.base_pokemon_id != self.pokemon_id:
                raise ValidationError("選択されたメガ進化先が、このポケモンに対応していません。")

        if not self.is_mega_stone and self.selected_mega_evolution is not None:
            raise ValidationError("メガストーンを持たない型には、メガ進化先を設定できません。")

    @property
    def item_name(self):
        if self.is_mega_stone:
            return "メガストーン"
        return self.custom_item_name or "なし"


class SetMove(models.Model):
    pokemon_set = models.ForeignKey(
        PokemonSet,
        verbose_name="型",
        on_delete=models.CASCADE,
        related_name="moves",
    )

    move_name = models.CharField("技名", max_length=50, blank=True)
    move_type = models.CharField("技タイプ", max_length=20, choices=TYPE_CHOICES)
    move_category = models.CharField(
        "技分類",
        max_length=20,
        choices=MOVE_CATEGORY_CHOICES,
        default="attack",
    )

    order = models.PositiveIntegerField("技スロット", default=1)

    class Meta:
        verbose_name = "技"
        verbose_name_plural = "技"
        ordering = ["pokemon_set", "order"]

    def __str__(self):
        return f"{self.pokemon_set} - {self.move_name or '未入力'}"


class Matchup(models.Model):
    pokemon_set = models.ForeignKey(
        PokemonSet,
        verbose_name="型",
        on_delete=models.CASCADE,
        related_name="matchups",
    )

    target_pokemon = models.ForeignKey(
        Pokemon,
        verbose_name="役割対象ポケモン",
        on_delete=models.CASCADE,
        related_name="targeted_by_sets",
    )

    method = models.CharField(
        "役割遂行方法",
        max_length=30,
        choices=MATCHUP_METHOD_CHOICES,
    )

    memo = models.TextField("メモ", blank=True)

    class Meta:
        verbose_name = "役割対象"
        verbose_name_plural = "役割対象"

    def __str__(self):
        return f"{self.pokemon_set} → {self.target_pokemon}（{self.get_method_display()}）"


class WeakMatchup(models.Model):
    pokemon_set = models.ForeignKey(
        PokemonSet,
        verbose_name="型",
        on_delete=models.CASCADE,
        related_name="weak_matchups",
    )

    target_pokemon = models.ForeignKey(
        Pokemon,
        verbose_name="苦手対象ポケモン",
        on_delete=models.CASCADE,
        related_name="threatens_sets",
    )

    memo = models.TextField("メモ", blank=True)

    class Meta:
        verbose_name = "苦手対象"
        verbose_name_plural = "苦手対象"

    def __str__(self):
        return f"{self.pokemon_set} 苦手：{self.target_pokemon}"


class Party(models.Model):
    name = models.CharField("パーティー名", max_length=100)

    slot1 = models.ForeignKey(
        PokemonSet,
        verbose_name="スロット1",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="party_slot1",
    )
    slot2 = models.ForeignKey(
        PokemonSet,
        verbose_name="スロット2",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="party_slot2",
    )
    slot3 = models.ForeignKey(
        PokemonSet,
        verbose_name="スロット3",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="party_slot3",
    )
    slot4 = models.ForeignKey(
        PokemonSet,
        verbose_name="スロット4",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="party_slot4",
    )
    slot5 = models.ForeignKey(
        PokemonSet,
        verbose_name="スロット5",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="party_slot5",
    )
    slot6 = models.ForeignKey(
        PokemonSet,
        verbose_name="スロット6",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="party_slot6",
    )

    memo = models.TextField("備考", blank=True)

    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        verbose_name = "パーティー"
        verbose_name_plural = "パーティー"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    def slots(self):
        return [
            self.slot1,
            self.slot2,
            self.slot3,
            self.slot4,
            self.slot5,
            self.slot6,
        ]