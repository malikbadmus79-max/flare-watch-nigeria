"""Phase 3 steps 5-6: apply column settings, helper tables and measures from model_spec.py
to the open FlareWatch model. Re-runnable: existing measures/columns/tables are updated,
not duplicated. Makes no report visuals."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model_spec as spec  # noqa: E402
from mcp_client import PBI  # noqa: E402

OPTS = {"continueOnError": False, "useTransaction": True}


def column_defs() -> list[dict]:
    cols: dict[tuple[str, str], dict] = {}

    def d(t, c):
        return cols.setdefault((t, c), {"tableName": t, "name": c})

    for t, cs in spec.NO_SUM.items():
        for c in cs:
            d(t, c)["summarizeBy"] = "None"
    for t, cs in spec.HIDDEN.items():
        for c in cs:
            d(t, c)["isHidden"] = True
    for (t, c), f in spec.FORMATS.items():
        d(t, c)["formatString"] = f
    for (t, c), cat in spec.DATA_CATEGORY.items():
        d(t, c)["dataCategory"] = cat
    return list(cols.values())


def main() -> None:
    pbi = PBI()
    try:
        tables = {t["name"] for t in pbi.call("table_operations", operation="List")["data"]}
        existing_cols = {(t["tableName"], c["name"])
                         for t in pbi.call("column_operations", operation="List")["data"] for c in t["columns"]}

        # step 5: column properties
        r = pbi.call("column_operations", operation="Update", definitions=column_defs(), options=OPTS)
        print("columns updated:", r.get("summary", r.get("message")))

        # sort helper column + sort-by
        new = [c for c in spec.CALC_COLUMNS if (c["tableName"], c["name"]) not in existing_cols]
        if new:
            r = pbi.call("column_operations", operation="Create", definitions=new, options=OPTS)
            print("calc columns created:", r.get("summary", r.get("message")))
        sort = [{"tableName": t, "name": c, "sortByColumn": s} for (t, c), s in spec.SORT_BY.items()]
        if sort:
            r = pbi.call("column_operations", operation="Update", definitions=sort, options=OPTS)
            print("sort-by set:", r.get("summary", r.get("message")))

        # step 6: helper tables
        for t in spec.CALC_TABLES:
            op = "Update" if t["name"] in tables else "Create"
            r = pbi.call("table_operations", operation=op, definitions=[t], options=OPTS)
            print(f"table {op}:", t["name"], r.get("summary", r.get("message")))
        hide = [{"tableName": spec.MEASURE_TABLE, "name": "_", "isHidden": True}]
        pbi.call("column_operations", operation="Update", definitions=hide, options=OPTS)

        # measures
        listed = pbi.call("measure_operations", operation="List").get("data") or []
        have = {m["name"] for t in listed for m in t.get("measures", [])}
        create, update = [], []
        for name, folder, fmt, desc, dax in spec.MEASURES:
            m = {"tableName": spec.MEASURE_TABLE, "name": name, "expression": dax, "formatString": fmt,
                 "description": desc, "displayFolder": folder}
            (update if name in have else create).append(m)
        if create:
            r = pbi.call("measure_operations", operation="Create", definitions=create, options=OPTS)
            print("measures created:", r.get("summary", r.get("message")))
        if update:
            r = pbi.call("measure_operations", operation="Update", definitions=update, options=OPTS)
            print("measures updated:", r.get("summary", r.get("message")))

        # recalculate calculated tables last (any change to them above leaves them empty until recalculated)
        pbi.call("table_operations", operation="RefreshWithXMLA", refreshType="Calculate",
                 references=[{"name": t["name"]} for t in spec.CALC_TABLES])
        print("calc tables recalculated")
    finally:
        pbi.close()


if __name__ == "__main__":
    main()
