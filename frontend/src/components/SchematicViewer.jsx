import React from "react";
import { FaExpand, FaCompress, FaDownload, FaSpinner } from "react-icons/fa";
import "./SchematicViewer.css";

const SchematicViewer = ({
  svgContent,
  currentFile,
  isGenerating,
  onReset,
}) => {
  const [zoom, setZoom] = React.useState(1);
  const [isFullscreen, setIsFullscreen] = React.useState(false);

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 0.1, 3));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 0.1, 0.3));
  };

  const handleZoomReset = () => {
    setZoom(1);
  };

  const handleReset = () => {
    setZoom(1);
    if (onReset) onReset();
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleDownload = () => {
    if (svgContent) {
      const blob = new Blob([svgContent], { type: "image/svg+xml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "schematic.svg";
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className={`schematic-viewer ${isFullscreen ? "fullscreen" : ""}`}>
      <div className="viewer-header">
        <div className="viewer-title">
          {currentFile ? (
            <span>{currentFile.split("/").pop()}</span>
          ) : (
            <span>Schematic Preview</span>
          )}
        </div>

        <div className="viewer-controls">
          <button
            className="control-btn"
            onClick={handleZoomOut}
            title="Zoom Out"
            disabled={!svgContent}
          >
            -
          </button>
          <span className="zoom-level">{Math.round(zoom * 100)}%</span>
          <button
            className="control-btn"
            onClick={handleZoomIn}
            title="Zoom In"
            disabled={!svgContent}
          >
            +
          </button>
          <button
            className="control-btn"
            onClick={handleReset}
            title="Reset All"
          >
            Reset
          </button>
          <button
            className="control-btn"
            onClick={handleDownload}
            title="Download SVG"
            disabled={!svgContent}
          >
            <FaDownload />
          </button>
          <button
            className="control-btn"
            onClick={toggleFullscreen}
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? <FaCompress /> : <FaExpand />}
          </button>
        </div>
      </div>

      <div className="viewer-content">
        {isGenerating ? (
          <div className="viewer-placeholder">
            <FaSpinner className="spinner large" />
            <p>Generating schematic...</p>
          </div>
        ) : svgContent ? (
          <div
            className="svg-container"
            style={{ transform: `scale(${zoom})` }}
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        ) : (
          <div className="viewer-placeholder">
            <div className="placeholder-icon">⚡</div>
            <h3>No Schematic Loaded</h3>
            <p>
              {currentFile
                ? "Select a .kicad_sch file to view"
                : "Enter a prompt to generate a schematic"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SchematicViewer;
