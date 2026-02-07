# Cursor PCB - Frontend

Electron + React frontend for the Cursor PCB application.

## 🚀 Quick Start

```bash
# Install dependencies
npm install --legacy-peer-deps

# Run development mode
npm run dev
```

## 📦 Available Scripts

- `npm run dev` - Start Vite + Electron in development mode
- `npm run dev:vite` - Run Vite dev server only
- `npm run dev:electron` - Run Electron only (requires Vite running)
- `npm run build` - Build React app for production
- `npm run build:electron` - Package Electron app
- `npm run preview` - Preview production build

## 🏗️ Structure

```
frontend/
├── electron/
│   ├── main.js           # Electron main process
│   └── preload.js        # IPC bridge (security layer)
│
├── src/
│   ├── components/       # React components
│   │   ├── Sidebar.jsx          # File explorer
│   │   ├── PromptEditor.jsx     # Prompt input
│   │   ├── SchematicViewer.jsx  # SVG preview
│   │   └── ComponentLibrary.jsx # Component browser
│   ├── App.jsx           # Main app component
│   ├── main.jsx          # React entry point
│   └── *.css             # Styles
│
├── index.html            # HTML entry point
├── vite.config.js        # Vite configuration
└── package.json          # Dependencies
```

## 🔌 Electron IPC API

The preload script exposes these APIs to React:

```javascript
window.electronAPI.selectDirectory();
window.electronAPI.readDirectory(path);
window.electronAPI.readFile(path);
window.electronAPI.writeFile(path, content);
window.electronAPI.executePython(script, args);
window.electronAPI.generateSchematic({ prompt, projectPath });
window.electronAPI.exportSchematicSVG(schematicPath);
window.electronAPI.listComponents(libPath);
```

## 🎨 UI Components

### Sidebar

- File tree navigation
- Project folder selection
- File type filtering

### PromptEditor

- Natural language input
- Example prompts
- Keyboard shortcuts (`Cmd+Enter`)

### SchematicViewer

- SVG rendering
- Zoom controls
- Fullscreen mode
- Export functionality

### ComponentLibrary

- Component search
- Category filtering
- Drag-and-drop (future)

## 🔐 Security

The app uses Electron's security best practices:

- **Context Isolation**: Enabled
- **Node Integration**: Disabled in renderer
- **Preload Script**: Acts as IPC gatekeeper
- **CSP**: Content Security Policy ready

## 🎨 Styling

- Dark theme matching VSCode
- CSS modules per component
- Responsive layout
- Smooth transitions

## 📱 Development Tips

### Hot Reload

Changes to React components automatically reload. Electron main process requires restart.

### Debugging

- React: Chrome DevTools opens automatically in dev mode
- Electron: Use `console.log` in main.js (shows in terminal)

### Testing UI Without Electron

```bash
npm run dev:vite
# Open http://localhost:5173 in browser
# Note: electronAPI won't work, mock it in React
```

## 🔧 Configuration

### Vite Config

- Base path set to `./` for Electron
- Port: 5173
- React plugin enabled

### Electron Config

- Title bar: Hidden (macOS style)
- Min size: 1400x900
- Background: `#1e1e1e`

## 📦 Building for Production

```bash
# Build React app
npm run build

# Package Electron app (macOS/Windows/Linux)
npm run build:electron
```

Output will be in `out/` directory.

## 🐛 Troubleshooting

### "Module not found" errors

```bash
npm install --legacy-peer-deps
```

### Electron window blank

Check that Vite dev server is running on port 5173

### IPC not working

Verify preload script is loaded and context isolation is enabled

## 📚 Learn More

- [Electron Documentation](https://www.electronjs.org/docs)
- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
