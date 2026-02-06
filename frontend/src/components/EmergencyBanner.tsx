import { useQuery } from '@tanstack/react-query';

interface EmergencyStatus {
  booking_disabled: boolean;
  readonly_dashboard: boolean;
}

export function EmergencyBanner() {
  const { data: status } = useQuery<EmergencyStatus>({
    queryKey: ['emergencyStatus'],
    queryFn: async () => {
      const res = await fetch('/api/emergency', { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to load status');
      return res.json();
    },
    refetchInterval: 30000, // Check every 30 seconds
  });

  if (!status) return null;

  const hasEmergency = status.booking_disabled || status.readonly_dashboard;
  if (!hasEmergency) return null;

  return (
    <div className="bg-red-100 border-l-4 border-red-500 p-4 mb-4">
      <div className="flex items-center">
        <span className="text-red-700 font-semibold mr-2">Emergency Mode Active</span>
      </div>
      <ul className="text-red-700 text-sm mt-1">
        {status.booking_disabled && (
          <li>New bookings are disabled</li>
        )}
        {status.readonly_dashboard && (
          <li>Dashboard is in read-only mode (no changes allowed)</li>
        )}
      </ul>
    </div>
  );
}
