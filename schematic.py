from pathlib import Path
import re
import uuid
import math
from typing import Tuple, Any
import json

# grab sch thumbnail: kicad-cli sch export svg --output schematic.svg test.kicad_sch
# grab pcb thumbnail: kicad-cli pcb export svg --layers F.Cu,F.Mask,F.SilkS,F.Fab,Drill,Edge.Cuts --output board.svg test.kicad_pcb


def llm_generate_plan():
    path = Path("llm_output1.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data

def llm_generate_nets():
    path = Path("llm_output2.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data

def validate_plan(plan_json):
    pass

def _find_root_uuid(text: str) -> str:
    m = re.search(r'^\s*\(uuid\s+"?([0-9a-fA-F-]+)"?\)\s*$', text, flags=re.MULTILINE)
    if not m:
        raise ValueError('Could not find top-level (uuid "...") in schematic.')
    return m.group(1)

def _sexpr_end(text: str, start_idx: int) -> int:
    if start_idx < 0 or text[start_idx] != "(":
        raise ValueError("start_idx must point at '('")
    depth = 0
    for i in range(start_idx, len(text)):
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("Unbalanced parentheses")

def get_symbol_def(lib_file: str | Path, symbol_name: str) -> str:
    lib_path = Path(lib_file)
    text = lib_path.read_text(encoding="utf-8")

    pat = re.compile(rf'\(\s*symbol\s+"{re.escape(symbol_name)}"\s*[\n)]')
    m = pat.search(text)
    if not m:
        raise ValueError(f'Could not find top-level symbol opener: (symbol "{symbol_name}" in {lib_path}')

    sym_start = m.start()
    block = text[sym_start:_sexpr_end(text, sym_start)]
    lib_id = f"{lib_path.stem}:{symbol_name}"
    block = re.sub(r'^\(\s*symbol\s+"[^"]+"', f'(symbol "{lib_id}"', block, count=1)
    return block

def add_lib_symbol(text: str, lib_file: str | Path, symbol_name: str) -> str:
    lib_id = f"{lib_file.stem}:{symbol_name}"
    if re.search(rf'\(symbol\s+"{re.escape(lib_id)}"', text):
        return text

    symbol_def = get_symbol_def(lib_file, symbol_name).rstrip() + "\n"

    m = re.search(r'^\s*\(lib_symbols\b', text, flags=re.MULTILINE)
    if not m:
        raise ValueError("No (lib_symbols) section found in schematic text.")

    lib_start = text.rfind("(", 0, m.end())
    lib_end = _sexpr_end(text, lib_start)

    lib_block = text[lib_start:lib_end]

    if re.fullmatch(r'\(\s*lib_symbols\s*\)', lib_block.strip()):
        new_block = "\t(lib_symbols\n\t\t" + symbol_def.replace("\n", "\n\t\t").rstrip() + "\n\t)"
        return text[:lib_start] + new_block + text[lib_end:]

    insert_at = lib_end - 1
    insertion = "\n\t\t" + symbol_def.replace("\n", "\n\t\t")
    return text[:insert_at] + insertion + text[insert_at:]

def _next_ref(text: str, ref_prefix: str) -> str:
    pattern = re.compile(rf'\(property\s+"Reference"\s+"({re.escape(ref_prefix)}(\d+))"\s*')
    nums = [int(m.group(2)) for m in pattern.finditer(text)]
    if not nums:
        return f"{ref_prefix}1"
    used = set(nums)
    n = 1
    while n in used:
        n += 1
    return f"{ref_prefix}{n}"

def _parse_property(symbol_def: str, prop_name: str) -> Tuple[float, float, int]:
    pm = re.search(rf'\(\s*property\s+"{re.escape(prop_name)}"\s+"[^"]*"[\s\S]*?\)', symbol_def, flags=re.DOTALL)
    if not pm:
        raise ValueError(f'Library symbol missing property "{prop_name}" block')

    prop_block = pm.group(0)

    am = re.search(r'\(\s*at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\)', prop_block)
    if not am:
        raise ValueError(f'Library symbol property "{prop_name}" exists but is missing an (at x y rot)')

    px = float(am.group(1))
    py = float(am.group(2))
    prot = int(round(float(am.group(3))))
    return px, py, prot


def _rotate_translate(px: float, py: float, rot_deg: int, x: float, y: float) -> tuple[float, float]:
    theta = math.radians(rot_deg % 360)
    cx = px * math.cos(theta) - py * math.sin(theta)
    cy = px * math.sin(theta) + py * math.cos(theta)
    return x + cx, y - cy

def place_symbol(sch_path: str | Path, lib_file: str | Path, symbol_name: str, ref_des: str, 
                x: float, y: float, rot: int = 0, value: str | None = None, footprint: str = "") -> str:
    sch_path = Path(sch_path)
    text = sch_path.read_text(encoding="utf-8")

    text = add_lib_symbol(text, lib_file, symbol_name)

    root_uuid = _find_root_uuid(text)
    sym_uuid = str(uuid.uuid4())
    pin1_uuid = str(uuid.uuid4())
    pin2_uuid = str(uuid.uuid4())

    lib_id = f"{Path(lib_file).stem}:{symbol_name}"
    value_str = value if value is not None else symbol_name
    unit = 1

    sym_def = get_symbol_def(lib_file, symbol_name)
    ref_px, ref_py, ref_prot = _parse_property(sym_def, "Reference")
    val_px, val_py, val_prot = _parse_property(sym_def, "Value")
    ref_x, ref_y = _rotate_translate(ref_px, ref_py, rot, x, y)
    val_x, val_y = _rotate_translate(val_px, val_py, rot, x, y)
    ref_rot = (ref_prot + rot) % 360
    val_rot = (val_prot + rot) % 360

    symbol_block = f"""
    \t(symbol
    \t\t(lib_id "{lib_id}")
    \t\t(at {x:.3f} {y:.3f} {rot})
    \t\t(unit {unit})
    \t\t(exclude_from_sim no)
    \t\t(in_bom yes)
    \t\t(on_board yes)
    \t\t(dnp no)
    \t\t(fields_autoplaced yes)
    \t\t(uuid "{sym_uuid}")
    \t\t(property "Reference" "{ref_des}"
    \t\t\t(at {ref_x:.3f} {ref_y:.3f} {ref_rot})
    \t\t\t(effects
    \t\t\t\t(font
    \t\t\t\t\t(size 1.27 1.27)
    \t\t\t\t)
    \t\t\t)
    \t\t)
    \t\t(property "Value" "{value_str}"
    \t\t\t(at {val_x:.3f} {val_y:.3f} {val_rot})
    \t\t\t(effects
    \t\t\t\t(font
    \t\t\t\t\t(size 1.27 1.27)
    \t\t\t\t)
    \t\t\t)
    \t\t)
    \t\t(property "Footprint" "{footprint}"
    \t\t\t(at {x:.3f} {y + 1.778:.3f} {rot})
    \t\t\t(effects
    \t\t\t\t(font
    \t\t\t\t\t(size 1.27 1.27)
    \t\t\t\t)
    \t\t\t\t(hide yes)
    \t\t\t)
    \t\t)
    \t\t(property "Datasheet" "~"
    \t\t\t(at {x:.3f} {y:.3f} 0)
    \t\t\t(effects
    \t\t\t\t(font
    \t\t\t\t\t(size 1.27 1.27)
    \t\t\t\t)
    \t\t\t\t(hide yes)
    \t\t\t)
    \t\t)
    \t\t(instances
    \t\t\t(project ""
    \t\t\t\t(path "/{root_uuid}"
    \t\t\t\t\t(reference "{ref_des}")
    \t\t\t\t\t(unit {unit})
    \t\t\t\t)
    \t\t\t)
    \t\t)
    \t)
    """

    si = text.find("\t(sheet_instances")
    if si != -1:
        new_text = text[:si] + symbol_block + text[si:]
    else:
        idx = text.rfind(")")
        if idx == -1:
            raise ValueError("Invalid schematic: no closing ')'.")
        new_text = text[:idx] + symbol_block + text[idx:]

    sch_path.write_text(new_text, encoding="utf-8")
    return new_text

def draw_wire(sch_path: str | Path, points: list[tuple[float, float]]) -> None:
    if len(points) != 2:
        raise ValueError("Wire must have two points")

    sch_path = Path(sch_path)
    text = sch_path.read_text(encoding="utf-8")

    pts = " ".join(f"(xy {x} {y})" for x, y in points)
    wire_block = f"""
        (wire
            (pts
                {pts}
            )
            (stroke
                (width 0)
                (type default)
            )
            (uuid "{uuid.uuid4()}")
        )
    """.rstrip()

    m = re.search(r"\n\s*\(sheet_instances\b", text)
    if not m:
        raise RuntimeError("Could not find sheet_instances block")

    insert_at = m.start()
    new_text = text[:insert_at] + "\n" + wire_block + text[insert_at:]

    sch_path.write_text(new_text, encoding="utf-8")

def place_from_llm_output(sch_path: str | Path, lib_file: str | Path, llm_output: dict[str, Any]) -> str:
    sch_path = Path(sch_path)
    sch_text = sch_path.read_text(encoding="utf-8")
    symbols = llm_output["symbols"]

    for s in symbols:
        file_name = s["lib"]
        symbol_name = s["symbol"]
        ref_des = s["ref_des"]
        at = s["at"]
        x, y, rot = at["x"], at["y"], at["rot"]
        value = s["value"]
        footprint = s["footprint"]
        sch_text = place_symbol(sch_path, lib_file / file_name, symbol_name, ref_des, x, y, rot=rot, value=value, footprint=footprint)
    return sch_text

def add_pin_outs(lib_dir: str | Path, llm_output: dict[str, Any]) -> dict[str, str]:
    lib_dir = Path(lib_dir)
    symbols = llm_output["symbols"]
    defs = {}
    pin_re = re.compile(
        r"\(pin\s+\w+\s+\w+.*?"
        r"\(at\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+)\).*?"
        r"\(name\s+\"([^\"]+)\".*?"
        r"\(number\s+\"([^\"]+)\"",
        re.S
    )
    for s in symbols:
        lib_path = lib_dir / s["lib"]
        sym_def = get_symbol_def(lib_path, s["symbol"])

        sx = s["at"]["x"]
        sy = s["at"]["y"]
        srot = s["at"]["rot"]

        pins = {}

        for m in pin_re.finditer(sym_def):
            px = float(m.group(1))
            py = float(m.group(2))
            prot = int(m.group(3))
            pin_name = m.group(4)
            pin_num = m.group(5)

            ax, ay = _rotate_translate(px, py, srot, sx, sy)
            arot = (prot + srot) % 360

            pins[pin_num] = {
                "name": pin_name,
                "pos": (ax, ay, arot)
            }
        s["pins"] = pins
    return llm_output

def get_pin_xy(llm_output, ref: str, pin: int) -> tuple[float, float]:
    pin = str(pin)
    for s in llm_output["symbols"]:
        if s["ref_des"] == ref:
            pin_data = s["pins"].get(pin)
            if not pin_data:
                raise KeyError(f"Pin {pin} not found on {ref}")
            x, y, _ = pin_data["pos"]
            return x, y
    raise KeyError(f"Symbol {ref} not found")

def draw_nets(sch_path: str | Path, llm_output1: dict[str, Any], llm_output2: dict[str, Any]) -> None:
    for net in llm_output2["nets"]:
        conns = net["connections"]
        if len(conns) < 2:
            continue

        anchor = conns[0]
        ax, ay = get_pin_xy(llm_output1, anchor["ref"], anchor["pin"])

        for c in conns[1:]:
            px, py = get_pin_xy(llm_output1, c["ref"], c["pin"])
            draw_wire(sch_path, [(ax, ay), (px, py)])

def clear_schematic(sch_path: str | Path) -> None:
    sch_path = Path(sch_path)
    text = sch_path.read_text(encoding="utf-8")

    root_uuid = _find_root_uuid(text)

    cleared = f'''(kicad_sch
        \t(version 20250114)
        \t(generator "eeschema")
        \t(generator_version "9.0")
        \t(uuid "{root_uuid}")
        \t(paper "A4")
        \t(lib_symbols)
        \t(sheet_instances
        \t\t(path "/"
        \t\t\t(page "1")
        \t\t)
        \t)
        \t(embedded_fonts no)
        )
    '''

    sch_path.write_text(cleared, encoding="utf-8")
