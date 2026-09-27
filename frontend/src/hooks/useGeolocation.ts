import { useState, useEffect, useCallback } from 'react';
import { UserLocation } from '../types';
import { DEFAULT_LOCATION, PRESET_LOCATIONS } from '../data/mockData';

export interface GeolocationState {
  location: UserLocation;
  loading: boolean;
  error: string | null;
  permissionDenied: boolean;
  isCustom: boolean;
  detectLocation: () => void;
  setLocation: (loc: UserLocation) => void;
}

export function useGeolocation(): GeolocationState {
  const [location, setLocationState] = useState<UserLocation>(() => {
    const saved = localStorage.getItem('geoshield_active_location');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return DEFAULT_LOCATION;
      }
    }
    return DEFAULT_LOCATION;
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState<boolean>(false);
  const [isCustom, setIsCustom] = useState<boolean>(false);

  const setLocation = useCallback((newLoc: UserLocation) => {
    setLocationState(newLoc);
    setIsCustom(true);
    localStorage.setItem('geoshield_active_location', JSON.stringify(newLoc));
  }, []);

  const detectLocation = useCallback(() => {
    if (!('geolocation' in navigator)) {
      setError('Geolocation is not supported by your browser.');
      return;
    }

    setLoading(true);
    setError(null);
    setPermissionDenied(false);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const detected: UserLocation = {
          name: 'Your Current Location (GPS)',
          latitude: Number(position.coords.latitude.toFixed(4)),
          longitude: Number(position.coords.longitude.toFixed(4)),
          accuracy: position.coords.accuracy,
          isCustom: false,
        };
        setLocationState(detected);
        setIsCustom(false);
        setLoading(false);
        localStorage.setItem('geoshield_active_location', JSON.stringify(detected));
      },
      (geoError) => {
        setLoading(false);
        if (geoError.code === geoError.PERMISSION_DENIED) {
          setPermissionDenied(true);
          setError('Location access denied. Using fallback mountain monitoring sector.');
        } else if (geoError.code === geoError.POSITION_UNAVAILABLE) {
          setError('Location signal unavailable. Using default station coordinates.');
        } else {
          setError('Location request timed out. Using default station coordinates.');
        }
        // Graceful fallback to default Ooty location
        setLocationState(DEFAULT_LOCATION);
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
    );
  }, []);

  return {
    location,
    loading,
    error,
    permissionDenied,
    isCustom,
    detectLocation,
    setLocation,
  };
}
