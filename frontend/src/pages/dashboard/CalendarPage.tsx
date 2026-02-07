import { useState, useMemo } from 'react';
import { addDays, addWeeks, subDays, subWeeks, startOfWeek, endOfWeek, format, isSameDay } from 'date-fns';
import { ChevronLeft, ChevronRight, Video, MapPin, Phone, RotateCcw, Send, XCircle } from 'lucide-react';
import { useAppointments, useFailedRefunds } from '@/api/appointments';
import { useCancelAppointment, useResendConfirmation, useRetryRefund } from '@/api/actions';
import { StatsOverview } from '@/components/dashboard/StatsOverview';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/Badge';
import { Badge } from '@/components/ui/Badge';
import { PageSkeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/cn';
import type { Appointment, CalendarView } from '@/types';

function AppointmentCardNew({ appointment, compact = false }: { appointment: Appointment; compact?: boolean }) {
  const cancelMutation = useCancelAppointment();
  const resendMutation = useResendConfirmation();

  const isOnline = appointment.consultation_type === 'online';
  const isActive = appointment.status === 'CONFIRMED' || appointment.status === 'PENDING_PAYMENT';

  const borderColor: Record<string, string> = {
    CONFIRMED: 'border-l-emerald-500',
    PENDING_PAYMENT: 'border-l-amber-500',
    CANCELLED: 'border-l-red-400',
    REFUNDED: 'border-l-clinical-400',
  };

  return (
    <div
      className={cn(
        'glass-card border-l-4 p-4 hover:shadow-card-hover transition-all',
        borderColor[appointment.status] || 'border-l-clinical-300',
        compact && 'p-3',
      )}
    >
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center text-sm font-semibold text-primary-700">
            {appointment.patient_name.charAt(0)}
          </div>
          <div>
            <span className="font-medium text-clinical-800">{appointment.patient_name}</span>
            <span className="text-clinical-400 ml-2 text-sm">
              {appointment.patient_age}y, {appointment.patient_gender}
            </span>
          </div>
        </div>
        <StatusBadge status={appointment.status} />
      </div>

      <div className="flex items-center gap-3 text-sm text-clinical-500 mb-2">
        {isOnline ? <Video className="w-4 h-4 text-accent-500" /> : <MapPin className="w-4 h-4 text-primary-500" />}
        <span className="capitalize">{appointment.consultation_type}</span>
        <span className="text-clinical-300">|</span>
        <span>{appointment.slot_time}</span>
        <span className="text-clinical-300">|</span>
        <Phone className="w-3.5 h-3.5" />
        <span>{appointment.patient_phone}</span>
      </div>

      {appointment.refund_status && (
        <div className="mb-2">
          <Badge variant={appointment.refund_status === 'PROCESSED' ? 'confirmed' : 'pending'}>
            Refund: {appointment.refund_status}
          </Badge>
        </div>
      )}

      {isActive && (
        <div className="flex gap-2 mt-3">
          {isOnline && appointment.google_meet_link && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => window.open(appointment.google_meet_link!, '_blank')}
            >
              <Video className="w-3.5 h-3.5 mr-1.5" />
              Join Meet
            </Button>
          )}
          <Button
            size="sm"
            variant="secondary"
            loading={resendMutation.isPending}
            onClick={() => { if (confirm('Resend confirmation?')) resendMutation.mutate(appointment.id); }}
          >
            <Send className="w-3.5 h-3.5 mr-1.5" />
            Resend
          </Button>
          <Button
            size="sm"
            variant="danger"
            loading={cancelMutation.isPending}
            onClick={() => { if (confirm(`Cancel appointment for ${appointment.patient_name}?`)) cancelMutation.mutate(appointment.id); }}
          >
            <XCircle className="w-3.5 h-3.5 mr-1.5" />
            Cancel
          </Button>
        </div>
      )}
    </div>
  );
}

function DayViewNew({ date, appointments }: { date: Date; appointments: Appointment[] }) {
  const dateStr = format(date, 'yyyy-MM-dd');

  const timeSlots = useMemo(() => {
    const slots: string[] = [];
    for (let hour = 9; hour < 17; hour++) {
      for (let min = 0; min < 60; min += 15) {
        slots.push(`${hour.toString().padStart(2, '0')}:${min.toString().padStart(2, '0')}`);
      }
    }
    return slots;
  }, []);

  const appointmentsBySlot = useMemo(() => {
    const map: Record<string, Appointment | undefined> = {};
    appointments.filter(a => a.appointment_date === dateStr).forEach(a => { map[a.slot_time] = a; });
    return map;
  }, [appointments, dateStr]);

  return (
    <Card variant="solid" padding="none" hover={false}>
      <div className="px-5 py-4 border-b border-clinical-100">
        <h2 className="text-lg font-display font-semibold text-clinical-800">
          {format(date, 'EEEE, MMMM d, yyyy')}
        </h2>
      </div>
      <div className="divide-y divide-clinical-100/60">
        {timeSlots.map(slot => {
          const appt = appointmentsBySlot[slot];
          const isBreak = slot >= '13:00' && slot < '14:00';
          return (
            <div key={slot} className={cn('flex', isBreak && 'bg-clinical-50/50')}>
              <div className="w-20 px-4 py-3 text-sm text-clinical-400 border-r border-clinical-100/60 font-medium">
                {slot}
              </div>
              <div className="flex-1 p-2 min-h-[60px]">
                {isBreak ? (
                  <span className="text-sm text-clinical-300 italic px-2">Break</span>
                ) : appt ? (
                  <AppointmentCardNew appointment={appt} compact />
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function WeekViewNew({ date, appointments }: { date: Date; appointments: Appointment[] }) {
  const weekStart = startOfWeek(date, { weekStartsOn: 1 });
  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)), [weekStart]);

  const appointmentsByDay = useMemo(() => {
    const map: Record<string, Appointment[]> = {};
    days.forEach(d => {
      const ds = format(d, 'yyyy-MM-dd');
      map[ds] = appointments.filter(a => a.appointment_date === ds);
    });
    return map;
  }, [appointments, days]);

  return (
    <Card variant="solid" padding="none" hover={false} className="overflow-hidden">
      <div className="grid grid-cols-7 border-b border-clinical-100">
        {days.map(day => (
          <div
            key={day.toISOString()}
            className={cn(
              'px-2 py-3 text-center border-r border-clinical-100/60 last:border-r-0',
              isSameDay(day, new Date()) && 'bg-primary-50/50',
            )}
          >
            <div className="text-xs text-clinical-400 font-medium">{format(day, 'EEE')}</div>
            <div className={cn(
              'text-lg font-display font-semibold',
              isSameDay(day, new Date()) ? 'text-primary-600' : 'text-clinical-700',
            )}>
              {format(day, 'd')}
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7 min-h-[500px]">
        {days.map(day => {
          const ds = format(day, 'yyyy-MM-dd');
          const dayAppts = appointmentsByDay[ds] || [];
          return (
            <div key={day.toISOString()} className="border-r border-clinical-100/60 last:border-r-0 p-2 space-y-2 overflow-y-auto max-h-[500px]">
              {dayAppts.length === 0 ? (
                <div className="text-xs text-clinical-300 text-center py-4">No appointments</div>
              ) : (
                dayAppts
                  .sort((a, b) => a.slot_time.localeCompare(b.slot_time))
                  .map(appt => <AppointmentCardNew key={appt.id} appointment={appt} compact />)
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function RefundsPanelNew() {
  const { data: refunds = [], isLoading } = useFailedRefunds();
  const retryMutation = useRetryRefund();

  if (isLoading || refunds.length === 0) return null;

  return (
    <Card variant="solid" padding="md" hover={false}>
      <h3 className="font-display font-semibold text-red-700 mb-3 flex items-center gap-2">
        <RotateCcw className="w-4 h-4" />
        Failed Refunds ({refunds.length})
      </h3>
      <div className="space-y-2">
        {refunds.map(refund => (
          <div key={refund.id} className="flex justify-between items-center p-3 bg-red-50/50 border border-red-100 rounded-xl">
            <div>
              <div className="font-medium text-clinical-800">{refund.patient_name}</div>
              <div className="text-sm text-clinical-500">
                {refund.appointment_date} &middot; Rs {refund.amount_paise / 100}
              </div>
              <div className="text-xs text-clinical-400">
                Retries: {refund.retry_count} &middot; {refund.status}
              </div>
            </div>
            <Button
              size="sm"
              variant="danger"
              loading={retryMutation.isPending}
              onClick={() => { if (confirm('Retry this refund?')) retryMutation.mutate(refund.id); }}
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
              Retry
            </Button>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default function CalendarPage() {
  const [view, setView] = useState<CalendarView>('day');
  const [selectedDate, setSelectedDate] = useState(new Date());

  const { dateFrom, dateTo } = useMemo(() => {
    if (view === 'day') {
      return { dateFrom: selectedDate, dateTo: selectedDate };
    }
    const ws = startOfWeek(selectedDate, { weekStartsOn: 1 });
    return { dateFrom: ws, dateTo: endOfWeek(selectedDate, { weekStartsOn: 1 }) };
  }, [view, selectedDate]);

  const { data: appointments = [], isLoading, error } = useAppointments(dateFrom, dateTo);

  return (
    <div className="space-y-6">
      <StatsOverview />

      {/* Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex bg-white border border-clinical-200 rounded-xl p-1 shadow-card">
          <button
            onClick={() => setView('day')}
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-lg transition-all',
              view === 'day' ? 'gradient-primary text-white shadow-sm' : 'text-clinical-600 hover:bg-clinical-50',
            )}
          >
            Day
          </button>
          <button
            onClick={() => setView('week')}
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-lg transition-all',
              view === 'week' ? 'gradient-primary text-white shadow-sm' : 'text-clinical-600 hover:bg-clinical-50',
            )}
          >
            Week
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSelectedDate(prev => view === 'day' ? subDays(prev, 1) : subWeeks(prev, 1))}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSelectedDate(new Date())}
          >
            Today
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSelectedDate(prev => view === 'day' ? addDays(prev, 1) : addWeeks(prev, 1))}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {isLoading && <PageSkeleton />}
      {error && (
        <Card variant="solid" className="text-center py-8 text-red-500">
          Failed to load appointments
        </Card>
      )}

      {!isLoading && !error && (
        view === 'day'
          ? <DayViewNew date={selectedDate} appointments={appointments} />
          : <WeekViewNew date={selectedDate} appointments={appointments} />
      )}

      <RefundsPanelNew />
    </div>
  );
}
