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
  const [isGeneratingSchematic, setIsGeneratingSchematic] = useState(false);
  const [isGeneratingPCB, setIsGeneratingPCB] = useState(false);
  const [isSelectingComponents, setIsSelectingComponents] = useState(false);
  const [activePanel, setActivePanel] = useState("prompt");
  const [generatedComponents, setGeneratedComponents] = useState([]);
  const [prompt, setPrompt] = useState("");

  const handleSelectProject = async () => {
    if (window.electronAPI) {
      const path = await window.electronAPI.selectDirectory();
      if (path) {
        setProjectPath(path);
      }
    }
  };

  const handleGeneratePCB = async () => {
    if (!projectPath) {
      alert("Please select a project directory first");
      return;
    }

    setIsGeneratingPCB(true);
    try {
      const response = await fetch("http://localhost:5001/api/generate-pcb", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directory: projectPath }),
      });

      const result = await response.json();
      console.log("Generate PCB result:", result);

      if (result.success) {
        alert(result.message);
      } else {
        alert(
          result.warning
            ? result.message
            : "PCB generation failed: " + result.error,
        );
      }
    } catch (error) {
      console.error("Error generating PCB:", error);
      alert("Error generating PCB: " + error.message);
    } finally {
      setIsGeneratingPCB(false);
    }
  };

  const handleSelectComponents = async (prompt) => {
    if (!projectPath) {
      alert("Please select a project directory first");
      return;
    }

    setIsSelectingComponents(true);
    try {
      const response = await fetch(
        "http://localhost:5001/api/chat-components",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: prompt, directory: projectPath }),
        },
      );

      const result = await response.json();

      if (result.success) {
        setGeneratedComponents(result.components);
        setActivePanel("components"); // Switch to components tab
        alert(
          `Selected ${result.components.length} components. Check the Components tab to review.`,
        );
      } else {
        alert("Component selection failed: " + result.error);
      }
    } catch (error) {
      console.error("Error selecting components:", error);
      alert("Error selecting components: " + error.message);
    } finally {
      setIsSelectingComponents(false);
    }
  };

  const handleGenerateSchematic = async (prompt) => {
    if (!projectPath) {
      alert("Please select a project directory first");
      return;
    }

    setIsGeneratingSchematic(true);
    try {
      // Call Flask backend generate endpoint
      const requestBody = {
        prompt: prompt,
        directory: projectPath,
      };

      // If user has selected components, pass them to skip Phase 0
      if (generatedComponents.length > 0) {
        requestBody.selected_components = generatedComponents;
        console.log(
          "Calling generate with selected components:",
          generatedComponents.length,
        );
      }

      console.log("Calling generate with:", requestBody);

      const response = await fetch("http://localhost:5001/api/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
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
      setIsGeneratingSchematic(false);
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

  const handleReset = () => {
    setSchematicSVG(null);
    setPrompt("");
    setGeneratedComponents([]);
    setCurrentFile(null);
  };

  const handleRemoveComponent = (componentToRemove) => {
    setGeneratedComponents((prev) =>
      prev.filter(
        (c) =>
          !(
            c.symbol === componentToRemove.symbol &&
            c.ref_des === componentToRemove.ref_des
          ),
      ),
    );
  };

  const handleAddComponent = (componentToAdd) => {
    const exists = generatedComponents.some(
      (c) => c.symbol === componentToAdd.symbol && c.lib === componentToAdd.lib,
    );
    if (!exists) {
      setGeneratedComponents((prev) => [...prev, componentToAdd]);
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
              onGeneratePCB={handleGeneratePCB}
              onSelectComponents={handleSelectComponents}
              isGeneratingSchematic={isGeneratingSchematic}
              isGeneratingPCB={isGeneratingPCB}
              isSelectingComponents={isSelectingComponents}
              prompt={prompt}
              setPrompt={setPrompt}
            />
          ) : (
            <ComponentLibrary
              projectPath={projectPath}
              components={generatedComponents}
              onRemoveComponent={handleRemoveComponent}
              onAddComponent={handleAddComponent}
            />
          )}
        </div>

        <div className="right-panel">
          <SchematicViewer
            svgContent={schematicSVG}
            currentFile={currentFile}
            isGenerating={isGeneratingSchematic}
            onReset={handleReset}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
