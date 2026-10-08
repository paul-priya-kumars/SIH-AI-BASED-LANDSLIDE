import React, { useState } from 'react';
import { X, MapPin, Calendar, User, Phone, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { HazardReport } from '../../types';
import { StatusBadge } from './StatusBadge';
import { RiskBadge } from '../dashboard/RiskBadge';

interface ReportDetailModalProps {
  report: HazardReport | null;
  onClose: () => void;
  onStatusUpdate?: (reportId: string, newStatus: string) => Promise<void>;
}

export const ReportDetailModal: React.FC<ReportDetailModalProps> = ({
  report,
  onClose,
  onStatusUpdate,
}) => {
  const [updating, setUpdating] = useState<boolean>(false);
  const [currentStatus, setCurrentStatus] = useState<string>(report?.status || 'PENDING');

  if (!report) return null;

  const formattedDate = new Date(report.created_at).toLocaleString([], {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  const handleStatusChange = async (newStatus: string) => {
    if (!onStatusUpdate) return;
    setUpdating(true);
    try {
      await onStatusUpdate(report.report_id, newStatus);
      setCurrentStatus(newStatus);
    } catch (e) {
      console.error(e);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-150 overflow-y-auto">
      <div className="relative w-full max-w-xl my-8 p-6 rounded-3xl glass-card border-slate-700 bg-slate-900/95 shadow-2xl">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-full bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="mb-4 pr-10">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold text-orange-400">
              REPORT #{report.report_id}
            </span>
            <StatusBadge status={currentStatus} size="sm" />
          </div>
          <h3 className="text-2xl font-bold text-white">
            {report.hazard_type}
          </h3>
        </div>

        {/* Severity Banner */}
        <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-800/60 border border-slate-700/60 mb-5">
          <span className="text-xs text-slate-300 font-medium">Assessed Severity:</span>
          <RiskBadge level={report.severity} size="md" />
        </div>

        {/* Attached Photo if available */}
        {(report.image_url || report.image_path) && (
          <div className="mb-5 rounded-2xl overflow-hidden border border-slate-700/80 bg-slate-950 aspect-video relative group">
            <img
              src={report.image_url || `/${report.image_path}`}
              alt="Hazard observation"
              className="w-full h-full object-cover"
              onError={(e) => {
                // Fallback placeholder if file wasn't found on disk
                (e.target as HTMLImageElement).src =
                  'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=800&q=80';
              }}
            />
            <div className="absolute bottom-2 left-2 px-2 py-1 rounded bg-black/70 text-[10px] text-slate-300 backdrop-blur-xs">
              Field Photograph
            </div>
          </div>
        )}

        {/* Description */}
        <div className="mb-5">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
            Observation Description
          </h4>
          <p className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 text-sm text-slate-200 leading-relaxed">
            {report.description}
          </p>
        </div>

        {/* Meta & Location Details */}
        <div className="grid grid-cols-2 gap-3 mb-5 text-xs">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="text-slate-400 text-[11px] mb-1 flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-orange-400" />
              <span>Location Coordinates</span>
            </div>
            <div className="font-mono text-slate-200 font-semibold">
              {report.latitude.toFixed(4)}°N, {report.longitude.toFixed(4)}°E
            </div>
            <div className="text-[11px] text-slate-400 truncate mt-0.5">
              {report.location_name}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
            <div className="text-slate-400 text-[11px] mb-1 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-blue-400" />
              <span>Submission Time</span>
            </div>
            <div className="font-semibold text-slate-200">{formattedDate}</div>
            <div className="text-[11px] text-slate-500">Local Standard Time</div>
          </div>
        </div>

        {/* Contact Info (if provided) */}
        {(report.contact_name || report.contact_phone) && (
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 mb-5 flex items-center gap-4 text-xs text-slate-300">
            {report.contact_name && (
              <div className="flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Reporter: {report.contact_name}</span>
              </div>
            )}
            {report.contact_phone && (
              <div className="flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                <span>{report.contact_phone}</span>
              </div>
            )}
          </div>
        )}

        {/* Authority Review Status Controller */}
        {onStatusUpdate && (
          <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 mb-5">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-teal-400" />
                Authority Workflow State
              </span>
              {updating && <span className="text-[10px] text-orange-400 animate-pulse">Updating...</span>}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {['PENDING', 'UNDER_REVIEW', 'VERIFIED', 'RESOLVED'].map((st) => (
                <button
                  key={st}
                  disabled={updating || currentStatus === st}
                  onClick={() => handleStatusChange(st)}
                  className={`text-[11px] py-1.5 px-2 rounded-lg border font-semibold transition ${
                    currentStatus === st
                      ? 'bg-orange-500/20 text-orange-300 border-orange-500/40'
                      : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  {st.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition"
        >
          Close View
        </button>
      </div>
    </div>
  );
};
