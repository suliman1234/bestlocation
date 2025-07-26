import React, { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polygon,
  useMapEvents,
  LayersControl,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import facilities from "../data/facilities.json";
import popGrid from "../data/pop_grid.json";

const defaultPosition = [24.7136, 46.6753]; // Riyadh

// Custom blue star for clicked location
const blueStarIcon = new L.Icon({
  iconUrl: "https://upload.wikimedia.org/wikipedia/commons/e/e3/Blue_star.svg",
  iconSize: [30, 30],
  iconAnchor: [15, 30],
});

// Custom gold star for best locations
const goldStarIcon = new L.Icon({
  iconUrl: "https://upload.wikimedia.org/wikipedia/commons/4/44/Plain_Yellow_Star.png",
  iconSize: [26, 26],
  iconAnchor: [13, 26],
});

// Simple color scale for population density
const getColor = (d) => {
  return d > 5000
    ? "#800026"
    : d > 2500
    ? "#BD0026"
    : d > 1000
    ? "#E31A1C"
    : d > 500
    ? "#FC4E2A"
    : d > 200
    ? "#FD8D3C"
    : d > 100
    ? "#FEB24C"
    : d > 50
    ? "#FED976"
    : "#FFEDA0";
};

export default function MapView() {
  const [clickedLocation, setClickedLocation] = useState(null);
  const [bestLocations, setBestLocations] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

  const handleMapClick = (e) => {
    setClickedLocation(e.latlng);
  };

  const calculateCompositeScore = (lat, lng) => {
    // Example dummy score: nearest population density
    let score = 0;
    popGrid.features.forEach((feature) => {
      const coords = feature?.geometry?.coordinates;
      if (
        !Array.isArray(coords) ||
        !Array.isArray(coords[0]) ||
        !Array.isArray(coords[0][0])
      )
        return;

      const polygon = coords[0]
        .map((pair) => {
          if (!Array.isArray(pair) || pair.length < 2) return null;
          return [pair[1], pair[0]];
        })
        .filter(Boolean);

      if (polygon.length < 3) return;

      if (L.polygon(polygon).getBounds().contains([lat, lng])) {
        score = feature?.properties?.PDEN_KM2 ?? 0;
      }
    });
    return score;
  };

  const FindBestLocations = () => {
    // Top 3 grid cells by PDEN_KM2
    const sorted = popGrid.features
      .filter((f) => f?.properties?.PDEN_KM2)
      .sort((a, b) => b.properties.PDEN_KM2 - a.properties.PDEN_KM2)
      .slice(0, 3)
      .map((f) => {
        const coords = f.geometry?.coordinates?.[0];
        if (!coords || coords.length < 3) return null;
        const latlngs = coords.map(([lng, lat]) => [lat, lng]);
        const polygon = L.polygon(latlngs);
        const center = polygon.getBounds().getCenter();
        return {
          lat: center.lat,
          lng: center.lng,
          score: f.properties.PDEN_KM2,
        };
      })
      .filter(Boolean);
    setBestLocations(sorted);
  };

  const MapClickHandler = () => {
    useMapEvents({
      click: handleMapClick,
    });
    return null;
  };

  return (
    <div style={{ display: "flex" }}>
      {/* Map */}
      <div style={{ flex: 1, height: "100vh" }}>
        <MapContainer center={defaultPosition} zoom={11} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler />

          {/* Population polygons */}
          {popGrid.features.map((feature, idx) => {
            const coords = feature?.geometry?.coordinates;
            if (
              !Array.isArray(coords) ||
              !Array.isArray(coords[0]) ||
              !Array.isArray(coords[0][0])
            )
              return null;

            const polygon = coords[0]
              .map((pair) => {
                if (!Array.isArray(pair) || pair.length < 2) return null;
                return [pair[1], pair[0]];
              })
              .filter(Boolean);
            if (polygon.length < 3) return null;

            const density = feature?.properties?.PDEN_KM2 ?? 0;

            return (
              <Polygon
                key={idx}
                positions={polygon}
                pathOptions={{
                  fillColor: getColor(density),
                  color: "#999",
                  weight: 0.3,
                  fillOpacity: 0.4,
                }}
              >
                <Popup>Pop Density: {density}</Popup>
              </Polygon>
            );
          })}

          {/* Facilities */}
          {facilities.map((f, i) => (
            <Marker key={i} position={[f.coords[1], f.coords[0]]}>
              <Popup>
                <b>{f.name}</b>
                <br />
                {f.type}
              </Popup>
            </Marker>
          ))}

          {/* Clicked location */}
          {clickedLocation && (
            <Marker position={clickedLocation} icon={blueStarIcon}>
              <Popup>
                Composite Score:{" "}
                {calculateCompositeScore(clickedLocation.lat, clickedLocation.lng)}
              </Popup>
            </Marker>
          )}

          {/* Best locations */}
          {bestLocations.map((loc, i) => (
            <Marker key={i} position={[loc.lat, loc.lng]} icon={goldStarIcon}>
              <Popup>
                ⭐ Best Location #{i + 1}
                <br />
                Score: {loc.score}
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Sidebar */}
      <div style={{ width: "280px", background: "#f5f5f5", padding: "10px" }}>
        <button onClick={() => setShowFilters(!showFilters)}>
          {showFilters ? "Hide Filters" : "Show Filters"}
        </button>

        {showFilters && (
          <div style={{ marginTop: "10px" }}>
            <label>Facility Type:</label>
            <select>
              <option value="all">All</option>
              <option value="PHC">PHC</option>
              <option value="Hospital">Hospital</option>
              {/* add more types */}
            </select>

            <label>Proximity Radius (km):</label>
            <input type="number" defaultValue={2} />

            <button style={{ marginTop: "10px" }} onClick={FindBestLocations}>
              Show Best Locations
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
