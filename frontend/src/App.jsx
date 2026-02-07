import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import PromptEditor from "./components/PromptEditor";
import SchematicViewer from "./components/SchematicViewer";
import ComponentLibrary from "./components/ComponentLibrary";
import "./App.css";

function App() {
  const [projectPath, setProjectPath] = useState(null);
  const [currentFile, setCurrentFile] = useState(null);
  const [schematicSVG, setSchematicSVG] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activePanel, setActivePanel] = useState("prompt"); // 'prompt' or 'components'

  const handleSelectProject = async () => {
    if (window.electronAPI) {
      const path = await window.electronAPI.selectDirectory();
      if (path) {
        setProjectPath(path);
      }
    }
  };

  const handleGenerateSchematic = async (prompt) => {
    if (!projectPath) {
      alert("Please select a project directory first");
      return;
    }

    setIsGenerating(true);
    try {
      // Call the backend to generate schematic
      const result = await window.electronAPI.generateSchematic({
        prompt,
        projectPath,
      });

      // Export to SVG for preview
      if (currentFile) {
        const svgResult =
          await window.electronAPI.exportSchematicSVG(currentFile);
        setSchematicSVG(svgResult.svgContent);
      }

      alert("Schematic generated successfully!");
    } catch (error) {
      console.error("Error generating schematic:", error);
      alert("Error generating schematic: " + error.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFileSelect = async (filePath) => {
    setCurrentFile(filePath);

    // If it's a schematic file, export to SVG
    if (filePath.endsWith(".kicad_sch") && window.electronAPI) {
      try {
        const result = await window.electronAPI.exportSchematicSVG(filePath);
        setSchematicSVG(result.svgContent);
      } catch (error) {
        console.error("Error exporting schematic:", error);
      }
    }
  };

  return (
    <div className="app">
      <Sidebar
        projectPath={projectPath}
        onSelectProject={handleSelectProject}
        onFileSelect={handleFileSelect}
        currentFile={currentFile}
      />

      <div className="main-content">
        <div className="left-panel">
          <div className="panel-tabs">
            <button
              className={`tab ${activePanel === "prompt" ? "active" : ""}`}
              onClick={() => setActivePanel("prompt")}
            >
              Prompt
            </button>
            <button
              className={`tab ${activePanel === "components" ? "active" : ""}`}
              onClick={() => setActivePanel("components")}
            >
              Components
            </button>
          </div>

          {activePanel === "prompt" ? (
            <PromptEditor
              onGenerate={handleGenerateSchematic}
              isGenerating={isGenerating}
            />
          ) : (
            <ComponentLibrary projectPath={projectPath} />
          )}
        </div>

        <div className="right-panel">
          <SchematicViewer
            svgContent={schematicSVG}
            currentFile={currentFile}
            isGenerating={isGenerating}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
