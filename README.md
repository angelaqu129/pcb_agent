# AI Agent for PCB

An AI-powered PCB design assistant inspired by Cursor IDE. Describe your circuit in natural language and watch it generate KiCAD schematics automatically.

## 🏗️ Project Structure

```
kicad-test/
├── frontend/              # Electron + React frontend
│   ├── electron/          # Electron main process
│   ├── src/               # React components
│   ├── package.json       # Frontend dependencies
│   ├── vite.config.js     # Vite configuration
│   └── index.html         # Entry HTML
│
├── schematic.py           # KiCAD schematic generator (Python backend)
├── run_schematic.py       # Script to run schematic generation
├── pcb.py                 # PCB layout utilities
├── allow_list.json        # Component whitelist
├── llm_output1.json       # LLM-generated component placements
├── llm_output2.json       # LLM-generated net connections
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.8+
- **KiCAD** 7.0+ (with `kicad-cli` in PATH)

### Installation & Running

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Run the application
npm run dev
```

The Electron app will launch automatically with the React UI.

## 📖 How It Works

### Architecture Overview

```
User Prompt → React UI → Electron IPC → Python Backend → KiCAD Files → SVG Preview
```

1. **User writes a prompt** describing their circuit
2. **React frontend** sends it via Electron IPC
3. **Python backend** generates component list and connections
4. **KiCAD files** are updated with new symbols and wires
5. **SVG preview** is rendered in the UI

### Backend (Python)

The Python backend handles KiCAD file manipulation:

- `schematic.py` - Main schematic generation logic
  - `place_symbol()` - Places components at coordinates
  - `draw_wire()` - Connects pins with wires
  - `add_lib_symbol()` - Imports symbols from libraries
  - `get_pin_xy()` - Calculates pin positions

### Frontend (Electron + React)

The frontend provides the user interface:

- **Electron** - Desktop app with file system access
- **React** - Modern UI components
- **Vite** - Fast build tool and dev server

## 💡 Features

- ✍️ **Natural Language Input** - Describe circuits in plain English
- 📁 **File System Access** - Direct access to local KiCAD libraries
- 👀 **Live Preview** - Real-time schematic visualization
- 🔍 **Component Browser** - Search and explore available parts
- 🎨 **Modern UI** - VSCode-inspired dark theme

## 🛠️ Development

### Frontend Development

```bash
cd frontend
npm run dev          # Run dev server with hot reload
npm run build        # Build for production
npm run preview      # Preview production build
```

### Backend Development

The Python backend is in the root directory. Test it directly:

```bash
python3 schematic.py
```

### Project Commands

From the `frontend` directory:

- `npm run dev` - Start development mode
- `npm run dev:vite` - Run Vite only (without Electron)
- `npm run dev:electron` - Run Electron only
- `npm run build` - Build React app
- `npm run build:electron` - Package Electron app

## 🎯 Usage

1. **Launch the app**: `cd frontend && npm run dev`
2. **Open a project**: Click "Open Folder" to select your KiCAD project
3. **Write a prompt**: Describe your circuit (e.g., "LED blink circuit with Arduino")
4. **Generate**: Click "Generate" or press `Cmd+Enter`
5. **View result**: See the schematic in the preview panel

### Example Prompts

```
Create a simple LED blink circuit with an Arduino Uno,
a 220Ω resistor, and an LED

Design a 5V voltage regulator using LM7805 with
input/output capacitors

Build a temperature sensor circuit with DHT22
connected to Arduino pins
```

## 🔮 Roadmap

- [ ] Integrate LLM API (OpenAI/Anthropic)
- [ ] Add component footprint selection
- [ ] Generate PCB layouts from schematics
- [ ] Support multi-sheet designs
- [ ] BOM (Bill of Materials) generation
- [ ] Real-time collaboration
- [ ] DRC (Design Rule Check) integration
- [ ] Export to manufacturing formats

## 📚 Tech Stack

### Frontend

- Electron 33.0+
- React 18.2+
- Vite 6.0+
- React Icons

### Backend

- Python 3.8+
- KiCAD 7.0+

