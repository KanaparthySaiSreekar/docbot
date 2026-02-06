import { useMemo } from 'react';
import { format, addDays, startOfWeek, isSameDay } from 'date-fns';
import type { Appointment } from '../../types';
import { AppointmentCard } from '../AppointmentCard';

interface Props {
  date: Date;
  appointments: Appointment[];
  onCancelAppointment?: (id: string) => void;
}

export function WeekView({ date, appointments, onCancelAppointment }: Props) {
  const weekStart = startOfWeek(date, { weekStartsOn: 1 }); // Monday

  const days = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
  }, [weekStart]);

  const appointmentsByDay = useMemo(() => {
    const map: Record<string, Appointment[]> = {};
    days.forEach(d => {
      const dateStr = format(d, 'yyyy-MM-dd');
      map[dateStr] = appointments.filter(a => a.appointment_date === dateStr);
    });
    return map;
  }, [appointments, days]);

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="grid grid-cols-7 border-b">
        {days.map(day => (
          <div
            key={day.toISOString()}
            className={`px-2 py-3 text-center border-r last:border-r-0 ${
              isSameDay(day, new Date()) ? 'bg-blue-50' : ''
            }`}
          >
            <div className="text-sm text-gray-500">{format(day, 'EEE')}</div>
            <div className="text-lg font-semibold">{format(day, 'd')}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7 min-h-[500px]">
        {days.map(day => {
          const dateStr = format(day, 'yyyy-MM-dd');
          const dayAppts = appointmentsByDay[dateStr] || [];

          return (
            <div
              key={day.toISOString()}
              className="border-r last:border-r-0 p-2 space-y-2 overflow-y-auto max-h-[500px]"
            >
              {dayAppts.length === 0 ? (
                <div className="text-xs text-gray-400 text-center py-4">No appointments</div>
              ) : (
                dayAppts
                  .sort((a, b) => a.slot_time.localeCompare(b.slot_time))
                  .map(appt => (
                    <AppointmentCard
                      key={appt.id}
                      appointment={appt}
                      onCancel={onCancelAppointment}
                      compact
                    />
                  ))
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
