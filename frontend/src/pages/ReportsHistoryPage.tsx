import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { HazardReport } from '../types';
import { ReportCard } from '../components/reports/ReportCard';
import { ReportDetailModal } from '../components/reports/ReportDetailModal';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { FileText, Filter, Search, PlusCircle, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';

export const ReportsHistoryPage: React.FC = () => {
  const [reports, setReports] = useState<HazardReport[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedReport, setSelectedReport] = useState<HazardReport | null>(null);

  const loadReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getReports(statusFilter !== 'ALL' ? statusFilter : undefined);
      setReports(data);
    } catch (err) {
      setError('Unable to load citizen reports list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [statusFilter]);

  const handleStatusUpdate = async (reportId: string, newStatus: string) => {
    await api.updateReportStatus(reportId, newStatus);
    // Refresh local list
    setReports((prev) =>
      prev.map((r) => (r.report_id === reportId ? { ...r, status: newStatus as any } : r))
    );
  };

  const filteredReports = reports.filter((report) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      report.report_id.toLowerCase().includes(q) ||
      report.hazard_type.toLowerCase().includes(q) ||
      (report.location_name && report.location_name.toLowerCase().includes(q)) ||
      report.description.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs uppercase tracking-widest font-bold text-orange-400">
              Community Sourced Intelligence
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              REGISTRY
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white font-heading">
            Hazard Field Observations
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Browse and inspect ground reports submitted by local citizens and emergency responders.
          </p>
        </div>

        <Link
          to="/report"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs rounded-xl shadow-md transition"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Submit New Observation</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-3xl glass-card border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search ID, hazard, or landmark..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder:text-slate-500 focus:outline-hidden focus:border-orange-500"
          />
        </div>

        {/* Status Filter buttons */}
        <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto justify-end">
          <span className="text-[11px] text-slate-500 font-semibold mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3" /> Status:
          </span>
          {['ALL', 'PENDING', 'UNDER_REVIEW', 'VERIFIED', 'RESOLVED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`text-[11px] px-2.5 py-1 rounded-lg border font-semibold transition ${
                statusFilter === st
                  ? 'bg-orange-500/20 text-orange-300 border-orange-500/40'
                  : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
            >
              {st.replace('_', ' ')}
            </button>
          ))}
          <button
            onClick={loadReports}
            className="p-1.5 rounded-lg bg-slate-900 text-slate-400 hover:text-white border border-slate-800 transition ml-1"
            title="Refresh List"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Reports Grid */}
      {loading ? (
        <LoadingState message="Fetching registered hazard reports..." className="min-h-[40vh]" />
      ) : error ? (
        <ErrorState message={error} onRetry={loadReports} />
      ) : filteredReports.length === 0 ? (
        <EmptyState
          title="No Hazard Reports Found"
          description="There are currently no observations recorded matching your search query or status filter."
          actionLabel="Submit Observation"
          onAction={() => (window.location.href = '/report')}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredReports.map((report) => (
            <ReportCard
              key={report.id || report.report_id}
              report={report}
              onClick={() => setSelectedReport(report)}
            />
          ))}
        </div>
      )}

      {/* Modal Detail View */}
      <ReportDetailModal
        report={selectedReport}
        onClose={() => setSelectedReport(null)}
        onStatusUpdate={handleStatusUpdate}
      />
    </div>
  );
};
