import React, { useState, useEffect } from "react";
import { FaSearch, FaMicrochip } from "react-icons/fa";
import "./ComponentLibrary.css";

const ComponentLibrary = ({ projectPath, components = [] }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredComponents, setFilteredComponents] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("all");

  const categories = [
    { id: "all", name: "All Components" },
    { id: "microcontroller", name: "Microcontrollers" },
    { id: "passive", name: "Passive Components" },
    { id: "active", name: "Active Components" },
    { id: "connector", name: "Connectors" },
    { id: "power", name: "Power" },
    { id: "sensor", name: "Sensors" },
  ];

  // Mock component data - will be replaced with actual library parsing
  const mockComponents = [
    { name: "Arduino_Uno", category: "microcontroller", library: "MCU_Module" },
    {
      name: "ATmega328P",
      category: "microcontroller",
      library: "MCU_Microchip_ATmega",
    },
    { name: "R", category: "passive", library: "Device" },
    { name: "C", category: "passive", library: "Device" },
    { name: "LED", category: "active", library: "Device" },
    { name: "LM7805", category: "power", library: "Regulator_Linear" },
    { name: "DHT22", category: "sensor", library: "Sensor_Temperature" },
    {
      name: "USB_C_Receptacle",
      category: "connector",
      library: "Connector_USB",
    },
  ];

  useEffect(() => {
    // Use generated components if available, otherwise show mock
    const displayComponents =
      components.length > 0 ? components : mockComponents;
    let filtered = displayComponents;

    if (selectedCategory !== "all") {
      filtered = filtered.filter((c) => c.category === selectedCategory);
    }

    if (searchTerm) {
      filtered = filtered.filter(
        (c) =>
          c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.library.toLowerCase().includes(searchTerm.toLowerCase()),
      );
    }

    setFilteredComponents(filtered);
  }, [searchTerm, selectedCategory, components, projectPath]);

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

      <div className="category-filter">
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`category-btn ${selectedCategory === cat.id ? "active" : ""}`}
            onClick={() => setSelectedCategory(cat.id)}
          >
            {cat.name}
          </button>
        ))}
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
