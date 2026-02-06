import json
from pathlib import Path
from schematic import place_symbol

sch = Path("/Users/adityarao/Documents/KiCad/9.0/projects/test/test.kicad_sch")
prompt = Path("allow_list.json")
symbol_lib = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/")

allowed_list = json.loads(prompt.read_text(encoding="utf-8"))["allowlist"]

x0, y0 = 25.0, 25.0
dx, dy = 35.0, 25.0
cols = 6
for i, item in enumerate(allowed_list):
    col = i % cols
    row = i // cols
    x = x0 + col * dx
    y = y0 + row * dy
    lib_file = symbol_lib / item["lib"]
    place_symbol(sch, lib_file, item["symbol"], item["ref"], x, y, value=item["symbol"])
