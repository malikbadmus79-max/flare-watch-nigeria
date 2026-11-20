"""Register a custom theme in a PBIR report and make it the active custom theme.
Replaces the previous custom theme (its RegisteredResources file and report.json entries).
Usage: python register_theme.py <FlareWatch.Report folder> <theme.json>"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def main(report_dir: str, theme_path: str) -> None:
    rep = Path(report_dir)
    theme = Path(theme_path)
    json.loads(theme.read_text(encoding="utf-8"))  # must be valid JSON
    reg = rep / "StaticResources" / "RegisteredResources"
    new_name = "Flare_Watch_Nigeria_Night.json"
    rj_path = rep / "definition" / "report.json"
    rj = json.loads(rj_path.read_text(encoding="utf-8"))

    old_name = rj["themeCollection"]["customTheme"]["name"]
    rj["themeCollection"]["customTheme"]["name"] = new_name
    for pkg in rj["resourcePackages"]:
        if pkg["name"] == "RegisteredResources":
            pkg["items"] = [i for i in pkg["items"] if i.get("type") != "CustomTheme"]
            pkg["items"].append({"name": new_name, "path": new_name, "type": "CustomTheme"})

    shutil.copyfile(theme, reg / new_name)
    if old_name != new_name and (reg / old_name).exists():
        (reg / old_name).unlink()
    rj_path.write_text(json.dumps(rj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"custom theme: {old_name} -> {new_name}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
