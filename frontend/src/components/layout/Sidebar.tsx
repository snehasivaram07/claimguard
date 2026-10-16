import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  FileText,
  Network,
  Activity,
  ShieldCheck,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { clsx } from 'clsx';

interface SidebarProps {
  isMobileOpen: boolean;
  setIsMobileOpen: (open: boolean) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean | ((prev: boolean) => boolean)) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isMobileOpen,
  setIsMobileOpen,
  isCollapsed,
  setIsCollapsed,
}) => {
  const { user, logout } = useAuth();

  const navItems = [
    { name: 'Dashboard', to: '/', icon: LayoutDashboard },
    { name: 'Claims Directory', to: '/claims', icon: FileText },
    { name: 'Fraud Rings Explorer', to: '/fraud-rings', icon: Network },
    { name: 'System Health', to: '/system-health', icon: Activity },
    { name: 'Audit Activity', to: '/audit', icon: ShieldCheck },
    { name: 'Settings', to: '/settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 dark:bg-navy-950/80 backdrop-blur-sm lg:hidden"
          onClick={() => setIsMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex flex-col bg-navy-900 border-r border-navy-800 transition-all duration-300 ease-in-out',
          isCollapsed ? 'w-20' : 'w-64',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Logo and Brand Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-navy-800">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex items-center justify-center h-10 w-10 min-w-10 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 text-white shadow-md shadow-brand-500/20">
              <Shield className="h-5 w-5" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col truncate">
                <span className="text-base font-bold tracking-tight text-white">
                  ClaimGuard
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-widest text-brand-400">
                  SIU Intelligence
                </span>
              </div>
            )}
          </div>

          {/* Mobile close button */}
          <button
            onClick={() => setIsMobileOpen(false)}
            className="p-1 rounded-lg text-slate-400 hover:text-white lg:hidden"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setIsMobileOpen(false)}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group select-none',
                    isActive
                      ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-navy-800/80 border border-transparent'
                  )
                }
                title={isCollapsed ? item.name : undefined}
              >
                <Icon className="h-5 w-5 min-w-5 shrink-0 transition-colors group-hover:text-brand-300" />
                {!isCollapsed && <span className="truncate">{item.name}</span>}
              </NavLink>
            );
          })}
        </nav>

        {/* Desktop Collapse Toggle */}
        <div className="hidden lg:flex px-3 py-2 border-t border-navy-800/60 justify-end">
          <button
            onClick={() => setIsCollapsed((prev) => !prev)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-navy-800 transition-colors"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* User Card & Logout Footer */}
        <div className="p-3 border-t border-navy-800 bg-navy-950/40">
          <div
            className={clsx(
              'flex items-center gap-3 p-2 rounded-xl transition-all',
              isCollapsed ? 'justify-center' : 'justify-between'
            )}
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="h-8 w-8 min-w-8 rounded-full bg-navy-800 border border-navy-700 flex items-center justify-center text-xs font-semibold text-brand-300">
                {user?.email?.charAt(0).toUpperCase() || 'U'}
              </div>
              {!isCollapsed && (
                <div className="truncate text-left">
                  <p className="text-xs font-medium text-slate-200 truncate">
                    {user?.email || 'Investigator'}
                  </p>
                  <p className="text-[10px] text-slate-400 uppercase tracking-wider">
                    {user?.role || 'SIU Agent'}
                  </p>
                </div>
              )}
            </div>

            <button
              onClick={() => logout()}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors shrink-0"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
