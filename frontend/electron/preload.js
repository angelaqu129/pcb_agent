const { contextBridge, ipcRenderer } = require("electron");

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld("electronAPI", {
  selectDirectory: () => ipcRenderer.invoke("select-directory"),
  readDirectory: (dirPath) => ipcRenderer.invoke("read-directory", dirPath),
  readFile: (filePath) => ipcRenderer.invoke("read-file", filePath),
  writeFile: (filePath, content) =>
    ipcRenderer.invoke("write-file", filePath, content),
  executePython: (scriptPath, args) =>
    ipcRenderer.invoke("execute-python", scriptPath, args),
  generateSchematic: (data) => ipcRenderer.invoke("generate-schematic", data),
  exportSchematicSVG: (schematicPath) =>
    ipcRenderer.invoke("export-schematic-svg", schematicPath),
  listComponents: (libPath) => ipcRenderer.invoke("list-components", libPath),
});
