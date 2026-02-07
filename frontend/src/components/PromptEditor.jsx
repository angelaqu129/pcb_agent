import React, { useState } from "react";
import { FaPlay, FaSpinner } from "react-icons/fa";
import "./PromptEditor.css";

const PromptEditor = ({ onGenerate, onGeneratePCB, isGenerating }) => {
  const [prompt, setPrompt] = useState("");

  const handleGenerate = () => {
    if (prompt.trim() && !isGenerating) {
      onGenerate(prompt);
    }
  };

  const handleGeneratePCB = () => {
    if (prompt.trim() && !isGenerating && onGeneratePCB) {
      onGeneratePCB(prompt);
    }
  };

  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      handleGenerate();
    }
  };

  const examplePrompts = [
    "Create a simple LED blink circuit with an Arduino Uno, resistor, and LED",
    "Design a voltage divider circuit with two resistors",
    "Build an audio amplifier using an LM386 IC",
    "Create a 555 timer circuit in astable mode",
  ];

  return (
    <div className="prompt-editor">
      <div className="prompt-header">
        <h3>Describe Your PCB</h3>
        <div className="button-group">
          <button
            className="generate-btn"
            onClick={handleGenerate}
            disabled={isGenerating || !prompt.trim()}
          >
            {isGenerating ? (
              <>
                <FaSpinner className="spinner" />
                Generating...
              </>
            ) : (
              <>
                <FaPlay />
                Generate Schematic
              </>
            )}
          </button>
          <button
            className="generate-btn generate-pcb-btn"
            onClick={handleGeneratePCB}
            disabled={isGenerating || !prompt.trim()}
          >
            <FaPlay />
            Generate PCB
          </button>
        </div>
      </div>

      <div className="prompt-input-container">
        <textarea
          className="prompt-textarea"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe the PCB circuit you want to create...

Example:
• Create a simple LED blink circuit with Arduino
• Design a 5V power regulator using LM7805
• Build a temperature sensor circuit with DHT22

Press Cmd+Enter to generate"
          disabled={isGenerating}
        />
      </div>

      <div className="examples-section">
        <h4>Example Prompts</h4>
        <div className="example-list">
          {examplePrompts.map((example, index) => (
            <div
              key={index}
              className="example-item"
              onClick={() => !isGenerating && setPrompt(example)}
            >
              {example}
            </div>
          ))}
        </div>
      </div>

      <div className="tips-section">
        <h4>Tips</h4>
        <ul>
          <li>Be specific about components you want to use</li>
          <li>Mention voltage levels and ratings if important</li>
          <li>Describe the connections between components</li>
          <li>Include any special requirements or constraints</li>
        </ul>
      </div>
    </div>
  );
};

export default PromptEditor;
