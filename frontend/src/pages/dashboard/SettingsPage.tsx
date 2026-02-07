import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Clock, CalendarDays, Coffee, Check, AlertCircle } from 'lucide-react';
import { useSettings } from '@/api/appointments';
import { useUpdateSettings } from '@/api/settings';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { PageSkeleton } from '@/components/ui/Skeleton';
import { cn } from '@/lib/cn';
import type { ScheduleSettings } from '@/types';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function SettingsPage() {
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
    if (settings) setFormData(settings);
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
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Update failed' });
    }
  };

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="max-w-3xl space-y-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Working Days */}
        <Card variant="solid" padding="lg" hover={false}>
          <h3 className="text-lg font-display font-semibold text-clinical-800 mb-4 flex items-center gap-2">
            <CalendarDays className="w-5 h-5 text-primary-500" />
            Working Days
          </h3>
          <div className="flex flex-wrap gap-2">
            {DAYS.map((day, index) => (
              <button
                key={day}
                type="button"
                onClick={() => handleDayToggle(index)}
                className={cn(
                  'px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 border',
                  formData.working_days.includes(index)
                    ? 'gradient-primary text-white border-transparent shadow-md'
                    : 'bg-white text-clinical-600 border-clinical-200 hover:bg-clinical-50 hover:border-clinical-300',
                )}
              >
                {day.slice(0, 3)}
              </button>
            ))}
          </div>
        </Card>

        {/* Working Hours */}
        <Card variant="solid" padding="lg" hover={false}>
          <h3 className="text-lg font-display font-semibold text-clinical-800 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary-500" />
            Working Hours
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Start Time"
              type="time"
              value={formData.start_time}
              onChange={e => setFormData(prev => ({ ...prev, start_time: e.target.value }))}
              required
            />
            <Input
              label="End Time"
              type="time"
              value={formData.end_time}
              onChange={e => setFormData(prev => ({ ...prev, end_time: e.target.value }))}
              required
            />
          </div>
        </Card>

        {/* Break Time */}
        <Card variant="solid" padding="lg" hover={false}>
          <h3 className="text-lg font-display font-semibold text-clinical-800 mb-4 flex items-center gap-2">
            <Coffee className="w-5 h-5 text-primary-500" />
            Break Time
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Break Start"
              type="time"
              value={formData.break_start}
              onChange={e => setFormData(prev => ({ ...prev, break_start: e.target.value }))}
              required
            />
            <Input
              label="Break End"
              type="time"
              value={formData.break_end}
              onChange={e => setFormData(prev => ({ ...prev, break_end: e.target.value }))}
              required
            />
          </div>
        </Card>

        {/* Info */}
        <Card variant="outline" padding="sm" hover={false} className="border-accent-200 bg-accent-50/30">
          <div className="flex items-start gap-3 p-2">
            <AlertCircle className="w-5 h-5 text-accent-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-accent-700">
              Slot duration is fixed at 15 minutes. Changes to working hours will affect
              future bookings only — existing appointments remain unchanged.
            </p>
          </div>
        </Card>

        {/* Submit */}
        <div className="flex items-center gap-4">
          <Button type="submit" loading={updateMutation.isPending} size="lg">
            <SettingsIcon className="w-4 h-4 mr-2" />
            Save Changes
          </Button>

          {message && (
            <div className={cn(
              'flex items-center gap-2 text-sm font-medium animate-fade-in',
              message.type === 'success' ? 'text-emerald-600' : 'text-red-600',
            )}>
              {message.type === 'success' ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              {message.text}
            </div>
          )}
        </div>
      </form>
    </div>
  );
}
