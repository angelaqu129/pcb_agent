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
  const [activePanel, setActivePanel] = useState("prompt");
  const [generatedComponents, setGeneratedComponents] = useState([]);

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
      // Call Flask backend generate endpoint
      console.log("Calling generate with:", { prompt, directory: projectPath });

      const response = await fetch("http://localhost:5001/api/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: prompt,
          directory: projectPath, // ← Pass directory path
        }),
      });

      const result = await response.json();
      console.log("Generate result:", result);

      if (result.success || result.status === "success") {
        const componentCount = result.components?.length || 0;
        const netCount = result.nets?.length || 0;

        // Store generated components
        setGeneratedComponents(result.components || []);

        // Render schematic using kicad-cli
        const schematicPath = result.files?.schematic || result.schematic_path;

        if (schematicPath) {
          const svgResponse = await fetch(
            "http://localhost:5001/api/render-schematic",
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ schematic_path: schematicPath }),
            },
          );

          const svgResult = await svgResponse.json();

          if (svgResult.success) {
            setSchematicSVG(svgResult.svg_content);
            setCurrentFile(schematicPath);
            console.log("Schematic rendered and displayed!");
          } else {
            console.error("SVG render failed:", svgResult.error);
          }
        } else {
          console.warn("No schematic path found in result");
        }

        alert(
          `Schematic generated successfully!\nComponents: ${componentCount}\nNets: ${netCount}`,
        );
      } else {
        alert("Generation failed: " + (result.error || result.message));
      }
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
            <ComponentLibrary
              projectPath={projectPath}
              components={generatedComponents}
            />
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
