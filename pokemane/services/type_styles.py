TYPE_CSS_CLASS = {
    "ノーマル": "type-normal",
    "ほのお": "type-fire",
    "みず": "type-water",
    "でんき": "type-electric",
    "くさ": "type-grass",
    "こおり": "type-ice",
    "かくとう": "type-fighting",
    "どく": "type-poison",
    "じめん": "type-ground",
    "ひこう": "type-flying",
    "エスパー": "type-psychic",
    "むし": "type-bug",
    "いわ": "type-rock",
    "ゴースト": "type-ghost",
    "ドラゴン": "type-dragon",
    "あく": "type-dark",
    "はがね": "type-steel",
    "フェアリー": "type-fairy",
}


def get_type_class(type_name):
    return TYPE_CSS_CLASS.get(type_name, "type-unknown")