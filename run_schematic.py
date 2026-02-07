from pathlib import Path
from schematic import llm_generate_plan, place_from_llm_output, add_pin_outs, draw_wire, draw_nets, llm_generate_nets
import json
from copy import deepcopy
from typing import Tuple, Any

sch = Path("/Users/angelaqu/Desktop/test/test.kicad_sch")
symbol_lib = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/")

def simplify_pins_for_llm(llm_output: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(llm_output)
    for s in out.get("symbols", []):
        pins = s.get("pins")
        if isinstance(pins, dict):
            s["pins"] = {
                pin_num: pin_data.get("name", "")
                for pin_num, pin_data in pins.items()
            }
    return out

llm_output1 = llm_generate_plan()
place_from_llm_output(sch, symbol_lib, llm_output1)
print(f"Placed components in schematic file {sch}")

llm_output1 = add_pin_outs(symbol_lib, llm_output1)
out_file = Path("llm_output1_with_pins.json")
with out_file.open("w", encoding="utf-8") as f:
    json.dump(llm_output1, f, indent=2)
print(f"Wrote pin data to {out_file}")

prompt2_template = Path("prompt2_instructions.txt")
prompt2_out = Path("prompt2.txt")
base_prompt = prompt2_template.read_text(encoding="utf-8")
final_prompt = (
    base_prompt.rstrip()
    + "\n\n"
    + "Here is the component list JSON:\n\n"
    + json.dumps(simplify_pins_for_llm(llm_output1), indent=2)
    + "\n"
)
prompt2_out.write_text(final_prompt, encoding="utf-8")
print("Saved prompt2.txt")

llm_output2 = llm_generate_nets()
draw_nets(sch, llm_output1, llm_output2)
print("Drew test wire")
