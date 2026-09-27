import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Map, Route, Camera, Bell, FileText } from 'lucide-react';

export const Navigation: React.FC = () => {
  const links = [
    { to: '/', label: 'Home', icon: Home },
    { to: '/risk-map', label: 'Map', icon: Map },
    { to: '/route', label: 'Route', icon: Route },
    { to: '/report', label: 'Report', icon: Camera, primary: true },
    { to: '/reports', label: 'History', icon: FileText },
    { to: '/alerts', label: 'Alerts', icon: Bell },
  ];

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 border-t border-slate-800 bg-slate-950/90 backdrop-blur-lg px-2 py-1.5"
      aria-label="Mobile Navigation"
    >
      <div className="flex items-center justify-around">
        {links.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center justify-center p-1.5 rounded-2xl transition ${
                  item.primary
                    ? 'bg-orange-600 text-white shadow-lg shadow-orange-600/30 px-3 py-1 -mt-3'
                    : isActive
                    ? 'text-orange-400 font-bold'
                    : 'text-slate-400 hover:text-slate-200'
                }`
              }
            >
              <Icon className={item.primary ? 'w-5 h-5' : 'w-4 h-4 mb-0.5'} />
              <span className="text-[10px] font-medium tracking-tight">
                {item.label}
              </span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};
