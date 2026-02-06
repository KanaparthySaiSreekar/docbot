import { useState, useEffect } from 'react';
import { useSettings } from '../api/appointments';
import { useUpdateSettings } from '../api/settings';
import type { ScheduleSettings } from '../types';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export function Settings() {
  const { data: settings, isLoading } = useSettings();
  const updateMutation = useUpdateSettings();

  const [formData, setFormData] = useState<ScheduleSettings>({
    working_days: [0, 1, 2, 3, 4, 5],
    start_time: '09:00',
    end_time: '17:00',
    break_start: '13:00',
    break_end: '14:00',
    slot_duration_minutes: 15,
  });

  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const handleDayToggle = (day: number) => {
    setFormData(prev => ({
      ...prev,
      working_days: prev.working_days.includes(day)
        ? prev.working_days.filter(d => d !== day)
        : [...prev.working_days, day].sort(),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    try {
      await updateMutation.mutateAsync(formData);
      setMessage({ type: 'success', text: 'Settings saved successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Update failed' });
    }
  };

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading settings...</div>;
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-semibold mb-6">Working Hours Settings</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Working Days */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Working Days
          </label>
          <div className="flex flex-wrap gap-2">
            {DAYS.map((day, index) => (
              <button
                key={day}
                type="button"
                onClick={() => handleDayToggle(index)}
                className={`px-3 py-2 rounded border ${
                  formData.working_days.includes(index)
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {day.slice(0, 3)}
              </button>
            ))}
          </div>
        </div>

        {/* Working Hours */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Time
            </label>
            <input
              type="time"
              value={formData.start_time}
              onChange={e => setFormData(prev => ({ ...prev, start_time: e.target.value }))}
              className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Time
            </label>
            <input
              type="time"
              value={formData.end_time}
              onChange={e => setFormData(prev => ({ ...prev, end_time: e.target.value }))}
              className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
        </div>

        {/* Break Time */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Break Start
            </label>
            <input
              type="time"
              value={formData.break_start}
              onChange={e => setFormData(prev => ({ ...prev, break_start: e.target.value }))}
              className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Break End
            </label>
            <input
              type="time"
              value={formData.break_end}
              onChange={e => setFormData(prev => ({ ...prev, break_end: e.target.value }))}
              className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800">
          Slot duration is fixed at 15 minutes. Changes to working hours will affect
          future bookings only - existing appointments remain unchanged.
        </div>

        {/* Submit */}
        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={updateMutation.isPending}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </button>

          {message && (
            <span className={message.type === 'success' ? 'text-green-600' : 'text-red-600'}>
              {message.text}
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
