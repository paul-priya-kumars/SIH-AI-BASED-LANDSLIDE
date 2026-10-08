import React from 'react';
import { MapPin, Calendar, Image as ImageIcon, ChevronRight } from 'lucide-react';
import { HazardReport } from '../../types';
import { StatusBadge } from './StatusBadge';
import { RiskBadge } from '../dashboard/RiskBadge';

interface ReportCardProps {
  report: HazardReport;
  onClick: () => void;
}

export const ReportCard: React.FC<ReportCardProps> = ({ report, onClick }) => {
  const formattedDate = new Date(report.created_at).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  return (
    <div
      onClick={onClick}
      className="p-5 rounded-3xl glass-card glass-card-hover border-slate-800 cursor-pointer flex flex-col justify-between"
    >
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-xs font-mono font-bold text-orange-400">
            REPORT #{report.report_id}
          </span>
          <StatusBadge status={report.status} size="sm" />
        </div>

        <div className="flex items-start justify-between gap-3 mb-2">
          <h4 className="text-base font-bold text-white leading-snug">
            {report.hazard_type}
          </h4>
          <RiskBadge level={report.severity} size="sm" />
        </div>

        <p className="text-xs text-slate-400 line-clamp-2 mb-4 leading-relaxed">
          {report.description}
        </p>
      </div>

      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-slate-500" />
            <span className="truncate max-w-[120px]">{report.location_name || 'Nilgiris'}</span>
          </span>
          <span className="flex items-center gap-1 text-[11px] text-slate-500">
            <Calendar className="w-3 h-3" />
            <span>{formattedDate}</span>
          </span>
        </div>

        <div className="flex items-center gap-1 text-orange-400 font-semibold text-xs group-hover:text-orange-300">
          {report.image_path || report.image_url ? (
            <span title="Photo attached">
              <ImageIcon className="w-3.5 h-3.5 text-slate-400" />
            </span>
          ) : null}
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
};
