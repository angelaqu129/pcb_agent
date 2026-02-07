import React, { useState, useEffect } from "react";
import { FaSearch, FaMicrochip, FaTimes, FaPlus } from "react-icons/fa";
import "./ComponentLibrary.css";

const ComponentLibrary = ({
  projectPath,
  components = [],
  onRemoveComponent,
  onAddComponent,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredComponents, setFilteredComponents] = useState([]);
  const [filteredAllowList, setFilteredAllowList] = useState([]);
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
    // Filter selected components
    let filtered = components;
    if (searchTerm && components.length > 0) {
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

    // Filter allow list (exclude already selected components)
    let filteredAllow = allowList;
    if (components.length > 0) {
      const selectedSymbols = new Set(
        components.map((c) => `${c.lib}::${c.symbol}`),
      );
      filteredAllow = allowList.filter(
        (c) => !selectedSymbols.has(`${c.lib}::${c.symbol}`),
      );
    }
    if (searchTerm) {
      filteredAllow = filteredAllow.filter(
        (c) =>
          (c.name || c.symbol || "")
            .toLowerCase()
            .includes(searchTerm.toLowerCase()) ||
          (c.library || c.lib || "")
            .toLowerCase()
            .includes(searchTerm.toLowerCase()),
      );
    }
    setFilteredAllowList(filteredAllow);
  }, [searchTerm, components, allowList]);

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

      {/* Selected Components Section */}
      {components.length > 0 && (
        <>
          <div className="section-header">Selected Components</div>
          <div className="component-list">
            {filteredComponents.length > 0 ? (
              filteredComponents.map((component, index) => (
                <div key={index} className="component-item">
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
                  <button
                    className="remove-component-btn"
                    onClick={() => onRemoveComponent(component)}
                    title="Remove component"
                  >
                    <FaTimes />
                  </button>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <p>No selected components match your search</p>
              </div>
            )}
          </div>
        </>
      )}

      {/* Add Components Section */}
      {components.length > 0 && (
        <>
          <div className="section-header">Add More Components</div>
          <div className="component-list">
            {filteredAllowList.length > 0 ? (
              filteredAllowList.slice(0, 10).map((component, index) => (
                <div key={index} className="component-item">
                  <FaMicrochip className="component-icon" />
                  <div className="component-info">
                    <div className="component-name">
                      {component.symbol || component.name}
                    </div>
                    <div className="component-library">
                      {component.lib || component.library}
                    </div>
                  </div>
                  {onAddComponent && (
                    <button
                      className="add-component-btn"
                      onClick={() => onAddComponent(component)}
                      title="Add component"
                    >
                      <FaPlus />
                    </button>
                  )}
                </div>
              ))
            ) : (
              <div className="empty-state">
                <p>No components found</p>
              </div>
            )}
          </div>
        </>
      )}

      {/* Default View - All Components */}
      {components.length === 0 && (
        <div className="component-list">
          {filteredAllowList.length > 0 ? (
            filteredAllowList.map((component, index) => (
              <div key={index} className="component-item" draggable>
                <FaMicrochip className="component-icon" />
                <div className="component-info">
                  <div className="component-name">
                    {component.symbol || component.name}
                  </div>
                  <div className="component-library">
                    {component.lib || component.library}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <p>No components found</p>
            </div>
          )}
        </div>
      )}

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
