import csv
import io
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from pokemane.models import Pokemon


def read_csv_text_with_fallback(csv_path):
    """
    CSV/TSVをUTF-8優先で読み込み、失敗した場合はCP932で読み込む。
    """
    encodings = ["utf-8-sig", "cp932"]

    last_error = None

    raw = csv_path.read_bytes()

    for encoding in encodings:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError as exc:
            last_error = exc

    raise last_error


def build_dict_reader(csv_path):
    """
    カンマ区切りCSV / タブ区切りTSV の両方に対応したDictReaderを返す。
    """
    text = read_csv_text_with_fallback(csv_path)

    sample = text[:4096]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)

    if reader.fieldnames:
        reader.fieldnames = [
            field_name.strip()
            for field_name in reader.fieldnames
        ]

    return reader


def parse_optional_int(value):
    value = str(value).strip()

    if value == "":
        return None

    return int(value)


def parse_required_int(value, field_name):
    value = str(value).strip()

    if value == "":
        raise ValueError(f"{field_name} は必須です。")

    return int(value)


def parse_optional_decimal(value):
    value = str(value).strip()

    if value == "":
        return None

    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"体重kgの値が不正です: {value}") from exc


def parse_bool(value):
    value = str(value).strip().lower()

    return value in ["1", "true", "yes", "y", "on"]


class Command(BaseCommand):
    help = "Import Pokemon data from CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            nargs="?",
            default="data/pokemon.csv",
            help="Path to pokemon.csv",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])

        if not csv_path.exists():
            raise CommandError(f"CSVファイルが見つかりません: {csv_path}")

        created_count = 0
        updated_count = 0

        reader = build_dict_reader(csv_path)

        required_columns = [
            "national_dex_no",
            "name",
            "type1",
            "type2",
            "base_hp",
            "base_attack",
            "base_defense",
            "base_sp_attack",
            "base_sp_defense",
            "base_speed",
            "weight_kg",
            "ability1",
            "ability2",
            "hidden_ability",
            "is_virtual_target",
        ]


        missing_columns = [
                column
                for column in required_columns
                if column not in reader.fieldnames
            ]

        if missing_columns:
                raise CommandError(
                    f"CSVに必要な列がありません: {', '.join(missing_columns)}"
                )

        for row_number, row in enumerate(reader, start=2):
                try:
                    name = row["name"].strip()

                    if not name:
                        raise ValueError("name は必須です。")

                    defaults = {
                        "national_dex_no": parse_optional_int(row["national_dex_no"]),
                        "type1": row["type1"].strip(),
                        "type2": row["type2"].strip() or None,
                        "base_hp": parse_required_int(row["base_hp"], "base_hp"),
                        "base_attack": parse_required_int(row["base_attack"], "base_attack"),
                        "base_defense": parse_required_int(row["base_defense"], "base_defense"),
                        "base_sp_attack": parse_required_int(row["base_sp_attack"], "base_sp_attack"),
                        "base_sp_defense": parse_required_int(row["base_sp_defense"], "base_sp_defense"),
                        "base_speed": parse_required_int(row["base_speed"], "base_speed"),
                        "weight_kg": parse_optional_decimal(row["weight_kg"]),
                        "ability1": row["ability1"].strip(),
                        "ability2": row["ability2"].strip(),
                        "hidden_ability": row["hidden_ability"].strip(),
                        "is_virtual_target": parse_bool(row["is_virtual_target"]),
                    }

                    pokemon, created = Pokemon.objects.update_or_create(
                        name=name,
                        defaults=defaults,
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as exc:
                    raise CommandError(
                        f"{row_number}行目でエラー: {exc}"
                    ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Pokemon import completed. created={created_count}, updated={updated_count}"
            )
        )