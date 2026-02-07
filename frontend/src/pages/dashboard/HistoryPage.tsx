import { useState } from 'react';
import { Video, MapPin, Phone, ChevronLeft, ChevronRight, Clock } from 'lucide-react';
import { useAppointmentsHistory } from '@/api/appointments';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusBadge, Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { CardSkeleton } from '@/components/ui/Skeleton';
import type { Appointment } from '@/types';

function HistoryCardNew({ appointment }: { appointment: Appointment }) {
  const isOnline = appointment.consultation_type === 'online';

  return (
    <Card variant="glass" padding="md">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center text-sm font-semibold text-primary-700">
            {appointment.patient_name.charAt(0)}
          </div>
          <div>
            <span className="font-medium text-clinical-800 text-lg">{appointment.patient_name}</span>
            <span className="text-clinical-400 ml-2 text-sm">
              {appointment.patient_age}y, {appointment.patient_gender}
            </span>
          </div>
        </div>
        <StatusBadge status={appointment.status} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
        <div className="flex items-center gap-2 text-clinical-500">
          <Clock className="w-4 h-4 text-clinical-400" />
          <span>{appointment.appointment_date} at {appointment.slot_time}</span>
        </div>
        <div className="flex items-center gap-2 text-clinical-500">
          {isOnline ? <Video className="w-4 h-4 text-accent-500" /> : <MapPin className="w-4 h-4 text-primary-500" />}
          <span className="capitalize">{appointment.consultation_type}</span>
        </div>
        <div className="flex items-center gap-2 text-clinical-500">
          <Phone className="w-4 h-4 text-clinical-400" />
          <span>{appointment.patient_phone}</span>
        </div>
      </div>

      {appointment.refund_status && (
        <div className="mt-3 pt-3 border-t border-clinical-100/60">
          <Badge variant={appointment.refund_status === 'PROCESSED' ? 'confirmed' : 'pending'}>
            Refund: {appointment.refund_status}
          </Badge>
        </div>
      )}
    </Card>
  );
}

export default function HistoryPage() {
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data: appointments = [], isLoading, isFetching } = useAppointmentsHistory(limit, page * limit);
  const hasMore = appointments.length === limit;

  return (
    <div className="space-y-6">
      {isLoading && (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      )}

      {!isLoading && appointments.length === 0 && (
        <EmptyState
          icon={Clock}
          title="No Past Appointments"
          description="Your appointment history will appear here once you have completed appointments."
        />
      )}

      <div className="space-y-3">
        {appointments.map(appointment => (
          <HistoryCardNew key={appointment.id} appointment={appointment} />
        ))}
      </div>

      {(page > 0 || hasMore) && (
        <div className="flex justify-center items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0 || isFetching}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>
          <span className="px-4 py-2 bg-white border border-clinical-200 rounded-xl text-sm font-medium text-clinical-600">
            Page {page + 1}
          </span>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage(p => p + 1)}
            disabled={!hasMore || isFetching}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      )}

      {isFetching && !isLoading && (
        <div className="text-center py-4 text-clinical-400 text-sm">Loading...</div>
      )}
    </div>
  );
}
