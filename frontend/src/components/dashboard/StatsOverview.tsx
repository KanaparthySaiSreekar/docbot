import { Calendar, Clock, Users, AlertCircle } from 'lucide-react';
import { useAppointments } from '@/api/appointments';
import { useFailedRefunds } from '@/api/appointments';

export function StatsOverview() {
  const today = new Date();
  const { data: todayAppts = [] } = useAppointments(today, today);
  const { data: refunds = [] } = useFailedRefunds();

  const confirmed = todayAppts.filter(a => a.status === 'CONFIRMED').length;
  const pending = todayAppts.filter(a => a.status === 'PENDING_PAYMENT').length;
  const total = todayAppts.length;

  const stats = [
    {
      label: "Today's Appointments",
      value: total,
      icon: Calendar,
      color: 'text-primary-600 bg-primary-50',
    },
    {
      label: 'Confirmed',
      value: confirmed,
      icon: Users,
      color: 'text-emerald-600 bg-emerald-50',
    },
    {
      label: 'Pending Payment',
      value: pending,
      icon: Clock,
      color: 'text-amber-600 bg-amber-50',
    },
    {
      label: 'Failed Refunds',
      value: refunds.length,
      icon: AlertCircle,
      color: refunds.length > 0 ? 'text-red-600 bg-red-50' : 'text-clinical-500 bg-clinical-50',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map(({ label, value, icon: Icon, color }) => (
        <div key={label} className="glass-card p-4 flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <p className="text-2xl font-display font-bold text-clinical-800">{value}</p>
            <p className="text-xs text-clinical-500">{label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
