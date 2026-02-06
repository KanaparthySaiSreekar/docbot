import type { Appointment } from '../types';

interface Props {
  appointment: Appointment;
  onCancel?: (id: string) => void;
  compact?: boolean;
}

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

export function AppointmentCard({ appointment, onCancel, compact = false }: Props) {
  const handleJoinMeet = () => {
    if (appointment.google_meet_link) {
      window.open(appointment.google_meet_link, '_blank');
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-3 ${compact ? 'text-sm' : ''}`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="font-medium">{appointment.patient_name}</span>
          <span className="text-gray-500 ml-2">
            {appointment.patient_age}y, {appointment.patient_gender}
          </span>
        </div>
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColors[appointment.status]}`}>
          {appointment.status}
        </span>
      </div>

      <div className="text-gray-600 text-sm mb-2">
        <span>{typeIcons[appointment.consultation_type]} {appointment.consultation_type}</span>
        <span className="mx-2">|</span>
        <span>{appointment.slot_time}</span>
        <span className="mx-2">|</span>
        <span>{appointment.patient_phone}</span>
      </div>

      {appointment.refund_status && (
        <div className={`text-xs mb-2 ${appointment.refund_status === 'FAILED' ? 'text-red-600' : 'text-yellow-600'}`}>
          Refund: {appointment.refund_status}
        </div>
      )}

      <div className="flex gap-2 mt-2">
        {appointment.consultation_type === 'online' &&
         appointment.status === 'CONFIRMED' &&
         appointment.google_meet_link && (
          <button
            onClick={handleJoinMeet}
            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          >
            Join Meet
          </button>
        )}

        {(appointment.status === 'CONFIRMED' || appointment.status === 'PENDING_PAYMENT') && onCancel && (
          <button
            onClick={() => onCancel(appointment.id)}
            className="px-3 py-1 bg-red-100 text-red-700 text-sm rounded hover:bg-red-200"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
