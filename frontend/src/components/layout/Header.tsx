import React from 'react';
import { Menu } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { SearchInput } from '../ui/Input';

interface HeaderProps {
  onMenuClick: () => void;
  title?: string;
  breadcrumbs?: Array<{ label: string; href?: string }>;
}

export const Header: React.FC<HeaderProps> = ({
  onMenuClick,
  title,
  breadcrumbs,
}) => {
  return (
    <header className="sticky top-0 z-30 h-16 bg-white/80 dark:bg-navy-900/80 backdrop-blur-md border-b border-slate-200 dark:border-navy-800 px-4 sm:px-6 flex items-center justify-between transition-colors">
      <div className="flex items-center gap-3">
        {/* Mobile menu toggle */}
        <button
          onClick={onMenuClick}
          className="p-2 -ml-2 rounded-lg text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 lg:hidden focus:outline-none"
          aria-label="Open sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Title or Breadcrumbs */}
        <div className="flex flex-col">
          {breadcrumbs && breadcrumbs.length > 0 ? (
            <nav className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              {breadcrumbs.map((crumb, idx) => (
                <React.Fragment key={crumb.label}>
                  {idx > 0 && <span>/</span>}
                  {crumb.href ? (
                    <a
                      href={crumb.href}
                      className="hover:text-brand-500 dark:hover:text-brand-400 transition-colors"
                    >
                      {crumb.label}
                    </a>
                  ) : (
                    <span className="font-semibold text-slate-900 dark:text-slate-100">
                      {crumb.label}
                    </span>
                  )}
                </React.Fragment>
              ))}
            </nav>
          ) : (
            <h1 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              {title || 'Claim Intelligence Workspace'}
            </h1>
          )}
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* Global Search Bar (hidden on very small screens, visible on md+) */}
        <div className="hidden md:block w-64 lg:w-80">
          <SearchInput />
        </div>

        {/* Theme Toggle (Dark Navy / Light) */}
        <ThemeToggle />
      </div>
    </header>
  );
};
