# 🤖 PCB Agent - Setup Guide

Complete guide to setting up and using the automated PCB schematic generation agent.

## 📋 Overview

The PCB Agent automates your workflow using **Dedalus SDK** to orchestrate LLM calls and Python functions. It runs Phases 1-5 and stops before wire drawing (Phase 6).

```
User Prompt → Agent → llm_output2.json (STOP HERE)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-agent.txt
```

Or manually:

```bash
pip install dedalus-labs python-dotenv
```

### 2. Get Dedalus API Key

1. Go to: https://dedaluslabs.ai/dashboard
2. Sign up or log in
3. Navigate to "API Keys"
4. Create a new API key
5. Copy the key

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```bash
DEDALUS_API_KEY=your-actual-api-key-here
PCB_AGENT_VERBOSE=1
```

### 4. Test Setup

```bash
python test_agent.py
```

This will:

- ✅ Check API key
- ✅ Verify required files exist
- ✅ Initialize agent
- ✅ (Optional) Run a test prompt

### 5. Run the Agent

```bash
# Command line usage
python pcb_agent.py "Create a simple ESP32 circuit"

# Or use in your own code
python
>>> from pcb_agent import PCBAgent
>>> agent = PCBAgent(verbose=True)
>>> result = await agent.generate_schematic("Your prompt here")
```

## 📂 Required Files

Make sure these files exist in your project:

- ✅ `allow_list.json` - Component whitelist
- ✅ `prompt1.txt` - Phase 1 LLM instructions
- ✅ `prompt2_instructions.txt` - Phase 5 LLM instructions
- ✅ `schematic.py` - Python functions for KiCAD manipulation
- ✅ `.env` - API key configuration

## 🔧 Configuration

### Custom Paths

```python
agent = PCBAgent(
    allow_list_path="custom/allow_list.json",
    symbol_lib_path="/custom/path/to/kicad/symbols/",
    prompt1_path="custom/prompt1.txt",
    prompt2_instructions_path="custom/prompt2_instructions.txt",
    verbose=True
)
```

### Different LLM Models

```python
result = await agent.generate_schematic(
    user_prompt="Create an ESP32 circuit",
    model="openai/gpt-4o"  # or anthropic/claude-3-5-sonnet-20241022
)
```

### Custom Schematic Path

```python
result = await agent.generate_schematic(
    user_prompt="Your prompt",
    schematic_path="./my_project/board.kicad_sch"
)
```

## 📊 What the Agent Does

### Phase 1: Component Selection (LLM)

```
Input: User prompt + allow_list.json + prompt1.txt
Output: llm_output1.json (components without pins)
```

**Example output:**

```json
{
  "circuit_intent": {...},
  "symbols": [
    {"ref_des": "U1", "symbol": "ESP32-C3", ...},
    {"ref_des": "C1", "symbol": "C", "value": "0.1uF", ...}
  ]
}
```

### Phase 2: Component Placement (Python)

```
Input: llm_output1.json
Action: place_from_llm_output() adds symbols to .kicad_sch
Output: test.kicad_sch (partial)
```

### Phase 3: Pin Mapping (Python)

```
Input: llm_output1.json + KiCAD libraries
Action: add_pin_outs() extracts pin info
Output: llm_output1_with_pins.json
```

**Example output:**

```json
{
  "symbols": [
    {
      "ref_des": "U1",
      "pins": {
        "1": { "name": "VDD", "pos": [150.5, 100.2, 0] },
        "2": { "name": "GND", "pos": [150.5, 102.8, 180] }
      }
    }
  ]
}
```

### Phase 4: Prompt Generation (Python)

```
Input: llm_output1_with_pins.json + prompt2_instructions.txt
Action: Simplifies pins, combines with instructions
Output: prompt2.txt
```

### Phase 5: Netlist Generation (LLM)

```
Input: prompt2.txt
Output: llm_output2.json (connections)
```

**Example output:**

```json
{
  "nets": [
    {
      "name": "NET_3V3",
      "connections": [
        { "ref": "U1", "pin": "2" },
        { "ref": "C1", "pin": "1" }
      ]
    }
  ]
}
```

### Agent STOPS Here ✋

Phase 6 (wire drawing) is NOT executed. You must run it manually if needed:

```python
from schematic import draw_nets
import json

llm_output1 = json.load(open("llm_output1_with_pins.json"))
llm_output2 = json.load(open("llm_output2.json"))

draw_nets("test.kicad_sch", llm_output1, llm_output2)
```

## 🎯 Return Value Structure

```python
{
    "status": "success",  # or "error"
    "phases_completed": 5,
    "components": [...],  # List of symbols
    "nets": [...],        # List of connections
    "files": {
        "schematic": "test.kicad_sch",
        "output1": "llm_output1.json",
        "output1_with_pins": "llm_output1_with_pins.json",
        "prompt2": "prompt2.txt",
        "output2": "llm_output2.json"
    },
    "message": "Schematic generation complete..."
}
```

## 🐛 Troubleshooting

### Error: "DEDALUS_API_KEY not found"

**Solution:**

```bash
# Create .env file
echo "DEDALUS_API_KEY=your-key-here" > .env

# Or set environment variable
export DEDALUS_API_KEY=your-key-here
```

### Error: "Component not in allowlist"

**Solution:**

- Check `allow_list.json` for available components
- Modify your prompt to use allowed components only
- Or add new components to allowlist

### Error: "KiCAD library not found"

**Solution:**

```python
# Specify custom path
agent = PCBAgent(
    symbol_lib_path="/your/kicad/installation/symbols/"
)
```

**Common paths:**

- macOS: `/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/`
- Linux: `/usr/share/kicad/symbols/`
- Windows: `C:\Program Files\KiCad\share\kicad\symbols\`

### Error: "LLM returned invalid JSON"

**Solution:**

- Check your prompt for clarity
- Ensure prompt instructions are complete
- Try a different model
- Check Dedalus API status

### Verbose Logging

Enable detailed logs to debug:

```python
agent = PCBAgent(verbose=True)
```

Or set environment variable:

```bash
export PCB_AGENT_VERBOSE=1
```

## 💡 Usage Examples

### Basic Usage

```python
import asyncio
from pcb_agent import PCBAgent

async def main():
    agent = PCBAgent()
    result = await agent.generate_schematic(
        "Create an ESP32-C3 circuit with power supply"
    )
    print(f"Status: {result['status']}")
    print(f"Components: {len(result['components'])}")

asyncio.run(main())
```

### With Error Handling

```python
async def main():
    agent = PCBAgent(verbose=True)

    try:
        result = await agent.generate_schematic(
            "Your circuit description here"
        )

        if result["status"] == "success":
            print("✅ Success!")
            print(f"Generated {len(result['nets'])} nets")
        else:
            print(f"❌ Failed: {result['error']}")

    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
```

### Multiple Circuits

```python
async def main():
    agent = PCBAgent()

    circuits = [
        "ESP32 with LED",
        "Temperature sensor with display",
        "Power regulator circuit"
    ]

    for i, prompt in enumerate(circuits):
        result = await agent.generate_schematic(
            user_prompt=prompt,
            schematic_path=f"circuit_{i}.kicad_sch"
        )
        print(f"Circuit {i}: {result['status']}")

asyncio.run(main())
```

## 🔗 Integration with Frontend

To integrate with your Electron frontend:

### 1. Add IPC Handler in `electron/main.js`:

```javascript
ipcMain.handle("run-agent", async (event, { prompt }) => {
  return new Promise((resolve, reject) => {
    const python = spawn("python3", ["pcb_agent.py", prompt]);

    let stdout = "";
    python.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    python.on("close", (code) => {
      if (code === 0) {
        resolve(JSON.parse(stdout));
      } else {
        reject(new Error(`Agent failed with code ${code}`));
      }
    });
  });
});
```

### 2. Call from React:

```javascript
const result = await window.electronAPI.runAgent({
  prompt: userPrompt,
});

if (result.status === "success") {
  console.log("Agent completed successfully!");
  // Display schematic, etc.
}
```

## 📚 Architecture

```
PCBAgent
├── __init__()          Initialize with paths and API key
├── generate_schematic() Main entry point, runs phases 1-5
├── _phase1_component_selection()  Call LLM for components
├── _phase4_generate_prompt()      Generate prompt2.txt
├── _phase5_netlist_generation()   Call LLM for netlist
└── _simplify_pins_for_llm()       Helper function
```

## 🎨 Customization

### Add Custom Logging

```python
class CustomPCBAgent(PCBAgent):
    def log(self, message, phase=None):
        # Custom logging logic
        with open("agent.log", "a") as f:
            f.write(f"{phase}: {message}\n")
```

### Modify LLM Parameters

Edit `pcb_agent.py` and modify the `runner.run()` calls:

```python
response = await self.runner.run(
    input=prompt,
    model=model,
    response_format={"type": "json_object"},
    temperature=0.7,  # Add this
    max_tokens=4000   # Add this
)
```

## 🔐 Security Notes

- ⚠️ Never commit your `.env` file with API keys
- ✅ Add `.env` to `.gitignore`
- ✅ Use `.env.example` as template
- ✅ Rotate API keys periodically

## 📦 Dependencies

```
dedalus-labs    # LLM orchestration SDK
python-dotenv   # Environment variable management
asyncio         # Async/await support (built-in)
```

Your existing dependencies from `schematic.py` are also required.

## 🚀 Next Steps

After the agent completes:

1. **Review outputs:**
   - Check `llm_output1.json` for component selection
   - Check `llm_output2.json` for netlist accuracy

2. **Run Phase 6 manually** (if needed):

   ```python
   from schematic import draw_nets
   draw_nets("test.kicad_sch", llm_output1, llm_output2)
   ```

3. **Open in KiCAD:**

   ```bash
   open test.kicad_sch
   # Or: kicad test.kicad_sch
   ```

4. **Export SVG:**
   ```bash
   kicad-cli sch export svg --output schematic.svg test.kicad_sch
   ```

## 💬 Support

- **Documentation:** This file + WORKFLOW_DOCUMENTATION.md
- **Test Script:** `python test_agent.py`
- **Dedalus Docs:** https://docs.dedaluslabs.ai/
- **Issues:** Check logs with `verbose=True`

---

**Happy automated PCB designing! 🎉**
