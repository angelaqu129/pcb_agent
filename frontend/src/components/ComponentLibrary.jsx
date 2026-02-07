import React, { useState, useEffect } from "react";
import { FaSearch, FaMicrochip } from "react-icons/fa";
import "./ComponentLibrary.css";

const ComponentLibrary = ({ projectPath, components = [] }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredComponents, setFilteredComponents] = useState([]);
  const [allowList, setAllowList] = useState([]);

  // Load allow_list.json on mount
  useEffect(() => {
    fetch("http://localhost:5001/api/allow-list")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          // Map to component format
          const mapped = data.data.map((c) => ({
            name: c.symbol,
            symbol: c.symbol,
            library: c.lib?.replace(".kicad_sym", "") || "",
            lib: c.lib,
            footprint: c.footprint,
          }));
          setAllowList(mapped);
        }
      })
      .catch((err) => console.error("Error loading allow list:", err));
  }, []);

  useEffect(() => {
    // Use generated components if available, otherwise show allow list
    const displayComponents = components.length > 0 ? components : allowList;
    let filtered = displayComponents;

    if (searchTerm) {
      filtered = filtered.filter(
        (c) =>
          (c.name || c.symbol || "")
            .toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
          (c.library || c.lib || "")
            .toLowerCase()
            .includes(searchTerm.toLowerCase()),
      );
    }

    setFilteredComponents(filtered);
  }, [searchTerm, components, projectPath, allowList]);

  const handleDragStart = (e, component) => {
    e.dataTransfer.setData("component", JSON.stringify(component));
  };

  return (
    <div className="component-library">
      <div className="library-header">
        <h3>
          {components.length > 0 ? "Generated Components" : "Component Library"}
        </h3>
        {components.length > 0 && (
          <span className="component-count-badge">
            {components.length} selected
          </span>
        )}
      </div>

      <div className="search-container">
        <FaSearch className="search-icon" />
        <input
          type="text"
          className="search-input"
          placeholder="Search components..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="component-list">
        {filteredComponents.length > 0 ? (
          filteredComponents.map((component, index) => (
            <div
              key={index}
              className="component-item"
              draggable
              onDragStart={(e) => handleDragStart(e, component)}
            >
              <FaMicrochip className="component-icon" />
              <div className="component-info">
                <div className="component-name">
                  {component.symbol || component.name}
                  {component.ref_des && (
                    <span className="ref-badge">{component.ref_des}</span>
                  )}
                </div>
                {component.value && (
                  <div className="component-value">{component.value}</div>
                )}
                <div className="component-library">
                  {component.lib || component.library}
                </div>
                {component.explanation && (
                  <div className="component-explanation">
                    💡 {component.explanation}
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <p>No components found</p>
          </div>
        )}
      </div>

      <div className="library-footer">
        <div className="component-count">
          {filteredComponents.length} component
          {filteredComponents.length !== 1 ? "s" : ""}
        </div>
      </div>
    </div>
  );
};

export default ComponentLibrary;
