import React, { useState, useEffect } from "react";
import {
  FaFolder,
  FaFile,
  FaChevronRight,
  FaChevronDown,
} from "react-icons/fa";
import "./Sidebar.css";

const Sidebar = ({
  projectPath,
  onSelectProject,
  onFileSelect,
  currentFile,
}) => {
  const [files, setFiles] = useState([]);
  const [expandedDirs, setExpandedDirs] = useState(new Set());

  useEffect(() => {
    if (projectPath && window.electronAPI) {
      loadDirectory(projectPath);
    }
  }, [projectPath]);

  const loadDirectory = async (dirPath) => {
    try {
      const entries = await window.electronAPI.readDirectory(dirPath);
      setFiles(entries);
    } catch (error) {
      console.error("Error loading directory:", error);
    }
  };

  const toggleDirectory = async (dirPath) => {
    const newExpanded = new Set(expandedDirs);
    if (expandedDirs.has(dirPath)) {
      newExpanded.delete(dirPath);
    } else {
      newExpanded.add(dirPath);
    }
    setExpandedDirs(newExpanded);
  };

  const renderFileTree = (entries, level = 0) => {
    return entries.map((entry) => {
      const isExpanded = expandedDirs.has(entry.path);
      const isSelected = currentFile === entry.path;

      return (
        <div key={entry.path}>
          <div
            className={`file-item ${isSelected ? "selected" : ""}`}
            style={{ paddingLeft: `${level * 16 + 8}px` }}
            onClick={() => {
              if (entry.isDirectory) {
                toggleDirectory(entry.path);
              } else {
                onFileSelect(entry.path);
              }
            }}
          >
            <div className="file-item-content">
              {entry.isDirectory ? (
                <>
                  {isExpanded ? (
                    <FaChevronDown size={12} />
                  ) : (
                    <FaChevronRight size={12} />
                  )}
                  <FaFolder className="icon folder-icon" />
                </>
              ) : (
                <FaFile className="icon file-icon" />
              )}
              <span className="file-name">{entry.name}</span>
            </div>
          </div>
        </div>
      );
    });
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h3>Explorer</h3>
        <button className="select-project-btn" onClick={onSelectProject}>
          {projectPath ? "Change Project" : "Open Folder"}
        </button>
      </div>

      <div className="file-tree">
        {projectPath ? (
          <>
            <div className="project-path">{projectPath}</div>
            {files.length > 0 ? (
              renderFileTree(files)
            ) : (
              <div className="empty-state">No files found</div>
            )}
          </>
        ) : (
          <div className="empty-state">
            <p>No folder opened</p>
            <button onClick={onSelectProject}>Open Folder</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
