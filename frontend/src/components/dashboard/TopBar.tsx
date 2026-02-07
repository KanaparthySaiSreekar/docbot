import { useLocation } from 'react-router-dom';
import { Menu, LogOut, AlertTriangle } from 'lucide-react';
import { useCurrentUser } from '@/api/auth';
import { useQuery } from '@tanstack/react-query';

interface TopBarProps {
  onMenuClick: () => void;
}

const pageTitles: Record<string, string> = {
  '/dashboard': 'Calendar',
  '/dashboard/history': 'History',
  '/dashboard/prescriptions': 'Prescriptions',
  '/dashboard/settings': 'Settings',
};

interface EmergencyStatus {
  booking_disabled: boolean;
  readonly_dashboard: boolean;
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const location = useLocation();
  const { data: user } = useCurrentUser();
  const title = pageTitles[location.pathname] || 'Dashboard';

  const { data: emergency } = useQuery<EmergencyStatus>({
    queryKey: ['emergencyStatus'],
    queryFn: async () => {
      const res = await fetch('/api/emergency', { credentials: 'include' });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    refetchInterval: 30000,
  });

  const hasEmergency = emergency?.booking_disabled || emergency?.readonly_dashboard;

  return (
    <header className="sticky top-0 z-30 glass-solid">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 hover:bg-clinical-100 rounded-xl"
          >
            <Menu className="w-5 h-5 text-clinical-600" />
          </button>
          <div>
            <h1 className="text-xl font-display font-bold text-clinical-800">{title}</h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {hasEmergency && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 border border-red-200 rounded-xl text-red-700">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-xs font-medium hidden sm:inline">Emergency</span>
            </div>
          )}

          {user && (
            <div className="flex items-center gap-3">
              <div className="hidden sm:block text-right">
                <p className="text-sm font-medium text-clinical-700">{user.name || user.email}</p>
                {user.name && <p className="text-xs text-clinical-500">{user.email}</p>}
              </div>
              {user.picture ? (
                <img
                  src={user.picture}
                  alt=""
                  className="w-9 h-9 rounded-xl object-cover border border-clinical-200"
                />
              ) : (
                <div className="w-9 h-9 rounded-xl bg-primary-100 flex items-center justify-center text-sm font-medium text-primary-700">
                  {(user.name || user.email).charAt(0).toUpperCase()}
                </div>
              )}
            </div>
          )}

          <a
            href="/auth/logout"
            className="p-2 hover:bg-clinical-100 rounded-xl text-clinical-500 hover:text-clinical-700 transition-colors"
            title="Logout"
          >
            <LogOut className="w-5 h-5" />
          </a>
        </div>
      </div>

      {/* Emergency Banner - full width */}
      {hasEmergency && (
        <div className="px-6 pb-3">
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-2.5 text-sm text-red-700">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <div>
                <span className="font-medium">Emergency Mode Active</span>
                {emergency?.booking_disabled && <span className="mx-1">&middot; Bookings disabled</span>}
                {emergency?.readonly_dashboard && <span className="mx-1">&middot; Read-only mode</span>}
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
