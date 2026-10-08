import React from 'react';
import { ShieldCheck, Database, Cpu, ExternalLink } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-slate-800/80 bg-slate-950 py-8 px-4 sm:px-6 lg:px-8 text-xs text-slate-500 mb-16 md:mb-0">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-orange-600/20 border border-orange-600/30 flex items-center justify-center text-orange-400">
            <ShieldCheck className="w-3.5 h-3.5" />
          </div>
          <span className="text-slate-300 font-semibold font-heading">
            GeoShield AI Disaster Monitoring
          </span>
          <span>•</span>
          <span>Phase 1 Full-Stack Platform</span>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-[11px]">
          <span className="flex items-center gap-1.5 text-slate-400">
            <Cpu className="w-3.5 h-3.5 text-orange-400" />
            M1 AI/ML Contract Ready
          </span>
          <span className="flex items-center gap-1.5 text-slate-400">
            <Database className="w-3.5 h-3.5 text-blue-400" />
            M2 GIS Pipeline Ready
          </span>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 text-slate-400 hover:text-white transition underline"
          >
            FastAPI Swagger <ExternalLink className="w-2.5 h-2.5" />
          </a>
        </div>
      </div>
    </footer>
  );
};
