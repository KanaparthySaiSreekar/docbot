import { useMemo } from 'react';
import { format } from 'date-fns';
import type { Appointment } from '../../types';
import { AppointmentCard } from '../AppointmentCard';

interface Props {
  date: Date;
  appointments: Appointment[];
}

export function DayView({ date, appointments }: Props) {
  const dateStr = format(date, 'yyyy-MM-dd');

  // Generate time slots from 9:00 to 17:00 in 15-min intervals
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
    appointments
      .filter(a => a.appointment_date === dateStr)
      .forEach(a => { map[a.slot_time] = a; });
    return map;
  }, [appointments, dateStr]);

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b">
        <h2 className="text-lg font-semibold">{format(date, 'EEEE, MMMM d, yyyy')}</h2>
      </div>

      <div className="divide-y">
        {timeSlots.map(slot => {
          const appt = appointmentsBySlot[slot];
          const isBreak = slot >= '13:00' && slot < '14:00';

          return (
            <div key={slot} className={`flex ${isBreak ? 'bg-gray-50' : ''}`}>
              <div className="w-20 px-3 py-2 text-sm text-gray-500 border-r">
                {slot}
              </div>
              <div className="flex-1 p-2 min-h-[60px]">
                {isBreak ? (
                  <span className="text-sm text-gray-400 italic">Break</span>
                ) : appt ? (
                  <AppointmentCard
                    appointment={appt}
                    compact
                  />
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
