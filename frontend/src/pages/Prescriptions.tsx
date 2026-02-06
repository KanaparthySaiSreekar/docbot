import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PrescriptionForm } from '../components/PrescriptionForm';
import type { Appointment, Prescription, CreatePrescriptionData } from '../types';

export function Prescriptions() {
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const queryClient = useQueryClient();

  // Fetch completed appointments without prescriptions
  const { data: appointments, isLoading: loadingAppointments } = useQuery<Appointment[]>({
    queryKey: ['completedAppointments'],
    queryFn: async () => {
      const res = await fetch('/api/appointments/completed', { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to load appointments');
      return res.json();
    },
  });

  // Fetch prescription history
  const { data: prescriptions, isLoading: loadingPrescriptions } = useQuery<Prescription[]>({
    queryKey: ['prescriptions'],
    queryFn: async () => {
      const res = await fetch('/api/prescriptions', { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to load prescriptions');
      return res.json();
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: CreatePrescriptionData) => {
      const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
      const res = await fetch('/api/prescriptions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to create prescription');
      return res.json();
    },
    onSuccess: () => {
      setSelectedAppointment(null);
      queryClient.invalidateQueries({ queryKey: ['prescriptions'] });
      queryClient.invalidateQueries({ queryKey: ['completedAppointments'] });
    },
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Prescriptions</h2>

      {/* Patient Selection */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Create New Prescription</h3>

        {loadingAppointments ? (
          <p>Loading appointments...</p>
        ) : appointments?.length === 0 ? (
          <p className="text-gray-500">No completed appointments without prescriptions.</p>
        ) : (
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Select Patient</label>
            <select
              className="w-full border rounded-lg p-2"
              value={selectedAppointment?.id || ''}
              onChange={(e) => {
                const appt = appointments?.find(a => a.id === e.target.value);
                setSelectedAppointment(appt || null);
              }}
            >
              <option value="">Select a patient...</option>
              {appointments?.map(appt => (
                <option key={appt.id} value={appt.id}>
                  {appt.patient_name} - {appt.appointment_date} ({appt.consultation_type})
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedAppointment && (
          <PrescriptionForm
            appointment={selectedAppointment}
            onSubmit={(data) => createMutation.mutate(data)}
            isSubmitting={createMutation.isPending}
          />
        )}
      </div>

      {/* Prescription History */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Prescription History</h3>

        {loadingPrescriptions ? (
          <p>Loading...</p>
        ) : prescriptions?.length === 0 ? (
          <p className="text-gray-500">No prescriptions yet.</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-left border-b">
                <th className="pb-2">Patient</th>
                <th className="pb-2">Date</th>
                <th className="pb-2">WhatsApp</th>
                <th className="pb-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {prescriptions?.map(rx => (
                <tr key={rx.id} className="border-b">
                  <td className="py-2">{rx.patient_name}</td>
                  <td className="py-2">{rx.created_at.split('T')[0]}</td>
                  <td className="py-2">
                    {rx.whatsapp_sent ? (
                      <span className="text-green-600">Sent</span>
                    ) : (
                      <span className="text-yellow-600">Pending</span>
                    )}
                  </td>
                  <td className="py-2">
                    <a
                      href={rx.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      Download PDF
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
