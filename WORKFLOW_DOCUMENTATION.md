# Cursor PCB - Current Workflow Documentation

## 📋 Overview

Your system generates KiCAD schematics through a **3-phase LLM workflow** with pin mapping in between.

## 🔄 Complete Workflow

```
User Prompt
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Component Selection & Placement                    │
└─────────────────────────────────────────────────────────────┘
    │
    ├─→ Input: User prompt + allow_list.json
    ├─→ LLM: Reads prompt1.txt instructions
    ├─→ Output: llm_output1.json (components WITHOUT pins)
    │
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Physical Placement                                 │
└─────────────────────────────────────────────────────────────┘
    │
    ├─→ place_from_llm_output() places symbols in .kicad_sch
    ├─→ Reads KiCAD library files for each component
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Pin Discovery & Mapping                            │
└─────────────────────────────────────────────────────────────┘
    │
    ├─→ add_pin_outs() extracts pin info from KiCAD libraries
    ├─→ Calculates world coordinates for each pin
    ├─→ Output: llm_output1_with_pins.json
    │
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Generate Prompt for Netlist                        │
└─────────────────────────────────────────────────────────────┘
    │
    ├─→ Combines prompt2_instructions.txt + llm_output1_with_pins
    ├─→ Simplifies pin format (only pin names, not coordinates)
    ├─→ Output: prompt2.txt (for LLM to read)
    │
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: Netlist Generation                                 │
└─────────────────────────────────────────────────────────────┘
    │
    ├─→ Input: prompt2.txt
    ├─→ LLM: Generates connections between pins
    ├─→ Output: llm_output2.json (netlist)
    │
    ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: Wire Drawing                                       │
└─────────────────────────────────────────────────────────────┘
    │
    ├─→ draw_nets() reads llm_output2.json
    ├─→ Uses pin coordinates from llm_output1_with_pins.json
    ├─→ Draws wires in .kicad_sch file
    │
    ↓
  DONE: Complete schematic with components and wires
```

## 📂 File Roles

### Input Files

- **User Prompt** - Natural language circuit description
- **allow_list.json** - Whitelist of allowed components
- **prompt1.txt** - LLM instructions for component selection
- **prompt2_instructions.txt** - LLM instructions for netlist generation

### Intermediate Files

- **llm_output1.json** - Component list WITHOUT pin data
- **llm_output1_with_pins.json** - Component list WITH pin data
- **prompt2.txt** - Generated prompt for netlist LLM call

### Output Files

- **llm_output2.json** - Netlist (connections between pins)
- **test.kicad_sch** - Final KiCAD schematic file

## 🔍 Detailed Phase Breakdown

### Phase 1: Component Selection (LLM)

**What happens:**

- LLM receives user prompt + allow_list.json
- Follows rules in prompt1.txt
- Selects components from allowlist
- Assigns reference designators (U1, R1, C1, etc.)
- Places components at X,Y coordinates
- Chooses footprints

**Output structure (llm_output1.json):**

```json
{
  "circuit_intent": { ... },
  "symbols": [
    {
      "lib": "Device.kicad_sym",
      "symbol": "R",
      "ref_des": "R1",
      "value": "10k",
      "at": { "x": 100, "y": 50, "rot": 0 },
      "footprint": "Resistor_SMD:R_0603_1608Metric",
      "explanation": "Pull-up resistor for..."
    }
  ]
}
```

### Phase 2: Physical Placement (Python)

**What happens (run_schematic.py lines 21-23):**

```python
llm_output1 = llm_generate_plan()
place_from_llm_output(sch, symbol_lib, llm_output1)
print(f"Placed components in schematic file {sch}")
```

**Actions:**

1. Reads llm_output1.json
2. For each symbol:
   - Opens KiCAD library file
   - Extracts symbol definition
   - Places at specified coordinates
   - Writes to .kicad_sch file

### Phase 3: Pin Discovery (Python)

**What happens (run_schematic.py lines 25-29):**

```python
llm_output1 = add_pin_outs(symbol_lib, llm_output1)
out_file = Path("llm_output1_with_pins.json")
with out_file.open("w", encoding="utf-8") as f:
    json.dump(llm_output1, f, indent=2)
```

**Actions:**

1. For each placed symbol:
   - Parses KiCAD library to find pin definitions
   - Extracts pin numbers and names
   - Calculates world coordinates (considering rotation)
   - Adds "pins" field to each symbol

**Output structure (llm_output1_with_pins.json):**

```json
{
  "symbols": [
    {
      "ref_des": "U1",
      "pins": {
        "1": {
          "name": "VDD",
          "pos": [150.5, 100.2, 0]
        },
        "2": {
          "name": "GND",
          "pos": [150.5, 102.8, 180]
        }
      }
    }
  ]
}
```

### Phase 4: Prompt Generation (Python)

**What happens (run_schematic.py lines 31-42):**

```python
prompt2_template = Path("prompt2_instructions.txt")
base_prompt = prompt2_template.read_text(encoding="utf-8")
final_prompt = (
    base_prompt.rstrip()
    + "\n\n"
    + "Here is the component list JSON:\n\n"
    + json.dumps(simplify_pins_for_llm(llm_output1), indent=2)
)
prompt2_out.write_text(final_prompt, encoding="utf-8")
```

**Actions:**

1. Reads prompt2_instructions.txt (netlist instructions)
2. Simplifies pin format (removes coordinates, keeps only names)
3. Appends component list to instructions
4. Saves as prompt2.txt

**Why simplify pins?**

```python
def simplify_pins_for_llm(llm_output):
    # Before: {"1": {"name": "VDD", "pos": [150.5, 100.2, 0]}}
    # After:  {"1": "VDD"}
    # LLM doesn't need coordinates, just pin names
```

### Phase 5: Netlist Generation (LLM)

**What happens (run_schematic.py line 44):**

```python
llm_output2 = llm_generate_nets()
```

**Actions:**

1. LLM reads prompt2.txt
2. Sees all components and their pins
3. Generates connections between pins
4. Outputs netlist as JSON

**Output structure (llm_output2.json):**

```json
{
  "nets": [
    {
      "name": "NET_3V3",
      "connections": [
        { "ref": "U1", "pin": "2" },
        { "ref": "C1", "pin": "1" },
        { "ref": "R1", "pin": "1" }
      ]
    }
  ]
}
```

### Phase 6: Wire Drawing (Python)

**What happens (run_schematic.py lines 45-46):**

```python
draw_nets(sch, llm_output1, llm_output2)
print("Drew test wire")
```

**Actions:**

1. Reads llm_output2.json (netlist)
2. For each net:
   - Looks up pin coordinates from llm_output1_with_pins
   - Draws wire from pin to pin
   - Writes wire definitions to .kicad_sch

## 🎯 Key Design Decisions

### Why Two Separate LLM Calls?

**Problem:** LLMs can't know pin positions until components are placed

**Solution:** Two-phase approach:

1. **Phase 1:** Select components (LLM doesn't know pins yet)
2. **Pin Mapping:** Python extracts pin info from libraries
3. **Phase 5:** Generate connections (LLM now knows all pins)

### Why llm_output1_with_pins.json?

**Purpose:** Bridge between component placement and netlist generation

**Contains:**

- Everything from llm_output1.json
- PLUS pin definitions with world coordinates

**Used by:**

- Phase 4: Prompt generation (simplified version)
- Phase 6: Wire drawing (full version with coordinates)

### Why simplify_pins_for_llm()?

**Problem:** Pin coordinates are huge and confusing for LLM

**Before:**

```json
"pins": {
  "1": {"name": "VDD", "pos": [150.5, 100.2, 0]},
  "2": {"name": "GND", "pos": [150.5, 102.8, 180]}
}
```

**After:**

```json
"pins": {
  "1": "VDD",
  "2": "GND"
}
```

**Result:** LLM sees clean pin names, makes better connections

## 🔄 Data Transformations

```
allow_list.json (whitelist)
    ↓
llm_output1.json (components)
    ↓
llm_output1_with_pins.json (components + pins)
    ↓ (simplified)
prompt2.txt (instructions + component list)
    ↓
llm_output2.json (netlist)
    ↓
test.kicad_sch (final schematic)
```

## 💡 Current Workflow Logic (run_schematic.py)

Line by line explanation:

```python
# Lines 21-23: PHASE 1 & 2
llm_output1 = llm_generate_plan()              # Call LLM for components
place_from_llm_output(sch, symbol_lib, llm_output1)  # Place in schematic
print(f"Placed components in schematic file {sch}")

# Lines 25-29: PHASE 3
llm_output1 = add_pin_outs(symbol_lib, llm_output1)  # Add pin data
out_file = Path("llm_output1_with_pins.json")
with out_file.open("w", encoding="utf-8") as f:
    json.dump(llm_output1, f, indent=2)        # Save with pins
print(f"Wrote pin data to {out_file}")

# Lines 31-42: PHASE 4
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
prompt2_out.write_text(final_prompt, encoding="utf-8")  # Generate prompt2
print("Saved prompt2.txt")

# Lines 44-46: PHASE 5 & 6
llm_output2 = llm_generate_nets()              # Call LLM for netlist
draw_nets(sch, llm_output1, llm_output2)       # Draw wires
print("Drew test wire")
```

## 🎨 Visual Flow

```
┌─────────────┐
│ User Prompt │
└──────┬──────┘
       │
       ├─→ allow_list.json
       │
       ↓
┌──────────────┐
│ LLM Call #1  │ prompt1.txt
└──────┬───────┘
       │
       ↓
   llm_output1.json
   (no pins)
       │
       ├─→ place_from_llm_output()
       │   └─→ test.kicad_sch (components only)
       │
       ├─→ add_pin_outs()
       │
       ↓
   llm_output1_with_pins.json
   (with pins)
       │
       ├─→ simplify_pins_for_llm()
       │
       ↓
   prompt2.txt
       │
       ↓
┌──────────────┐
│ LLM Call #2  │ prompt2_instructions.txt
└──────┬───────┘
       │
       ↓
   llm_output2.json
   (netlist)
       │
       ├─→ draw_nets()
       │
       ↓
   test.kicad_sch
   (complete with wires)
```

## 🚀 Next Steps for Frontend Integration

To integrate this into your Electron frontend:

1. **User enters prompt in UI**
2. **Frontend calls backend script**
3. **Backend runs run_schematic.py**
4. **Return status updates to frontend**
5. **Display schematic SVG when complete**

See: `frontend/electron/main.js` for IPC handlers to connect to this workflow.

---

This workflow is well-designed for LLM-driven PCB generation! The two-phase approach (components → pins → netlist) is necessary because pin information isn't available until after library parsing.
