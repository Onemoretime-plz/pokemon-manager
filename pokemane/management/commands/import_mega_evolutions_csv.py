import csv
import io
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from pokemane.models import MegaEvolution, Pokemon


def read_csv_text_with_fallback(csv_path):
    """
    CSV/TSVをUTF-8優先で読み込み、失敗した場合はCP932で読み込む。
    日本語CSVはExcel等でCP932保存されることがあるため。
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
    カンマ区切りCSV / タブ区切りTSV / セミコロン区切りに対応したDictReaderを返す。
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


class Command(BaseCommand):
    help = "Import Mega Evolution data from CSV or TSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            nargs="?",
            default="data/mega_evolutions.csv",
            help="Path to mega_evolutions.csv",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])

        if not csv_path.exists():
            raise CommandError(f"CSVファイルが見つかりません: {csv_path}")

        created_count = 0
        updated_count = 0

        reader = build_dict_reader(csv_path)

        required_columns = [
            "base_pokemon",
            "mega_pokemon",
            "form_name",
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
                base_pokemon_name = row["base_pokemon"].strip()
                mega_pokemon_name = row["mega_pokemon"].strip()
                form_name = row["form_name"].strip()

                if not base_pokemon_name:
                    raise ValueError("base_pokemon は必須です。")

                if not mega_pokemon_name:
                    raise ValueError("mega_pokemon は必須です。")

                try:
                    base_pokemon = Pokemon.objects.get(name=base_pokemon_name)
                except Pokemon.DoesNotExist as exc:
                    raise ValueError(
                        f"メガ進化前ポケモンが見つかりません: {base_pokemon_name}"
                    ) from exc

                try:
                    mega_pokemon = Pokemon.objects.get(name=mega_pokemon_name)
                except Pokemon.DoesNotExist as exc:
                    raise ValueError(
                        f"メガ進化後ポケモンが見つかりません: {mega_pokemon_name}"
                    ) from exc

                _, created = MegaEvolution.objects.update_or_create(
                    base_pokemon=base_pokemon,
                    mega_pokemon=mega_pokemon,
                    defaults={
                        "form_name": form_name,
                    },
                )

                # 旧フィールド互換用。
                # 現在のメガ分岐管理は MegaEvolution モデルを正とする。
                base_pokemon.can_mega_evolve = True
                base_pokemon.save(update_fields=["can_mega_evolve"])

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
                f"Mega Evolution import completed. created={created_count}, updated={updated_count}"
            )
        )