import React, { useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Circle,
  Marker,
  Popup,
  Polyline,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import { RiskZone, UserLocation } from '../../types';
import { RiskBadge } from '../dashboard/RiskBadge';
import { Info, MapPin } from 'lucide-react';

// Custom Map Controller to smoothly re-center map when coordinates change
const MapController: React.FC<{ center: [number, number]; zoom?: number }> = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom || map.getZoom());
    }
  }, [center, zoom, map]);
  return null;
};

// Create custom SVG DivIcons for Leaflet
const createCustomIcon = (color: string, label: string) => {
  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        transform: translate(-50%, -100%);
      ">
        <div style="
          background: ${color};
          color: white;
          padding: 4px 8px;
          border-radius: 9999px;
          font-size: 10px;
          font-weight: bold;
          white-space: nowrap;
          box-shadow: 0 4px 12px rgba(0,0,0,0.5);
          border: 1px solid rgba(255,255,255,0.4);
        ">
          ${label}
        </div>
        <div style="
          width: 0; 
          height: 0; 
          border-left: 5px solid transparent;
          border-right: 5px solid transparent;
          border-top: 6px solid ${color};
        "></div>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -32],
  });
};

const userIcon = L.divIcon({
  className: 'user-pin-marker',
  html: `
    <div style="
      width: 24px;
      height: 24px;
      background: #3b82f6;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 0 15px #3b82f6;
      animation: pulse 2s infinite;
    "></div>
  `,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  zones?: RiskZone[];
  userLocation?: UserLocation | null;
  onSelectZone?: (zone: RiskZone) => void;
  routeWaypoints?: [number, number][];
  alternativeWaypoints?: [number, number][];
  className?: string;
}

export const MapView: React.FC<MapViewProps> = ({
  center = [11.4102, 76.6950],
  zoom = 12,
  zones = [],
  userLocation,
  onSelectZone,
  routeWaypoints,
  alternativeWaypoints,
  className = 'h-[500px] w-full',
}) => {
  const getZoneColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'VERY_HIGH':
      case 'CRITICAL':
        return '#ef4444';
      case 'HIGH':
        return '#f97316';
      case 'MODERATE':
        return '#f59e0b';
      case 'LOW':
      default:
        return '#10b981';
    }
  };

  return (
    <div className={`relative rounded-3xl overflow-hidden border border-slate-800 shadow-2xl ${className}`}>
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <MapController center={center} zoom={zoom} />

        {/* Dark / Satellite styled OpenStreetMap CartoDB Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          maxZoom={19}
        />

        {/* Render Risk Hazard Zones */}
        {zones.map((zone) => {
          const color = getZoneColor(zone.risk_level);
          const icon = createCustomIcon(color, zone.name.split(' ')[0]);

          return (
            <React.Fragment key={zone.zone_id}>
              {/* Semi-transparent hazard buffer circle */}
              <Circle
                center={[zone.latitude, zone.longitude]}
                radius={zone.radius_meters}
                pathOptions={{
                  color: color,
                  fillColor: color,
                  fillOpacity: 0.25,
                  weight: 2,
                  dashArray: zone.risk_level === 'VERY_HIGH' ? '6, 6' : undefined,
                }}
                eventHandlers={{
                  click: () => onSelectZone?.(zone),
                }}
              />

              {/* Marker pin */}
              <Marker
                position={[zone.latitude, zone.longitude]}
                icon={icon}
                eventHandlers={{
                  click: () => onSelectZone?.(zone),
                }}
              >
                <Popup className="custom-popup">
                  <div className="p-2 min-w-[200px]">
                    <div className="text-xs font-bold text-slate-100 mb-1">
                      {zone.name}
                    </div>
                    <div className="mb-2">
                      <RiskBadge level={zone.risk_level} size="sm" />
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300 font-mono mb-2">
                      <div>Rain: {zone.rainfall_mm}mm</div>
                      <div>Slope: {zone.slope_deg}°</div>
                      <div>Elev: {zone.elevation_m}m</div>
                      <div>Prob: {Math.round(zone.risk_probability * 100)}%</div>
                    </div>
                    {onSelectZone && (
                      <button
                        onClick={() => onSelectZone(zone)}
                        className="w-full text-center py-1 px-2 bg-orange-600 hover:bg-orange-500 text-white rounded text-[10px] font-semibold transition"
                      >
                        Inspect Full GIS Telemetry
                      </button>
                    )}
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          );
        })}

        {/* Optional Route Waypoint Polylines */}
        {routeWaypoints && routeWaypoints.length > 0 && (
          <Polyline
            positions={routeWaypoints}
            pathOptions={{
              color: '#10b981',
              weight: 5,
              opacity: 0.85,
            }}
          />
        )}

        {alternativeWaypoints && alternativeWaypoints.length > 0 && (
          <Polyline
            positions={alternativeWaypoints}
            pathOptions={{
              color: '#ef4444',
              weight: 4,
              opacity: 0.75,
              dashArray: '8, 8',
            }}
          />
        )}

        {/* User Location Pin */}
        {userLocation && (
          <Marker
            position={[userLocation.latitude, userLocation.longitude]}
            icon={userIcon}
          >
            <Popup>
              <div className="p-1 text-center font-sans">
                <span className="text-xs font-bold text-slate-100 block">
                  📍 Your Location
                </span>
                <span className="text-[11px] text-slate-400 font-mono">
                  {userLocation.latitude.toFixed(4)}, {userLocation.longitude.toFixed(4)}
                </span>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* Map Legend Overlay */}
      <div className="absolute bottom-4 left-4 z-20 p-3 rounded-2xl glass-card border-slate-700/80 shadow-lg text-[11px]">
        <span className="text-[10px] uppercase tracking-wider font-bold text-slate-400 block mb-1.5">
          Hazard Susceptibility
        </span>
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-slate-300">Low</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span className="text-slate-300">Moderate</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
            <span className="text-slate-300">High</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
            <span className="text-slate-300 font-semibold">Very High</span>
          </div>
        </div>
      </div>
    </div>
  );
};
