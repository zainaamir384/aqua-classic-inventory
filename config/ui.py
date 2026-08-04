from decimal import Decimal


def resolve_value(instance, lookup: str):
    value = instance
    for part in lookup.split("."):
        value = getattr(value, part)
        if callable(value):
            value = value()
    if isinstance(value, Decimal):
        return f"{value:,.3f}".rstrip("0").rstrip(".")
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return value


def build_table_rows(objects, columns):
    rows = []
    for obj in objects:
        rows.append(
            {
                "object": obj,
                "values": [resolve_value(obj, column["lookup"]) for column in columns],
            }
        )
    return rows


def build_detail_rows(instance, fields):
    return [
        {
            "label": field["label"],
            "value": resolve_value(instance, field["lookup"]),
        }
        for field in fields
    ]
