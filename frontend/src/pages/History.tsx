import { useState } from 'react';
import { useAppointmentsHistory } from '../api/appointments';
import type { Appointment } from '../types';

const statusColors = {
  PENDING_PAYMENT: 'bg-yellow-100 text-yellow-800',
  CONFIRMED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
  REFUNDED: 'bg-gray-100 text-gray-800',
};

const typeIcons = {
  online: '🎥',
  offline: '🏥',
};

function HistoryCard({ appointment }: { appointment: Appointment }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="font-medium text-lg">{appointment.patient_name}</span>
          <span className="text-gray-500 ml-2">
            {appointment.patient_age}y, {appointment.patient_gender}
          </span>
        </div>
        <span className={`px-2 py-1 rounded text-sm font-medium ${statusColors[appointment.status]}`}>
          {appointment.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
        <div>
          <span className="text-gray-400">Date & Time:</span>
          <div>{appointment.appointment_date} at {appointment.slot_time}</div>
        </div>
        <div>
          <span className="text-gray-400">Type:</span>
          <div>{typeIcons[appointment.consultation_type]} {appointment.consultation_type}</div>
        </div>
        <div>
          <span className="text-gray-400">Phone:</span>
          <div>{appointment.patient_phone}</div>
        </div>
        {appointment.refund_status && (
          <div>
            <span className="text-gray-400">Refund:</span>
            <div className={appointment.refund_status === 'PROCESSED' ? 'text-green-600' : 'text-yellow-600'}>
              {appointment.refund_status}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function History() {
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data: appointments = [], isLoading, isFetching } = useAppointmentsHistory(limit, page * limit);

  const hasMore = appointments.length === limit;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Appointment History</h2>

      {isLoading && (
        <div className="text-center py-8 text-gray-500">Loading history...</div>
      )}

      {!isLoading && appointments.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No past appointments found.
        </div>
      )}

      <div className="space-y-3">
        {appointments.map(appointment => (
          <HistoryCard key={appointment.id} appointment={appointment} />
        ))}
      </div>

      {/* Pagination */}
      {(page > 0 || hasMore) && (
        <div className="flex justify-center gap-4 mt-6">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0 || isFetching}
            className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="py-2 text-gray-600">Page {page + 1}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={!hasMore || isFetching}
            className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}

      {isFetching && !isLoading && (
        <div className="text-center py-4 text-gray-500">Loading...</div>
      )}
    </div>
  );
}
