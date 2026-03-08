import { NavLink, useLocation } from 'react-router-dom';
import { Calendar, History, Pill, Settings, X } from 'lucide-react';
import { Logo } from '@/components/icons/Logo';
import { cn } from '@/lib/cn';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

const navItems = [
  { to: '/dashboard', icon: Calendar, label: 'Calendar', end: true },
  { to: '/dashboard/history', icon: History, label: 'History', end: false },
  { to: '/dashboard/prescriptions', icon: Pill, label: 'Prescriptions', end: false },
  { to: '/dashboard/settings', icon: Settings, label: 'Settings', end: false },
];

export function Sidebar({ open, onClose }: SidebarProps) {
  const location = useLocation();

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-50 h-full w-64 glass-sidebar flex flex-col transition-transform duration-300 lg:translate-x-0 lg:static lg:z-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-clinical-100/50">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center">
              <Logo className="w-5 h-5 text-white" />
            </div>
            <span className="font-display font-bold text-lg text-clinical-800">ShivaPuja Homeo</span>
          </div>
          <button onClick={onClose} className="lg:hidden p-1 hover:bg-clinical-100 rounded-lg">
            <X className="w-5 h-5 text-clinical-500" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label, end }) => {
            const isActive = end
              ? location.pathname === to
              : location.pathname.startsWith(to);

            return (
              <NavLink
                key={to}
                to={to}
                end={end}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-primary-50 text-primary-700 shadow-sm'
                    : 'text-clinical-500 hover:text-clinical-700 hover:bg-clinical-50',
                )}
              >
                <Icon className={cn('w-5 h-5', isActive ? 'text-primary-600' : 'text-clinical-400')} />
                {label}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-clinical-100/50">
          <p className="text-xs text-clinical-400">ShivaPuja Homeo v1.0</p>
        </div>
      </aside>
    </>
  );
}
