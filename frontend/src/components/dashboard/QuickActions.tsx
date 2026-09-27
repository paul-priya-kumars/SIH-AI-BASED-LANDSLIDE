import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Map, Route, Camera, ArrowRight, ShieldCheck, RefreshCw, AlertTriangle } from 'lucide-react';

export const QuickActions: React.FC = () => {
  const actions = [
    {
      title: 'View Risk Map',
      description: 'Explore interactive GIS zonation layers and spatial hazard polygons.',
      icon: Map,
      href: '/risk-map',
      accent: 'from-orange-500/20 to-amber-500/10 border-orange-500/30 text-orange-400',
      btnColor: 'bg-orange-600 hover:bg-orange-500 text-white',
    },
    {
      title: 'Check Route Safety',
      description: 'Analyze mountain passes and compare safe vs hazardous corridors.',
      icon: Route,
      href: '/route',
      accent: 'from-blue-500/20 to-indigo-500/10 border-blue-500/30 text-blue-400',
      btnColor: 'bg-blue-600 hover:bg-blue-500 text-white',
    },
    {
      title: 'Report Field Hazard',
      description: 'Capture GPS location, photograph rockfalls or fissures, and alert authorities.',
      icon: Camera,
      href: '/report',
      accent: 'from-red-500/20 to-rose-500/10 border-red-500/30 text-red-400',
      btnColor: 'bg-red-600 hover:bg-red-500 text-white',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {actions.map((act) => {
        const Icon = act.icon;
        return (
          <Link
            key={act.title}
            to={act.href}
            className={`group p-5 rounded-3xl border bg-gradient-to-br transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${act.accent} flex flex-col justify-between`}
          >
            <div className="flex-1 flex-col">
              <div className="flex items-center justify-center mb-4">
                <div className="w-12 h-12 rounded-2xl bg-slate-900/80 border border-white/10 flex items-center justify-center">
                  <Icon className="w-6 h-6" />
                </div>
              </div>
              <h3 className="text-lg font-bold text-white mb-3 flex items-center justify-between">
                <span>{act.title}</span>
                <ArrowRight className="w-4 h-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-slate-300" />
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed flex-1 mb-4">
                {act.description}
              </p>
            </div>

            <div className={`mt-4 inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-semibold shadow-md transition ${act.btnColor} hover:-translate-y-0.5`}>
              <span>Launch {act.title}</span>
            </div>
          </Link>
        );
      })}
    </div>
  );
};