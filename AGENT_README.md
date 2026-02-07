# Cursor PCB - Automated Agent System

This system automates Phases 1-6 of the PCB schematic generation workflow using Dedalus SDK.

## Installation

```bash
pip install dedalus-labs python-dotenv
```

## Configuration

Create a `.env` file in the project root:

```bash
DEDALUS_API_KEY=your-api-key-here
```

Get your API key from: https://dedaluslabs.ai/dashboard

## Usage

```python
from pcb_agent import PCBAgent

# Initialize agent
agent = PCBAgent()

# Run complete workflow (Phases 1-5)
result = await agent.generate_schematic(
    user_prompt="Create a simple ESP32-C3 circuit",
    schematic_path="./test.kicad_sch"
)

print(f"Status: {result['status']}")
print(f"Component count: {len(result['components'])}")
print(f"Net count: {len(result['nets'])}")
```

## What It Does

1. **Phase 1**: LLM selects components from allowlist
2. **Phase 2**: Places components in KiCAD schematic
3. **Phase 3**: Extracts pin information from libraries
4. **Phase 4**: Generates prompt for netlist LLM
5. **Phase 5**: LLM generates netlist connections
6. **Phase 6**: Draws wires between component pins

Complete schematic with wires generated automatically!

## Files Generated

- `llm_output1.json` - Component list without pins
- `llm_output1_with_pins.json` - Component list with pin data
- `prompt2.txt` - Generated prompt for netlist LLM
- `llm_output2.json` - Final netlist connections
- `test.kicad_sch` - **Complete KiCAD schematic with wires**

## Command Line Usage

```bash
python pcb_agent.py "Create an ESP32 circuit"
```

## Advanced Usage

```python
# With custom paths
agent = PCBAgent(
    allow_list_path="./allow_list.json",
    symbol_lib_path="/Applications/KiCad/..."
)

# Stream progress updates
async for update in agent.generate_schematic_stream(prompt):
    print(f"Phase {update.phase}: {update.message}")
```

## Error Handling

The agent will raise descriptive errors if:

- Component not in allowlist
- KiCAD library not found
- LLM returns invalid JSON
- Pin extraction fails

## Logging

Enable verbose logging:

```python
agent = PCBAgent(verbose=True)
```

Or set environment variable:

```bash
export PCB_AGENT_VERBOSE=1
```

## Architecture

```
PCBAgent
├── Phase1Agent (component selection)
├── PlacementEngine (KiCAD file manipulation)
├── PinMappingEngine (library parsing)
├── PromptGenerator (prompt2 creation)
└── Phase5Agent (netlist generation)
```

## Next Steps

After this agent completes:

- Review `llm_output2.json` for netlist accuracy
- Open schematic in KiCAD: `open test.kicad_sch`
- Export to SVG: `kicad-cli sch export svg --output sch.svg test.kicad_sch`
- The schematic is complete and ready to use!

## Troubleshooting

**Error: "API key not found"**

- Set `DEDALUS_API_KEY` in `.env` file

**Error: "Component not in allowlist"**

- Check `allow_list.json` for available components
- Update allowlist or modify prompt

**Error: "KiCAD library not found"**

- Verify `symbol_lib_path` points to KiCAD symbols directory
- Default: `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/`
