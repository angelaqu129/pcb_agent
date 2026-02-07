const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const fs = require("fs").promises;
const { spawn } = require("child_process");

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
    },
    titleBarStyle: "hiddenInset",
    backgroundColor: "#1e1e1e",
  });

  // Load from Vite dev server in development, from built files in production
  const isDev = !app.isPackaged;

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, "../dist/index.html"));
  }
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC Handlers

// Select project directory
ipcMain.handle("select-directory", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openDirectory"],
  });

  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

// Read directory contents
ipcMain.handle("read-directory", async (event, dirPath) => {
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    return entries.map((entry) => ({
      name: entry.name,
      path: path.join(dirPath, entry.name),
      isDirectory: entry.isDirectory(),
    }));
  } catch (error) {
    console.error("Error reading directory:", error);
    throw error;
  }
});

// Read file contents
ipcMain.handle("read-file", async (event, filePath) => {
  try {
    const content = await fs.readFile(filePath, "utf-8");
    return content;
  } catch (error) {
    console.error("Error reading file:", error);
    throw error;
  }
});

// Write file contents
ipcMain.handle("write-file", async (event, filePath, content) => {
  try {
    await fs.writeFile(filePath, content, "utf-8");
    return { success: true };
  } catch (error) {
    console.error("Error writing file:", error);
    throw error;
  }
});

// Execute Python script
ipcMain.handle("execute-python", async (event, scriptPath, args = []) => {
  return new Promise((resolve, reject) => {
    const python = spawn("python3", [scriptPath, ...args]);

    let stdout = "";
    let stderr = "";

    python.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    python.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    python.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(`Python script exited with code ${code}: ${stderr}`));
      } else {
        resolve({ stdout, stderr });
      }
    });
  });
});

// Generate schematic from prompt
ipcMain.handle("generate-schematic", async (event, { prompt, projectPath }) => {
  try {
    // Call LLM API or Python script to generate schematic
    // This is a placeholder - you'll integrate with your actual backend
    const result = await spawn("python3", [
      path.join(projectPath, "run_schematic.py"),
      prompt,
    ]);

    return { success: true, result };
  } catch (error) {
    console.error("Error generating schematic:", error);
    throw error;
  }
});

// Export schematic as SVG using kicad-cli
ipcMain.handle("export-schematic-svg", async (event, schematicPath) => {
  return new Promise((resolve, reject) => {
    const outputPath = schematicPath.replace(".kicad_sch", ".svg");
    const kicad = spawn("kicad-cli", [
      "sch",
      "export",
      "svg",
      "--output",
      outputPath,
      schematicPath,
    ]);

    let stderr = "";

    kicad.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    kicad.on("close", async (code) => {
      if (code !== 0) {
        reject(new Error(`kicad-cli exited with code ${code}: ${stderr}`));
      } else {
        try {
          const svgContent = await fs.readFile(outputPath, "utf-8");
          resolve({ svgContent, svgPath: outputPath });
        } catch (error) {
          reject(error);
        }
      }
    });
  });
});

// List available components from KiCAD libraries
ipcMain.handle("list-components", async (event, libPath) => {
  try {
    // Parse KiCAD library file and extract component list
    const content = await fs.readFile(libPath, "utf-8");
    const symbolMatches = [...content.matchAll(/\(symbol\s+"([^"]+)"/g)];
    const symbols = symbolMatches.map((match) => match[1]);
    return symbols;
  } catch (error) {
    console.error("Error listing components:", error);
    throw error;
  }
});
