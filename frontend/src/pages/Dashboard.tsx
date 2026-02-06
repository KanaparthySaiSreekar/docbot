import { useState, useMemo } from 'react';
import { addDays, addWeeks, subDays, subWeeks, startOfWeek, endOfWeek } from 'date-fns';
import { DayView } from '../components/Calendar/DayView';
import { WeekView } from '../components/Calendar/WeekView';
import { useAppointments } from '../api/appointments';
import type { CalendarView } from '../types';

export function Dashboard() {
  const [view, setView] = useState<CalendarView>('day');
  const [selectedDate, setSelectedDate] = useState(new Date());

  // Calculate date range based on view
  const { dateFrom, dateTo } = useMemo(() => {
    if (view === 'day') {
      return { dateFrom: selectedDate, dateTo: selectedDate };
    } else {
      const weekStart = startOfWeek(selectedDate, { weekStartsOn: 1 });
      return { dateFrom: weekStart, dateTo: endOfWeek(selectedDate, { weekStartsOn: 1 }) };
    }
  }, [view, selectedDate]);

  const { data: appointments = [], isLoading, error } = useAppointments(dateFrom, dateTo);

  const handlePrev = () => {
    setSelectedDate(prev => view === 'day' ? subDays(prev, 1) : subWeeks(prev, 1));
  };

  const handleNext = () => {
    setSelectedDate(prev => view === 'day' ? addDays(prev, 1) : addWeeks(prev, 1));
  };

  const handleToday = () => {
    setSelectedDate(new Date());
  };

  const handleCancelAppointment = (id: string) => {
    // Will be implemented in next plan
    console.log('Cancel appointment:', id);
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <button
            onClick={() => setView('day')}
            className={`px-4 py-2 rounded ${view === 'day' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Day
          </button>
          <button
            onClick={() => setView('week')}
            className={`px-4 py-2 rounded ${view === 'week' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Week
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={handlePrev} className="p-2 hover:bg-gray-100 rounded">
            ←
          </button>
          <button
            onClick={handleToday}
            className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
          >
            Today
          </button>
          <button onClick={handleNext} className="p-2 hover:bg-gray-100 rounded">
            →
          </button>
        </div>
      </div>

      {/* Loading/Error states */}
      {isLoading && <div className="text-center py-8 text-gray-500">Loading appointments...</div>}
      {error && <div className="text-center py-8 text-red-500">Failed to load appointments</div>}

      {/* Calendar View */}
      {!isLoading && !error && (
        view === 'day' ? (
          <DayView
            date={selectedDate}
            appointments={appointments}
            onCancelAppointment={handleCancelAppointment}
          />
        ) : (
          <WeekView
            date={selectedDate}
            appointments={appointments}
            onCancelAppointment={handleCancelAppointment}
          />
        )
      )}
    </div>
  );
}
