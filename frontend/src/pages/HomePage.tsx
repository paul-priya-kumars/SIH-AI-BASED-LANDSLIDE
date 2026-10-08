import React, { useEffect, useState } from 'react';
import { useGeolocation } from '../hooks/useGeolocation';
import { RiskPrediction, EnvironmentData, Alert } from '../types';
import { RiskCard } from '../components/dashboard/RiskCard';
import { EnvironmentalCard } from '../components/dashboard/EnvironmentalCard';
import { LocationCard } from '../components/dashboard/LocationCard';
import { AlertCard } from '../components/dashboard/AlertCard';
import { QuickActions } from '../components/dashboard/QuickActions';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { Bell, ShieldCheck, Flame, ArrowRight, RefreshCw, Zap, Server, Database } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useRiskData } from '../hooks/useEnhancedApi';
import { useEnvironmentData } from '../hooks/useEnhancedApi';
import { useAlerts } from '../hooks/useEnhancedApi';
import { useModelInfo } from '../hooks/useEnhancedApi';
import { useDriftStatus } from '../hooks/useEnhancedApi';
import { useApiLoadingStatus } from '../hooks/useEnhancedApi';

export const HomePage: React.FC = () => {
  const {
    location,
    loading: geoLoading,
    error: geoError,
    permissionDenied,
    detectLocation,
    setLocation,
  } = useGeolocation();

  // Enhanced API hooks with better state management
  const riskData = useRiskData(location.latitude, location.longitude);
  const environmentData = useEnvironmentData(location.latitude, location.longitude);
  const alertsData = useAlerts();
  const modelInfo = useModelInfo();
  const driftStatus = useDriftStatus();
  const { isLoading: globalLoading, error: globalError } = useApiLoadingStatus();

  // Combine loading states
  const isLoading = geoLoading ||
    riskData.loading ||
    environmentData.loading ||
    alertsData.loading ||
    modelInfo.loading ||
    driftStatus.loading ||
    globalLoading;

  // Combine error states
  const combinedError = geoError ||
    riskData.error ||
    environmentData.error ||
    alertsData.error ||
    modelInfo.error ||
    driftStatus.error ||
    globalError;

  // Check for stale data (older than 5 minutes)
  const isRiskStale = riskData.isStale;
  const isEnvironmentStale = environmentData.isStale;
  const isAlertsStale = alertsData.isStale;
  const isModelInfoStale = modelInfo.isStale;
  const isDriftStatusStale = driftStatus.isStale;

  const loadDashboardData = async () => {
    // Trigger refetches for all data
    await Promise.all([
      riskData.refetch(),
      environmentData.refetch(),
      alertsData.refetch(),
      modelInfo.refetch(),
      driftStatus.refetch()
    ]);
  };

  // Critical alerts filtering
  const criticalAlerts = alertsData.data?.filter(
    (a) => a.severity === 'CRITICAL' || a.severity === 'HIGH'
  ) || [];

  // Handle loading states
  if (isLoading && !riskData.data && !environmentData.data) {
    return <LoadingState message="Connecting to telemetry station and GIS models..." className="min-h-[50vh]" />;
  }

  // Handle error states - show error UI but still display cached data if available
  const showErrorState = combinedError && !riskData.data && !environmentData.data;

  if (showErrorState) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center px-4 py-8">
        <ErrorState
          message={combinedError}
          onRetry={loadDashboardData}
          className="w-full max-w-md"
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Global Status Indicators */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-3xl bg-slate-900/50 border border-slate-800/50">
        {/* Data Freshness Indicators */}
        <div className="flex flex-wrap items-center gap-4 text-xs">
          {isRiskStale && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-orange-500/20 text-orange-400 border border-orange-500/30">
              <Zap className="w-3 h-3" /> Risk Data Stale
            </span>
          )}
          {isEnvironmentStale && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-orange-500/20 text-orange-400 border border-orange-500/30">
              <Zap className="w-3 h-3" /> Env Data Stale
            </span>
          )}
          {isAlertsStale && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-orange-500/20 text-orange-400 border border-orange-500/30">
              <Zap className="w-3 h-3" /> Alerts Stale
            </span>
          )}
          {isModelInfoStale && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-400 border border-blue-500/30">
              <Server className="w-3 h-3" /> Model Info Stale
            </span>
          )}
          {isDriftStatusStale && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-500/20 text-purple-400 border border-purple-500/30">
              <Database className="w-3 h-3" /> Drift Status Stale
            </span>
          )}
          {!isRiskStale && !isEnvironmentStale && !isAlertsStale && !isModelInfoStale && !isDriftStatusStale && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <ShieldCheck className="w-3 h-3" /> Data Fresh
            </span>
          )}
        </div>

        {/* Manual Refresh Button */}
        <button
          onClick={loadDashboardData}
          className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 hover:text-slate-100 rounded-xl transition-all disabled:opacity-50"
          disabled={isLoading}
        >
          <RefreshCw className="w-4 h-4" />
          <span className="whitespace-nowrap">Refresh All Data</span>
          {isLoading && (
            <span className="ml-2 animate-spin w-3 h-3 border-2 border-current"></span>
          )}
        </button>
      </div>

      {/* Top Banner if Critical Alert exists */}
      {criticalAlerts.length > 0 && (
        <div className="p-4 rounded-3xl bg-red-500/15 border border-red-500/40 text-red-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg shadow-red-950/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 shrink-0">
              <Flame className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="text-xs uppercase font-extrabold tracking-wider text-red-400">
                CRITICAL EMERGENCY WARNING IN EFFECT
              </div>
              <p className="text-sm font-semibold text-white">
                {criticalAlerts[0].title}
              </p>
            </div>
          </div>
          <Link
            to="/alerts"
            className="inline-flex items-center gap-1 px-4 py-1.5 bg-red-600 hover:bg-red-500 text-white font-bold text-xs rounded-xl transition shrink-0"
          >
            Review Advisories <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Hero / Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-orange-400 block mb-1">
            Real-Time Hazard Early Warning System
          </span>
          <h1 className="text-3xl sm:text-4xl font-black text-white font-heading tracking-tight">
            Nilgiris Mountain Early Warning Center
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Live terrain saturation monitoring, slope stability analytics, and citizen hazard reporting.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
          <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
            Live Telemetry Online
          </span>
        </div>
      </div>

      {/* Quick Action Launchers */}
      <QuickActions />

      {/* Main Grid: Location & Risk Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Geographic Focus */}
        <div className="lg:col-span-4 space-y-6">
          <LocationCard
            location={location}
            loading={geoLoading}
            error={geoError}
            permissionDenied={permissionDenied}
            onDetectGPS={detectLocation}
            onSelectLocation={setLocation}
            isStale={isEnvironmentStale}
            lastUpdated={environmentData.lastUpdated}
          />

          {/* Environmental Overview card */}
          {environmentData.data && (
            <EnvironmentalCard
              environment={environmentData.data}
              isStale={isEnvironmentStale}
              lastUpdated={environmentData.lastUpdated}
            />
          )}
        </div>

        {/* Right Column: High Impact Risk Card & Recent Advisories */}
        <div className="lg:col-span-8 space-y-6">
          {riskData.data && (
            <RiskCard
              prediction={riskData.data}
              locationName={location.name || 'Nilgiris Highlands'}
              isStale={isRiskStale}
              lastUpdated={riskData.lastUpdated}
            />
          )}

          {/* Active Advisories Card Section */}
          <div className="p-6 rounded-3xl glass-card border-slate-800 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-orange-400" />
                <h3 className="text-base font-bold text-white">
                  Active Emergency Advisories ({alertsData.data?.length || 0})
                  {isAlertsStale && (
                    <span className="text-xs text-orange-400">(stale)</span>
                  )}
                </h3>
              </div>
              <Link
                to="/alerts"
                className="text-xs font-semibold text-orange-400 hover:text-orange-300 transition flex items-center gap-1"
              >
                All Bulletins <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(alertsData.data?.slice(0, 2) || []).map((alert) => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  isStale={isAlertsStale}
                  lastUpdated={alertsData.lastUpdated}
                />
              ))}
            </div>
          </div>

          {/* Model Information Section */}
          {modelInfo.data && (
            <div className="p-6 rounded-3xl glass-card border-slate-800 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-blue-400" />
                  <h3 className="text-base font-bold text-white">
                    ML Model Information
                    {isModelInfoStale && (
                      <span className="text-xs text-blue-400">(stale)</span>
                    )}
                  </h3>
                </div>
                <button
                  onClick={() => modelInfo.refetch()}
                  className="text-xs font-semibold text-blue-400 hover:text-blue-300 transition flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-900/50"
                >
                  <RefreshCw className="w-3 h-3" /> Refresh
                </button>
              </div>

              <div className="space-y-4 text-sm">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <span className="text-xs font-medium text-slate-400">Model Status:</span>
                    <p className="font-mono">
                      {modelInfo.data.available ?
                        (modelInfo.data.image_ai_enabled ?
                          '🟢 AI Enabled & Loaded' :
                          '🟡 Model Available but AI Disabled') :
                        '🔴 Model Not Available'}
                      {modelInfo.data.error && (
                        <span className="ml-2 text-xs text-red-400" title={modelInfo.data.error}>
                          !
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="flex-1">
                    <span className="text-xs font-medium text-slate-400">Model Version:</span>
                    <p className="font-mono text-xs">{modelInfo.data.model_version || 'N/A'}</p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <span className="text-xs font-medium text-slate-400">Checksum:</span>
                    <p className="font-mono text-xs break-all max-w-xs">{modelInfo.data.checksum || 'N/A'}</p>
                  </div>
                  <div className="flex-1">
                    <span className="text-xs font-medium text-slate-400">Load Time:</span>
                    <p className="font-mono text-xs">{modelInfo.data.load_time_seconds !== null ?
                      `${modelInfo.data.load_time_seconds.toFixed(2)}s` :
                      'N/A'}</p>
                  </div>
                </div>

                {modelInfo.data.checkpoint_epoch !== 'unknown' && modelInfo.data.checkpoint_epoch !== null && (
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <span className="text-xs font-medium text-slate-400">Checkpoint Epoch:</span>
                      <p className="font-mono text-xs">{modelInfo.data.checkpoint_epoch}</p>
                    </div>
                    <div className="flex-1">
                      <span className="text-xs font-medium text-slate-400">Best Val Dice:</span>
                      <p className="font-mono text-xs">{modelInfo.data.checkpoint_best_val_dice}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Drift Status Section */}
          {driftStatus.data && (
            <div className="p-6 rounded-3xl glass-card border-slate-800 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-purple-400" />
                  <h3 className="text-base font-bold text-white">
                    Drift Detection Status
                    {isDriftStatusStale && (
                      <span className="text-xs text-purple-400">(stale)</span>
                    )}
                  </h3>
                </div>
                <button
                  onClick={() => driftStatus.refetch()}
                  className="text-xs font-semibold text-purple-400 hover:text-purple-300 transition flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-900/50"
                >
                  <RefreshCw className="w-3 h-3" /> Refresh
                </button>
              </div>

              <div className="space-y-4 text-sm">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <span className="text-xs font-medium text-slate-400">Drift Monitoring:</span>
                    <p className="font-mono">
                      {driftStatus.data.enabled ?
                        '🟢 Enabled' :
                        '🔴 Disabled'}
                    </p>
                  </div>
                  <div className="flex-1">
                    <span className="text-xs font-medium text-slate-400">Baseline Available:</span>
                    <p className="font-mono">
                      {driftStatus.data.baseline_available ?
                        '🟢 Yes' :
                        '🔴 No'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <span className="text-xs font-medium text-slate-400">Drift Detected:</span>
                    <p className="font-mono">
                      {driftStatus.data.drift_detected ?
                        '<span class="text-red-400 font-bold">🔴 YES - DRIFT DETECTED</span>' :
                        '<span class="text-green-400 font-bold">🟢 NO - STABLE</span>'}
                    </p>
                  </div>
                  <div className="flex-1">
                    <span className="text-xs font-medium text-slate-400">Observation Window:</span>
                    <p className="font-mono text-xs">{driftStatus.data.observation_count}/${driftStatus.data.window_size}</p>
                  </div>
                </div>

                {driftStatus.data.details && (
                  <div className="mt-4 pt-3 border-t border-slate-800/20">
                    <span className="text-xs font-medium text-slate-400 block mb-2">PSI Scores by Band:</span>
                    <div className="space-y-1 text-xs font-mono">
                      {driftStatus.data.details.psi_scores?.map((score: number, index: number) => (
                        <div key={index} className="flex items-center gap-3">
                          <span className="w-8">Band {index + 1}:</span>
                          <span className="flex-1">{score.toFixed(4)}</span>
                          <span className="w-16 bg-slate-900/50 rounded-full h-2.5 relative overflow-hidden">
                            <div
                              className={`h-full bg-${score > 0.2 ? 'red-500' : score > 0.1 ? 'orange-500' : 'green-500'}/50 rounded-full h-2.5`}
                              style={{ width: `${Math.min(score * 100, 100)}%` }}
                            ></div>
                          </span>
                          <span className="ml-2 text-xs font-bold">
                            {score > 0.2 ? 'HIGH' : score > 0.1 ? 'MED' : 'LOW'}
                          </span>
                        </div>
                      )) || [
                        <div key="no-data" className="text-slate-400 italic">No PSI data available</div>
                      ]}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};