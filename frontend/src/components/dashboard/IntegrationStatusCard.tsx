import React, { useCallback, useEffect, useState } from 'react';
import { Layers, RefreshCw } from 'lucide-react';
import {
  CompositeRisk,
  ModelsStatus,
  RiskComponent,
  fetchCompositeRisk,
  fetchModelsStatus,
} from '../../services/integrationApi';

interface Props {
  latitude: number;
  longitude: number;
}

/** Honest provenance badge: REAL vs DEMO vs unavailable. */
const ProvenanceBadge: React.FC<{ component?: RiskComponent }> = ({ component }) => {
  if (!component || !component.available) {
    return (
      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-700/60 text-slate-300">
        NOT AVAILABLE
      </span>
    );
  }
  if (component.is_real === false) {
    return (
      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-900/60 text-amber-300">
        DEMO DATA
      </span>
    );
  }
  return (
    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-900/60 text-emerald-300">
      REAL MODEL
    </span>
  );
};

const percent = (value: number | null | undefined): string =>
  value === null || value === undefined ? '—' : `${(value * 100).toFixed(1)}%`;

export const IntegrationStatusCard: React.FC<Props> = ({ latitude, longitude }) => {
  const [composite, setComposite] = useState<CompositeRisk | null>(null);
  const [models, setModels] = useState<ModelsStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const [compositeData, modelsData] = await Promise.all([
          fetchCompositeRisk(latitude, longitude, signal),
          fetchModelsStatus(signal),
        ]);
        setComposite(compositeData);
        setModels(modelsData);
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          setError((err as Error).message);
        }
      } finally {
        setLoading(false);
      }
    },
    [latitude, longitude],
  );

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const m1 = composite?.components.environmental_m1;
  const m2 = composite?.components.spatial_m2;
  const m3 = composite?.components.satellite_m3;
  const finalRisk = composite?.final_risk;

  return (
    <div className="p-6 rounded-3xl glass-card border-slate-800 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <h3 className="text-base font-bold text-white">Model Integration (M1 / M2 / M3)</h3>
        </div>
        <button
          onClick={() => load()}
          className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition flex items-center gap-1 px-2 py-0.5 rounded-md bg-cyan-900/40"
        >
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>

      {loading && !composite && (
        <p className="text-sm text-slate-400">Querying the M1/M2/M3 integration layer…</p>
      )}

      {error && !composite && (
        <div className="text-sm text-red-400">
          Could not load integration status: {error}
        </div>
      )}

      {composite && (
        <div className="space-y-4 text-sm">
          {/* Environmental M1 */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-400">Environmental (M1):</span>
                <ProvenanceBadge component={m1} />
              </div>
              <p className="font-mono text-xs mt-1">
                {m1?.available
                  ? `${m1.level} · ${percent(m1.probability)} · confidence ${percent(m1.confidence)}`
                  : `Not available${m1?.error ? ` (${m1.error})` : ''}`}
              </p>
              {models?.environmental_m1.artifact_path && (
                <p className="text-[10px] text-slate-500 font-mono truncate" title={models.environmental_m1.artifact_path}>
                  {models.environmental_m1.model_version}
                </p>
              )}
            </div>
          </div>

          {/* Spatial M2 */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-400">Spatial / GIS (M2):</span>
                <ProvenanceBadge component={m2} />
              </div>
              <p className="font-mono text-xs mt-1">
                {m2?.available
                  ? `${m2.zone_id} · ${m2.level} · ${percent(m2.probability)}`
                  : 'Not available'}
              </p>
              {m2?.data_source && (
                <p className="text-[10px] text-slate-500">{m2.data_source}</p>
              )}
            </div>
          </div>

          {/* Satellite M3 */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-400">Satellite (M3):</span>
                <ProvenanceBadge component={m3} />
              </div>
              <p className="font-mono text-xs mt-1">
                {m3?.available
                  ? `${percent(m3.probability)} mean patch probability`
                  : m3?.reason || models?.satellite_m3.coordinate_mapping?.reason || 'Not available'}
              </p>
            </div>
          </div>

          {/* Final composite */}
          <div className="pt-3 border-t border-slate-700/60">
            <span className="text-xs font-medium text-slate-400">Final composite risk:</span>
            <p className="text-lg font-bold text-white font-mono">
              {finalRisk?.available
                ? `${finalRisk.risk_level} · ${percent(finalRisk.probability)}`
                : 'Unavailable'}
            </p>
            <p className="text-[10px] text-slate-500">
              Combined from: {composite.components_used.join(', ') || 'none'} ·{' '}
              {finalRisk?.method}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
