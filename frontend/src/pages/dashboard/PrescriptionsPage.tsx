import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Pill, Plus, Trash2, FileText, Send, Download, ExternalLink } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { CardSkeleton } from '@/components/ui/Skeleton';
import type { Appointment, Prescription, Medicine, CreatePrescriptionData } from '@/types';

const emptyMedicine: Medicine = { name: '', dosage: '', frequency: '', duration: '', notes: '' };

function PrescriptionFormNew({
  appointment,
  onSubmit,
  isSubmitting,
}: {
  appointment: Appointment;
  onSubmit: (data: CreatePrescriptionData) => void;
  isSubmitting: boolean;
}) {
  const [medicines, setMedicines] = useState<Medicine[]>([{ ...emptyMedicine }]);
  const [instructions, setInstructions] = useState('');

  const addMedicine = () => setMedicines([...medicines, { ...emptyMedicine }]);
  const removeMedicine = (idx: number) => setMedicines(medicines.filter((_, i) => i !== idx));
  const updateMedicine = (idx: number, field: keyof Medicine, value: string) => {
    const updated = [...medicines];
    updated[idx] = { ...updated[idx], [field]: value };
    setMedicines(updated);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validMedicines = medicines.filter(m => m.name.trim());
    if (validMedicines.length === 0) {
      alert('Please add at least one medicine');
      return;
    }
    onSubmit({
      appointment_id: appointment.id,
      medicines: validMedicines,
      instructions: instructions.trim() || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="bg-primary-50/50 border border-primary-100 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center text-sm font-semibold text-primary-700">
            {appointment.patient_name.charAt(0)}
          </div>
          <div>
            <p className="font-medium text-clinical-800">{appointment.patient_name}</p>
            <p className="text-sm text-clinical-500">{appointment.patient_age}y, {appointment.patient_gender} &middot; {appointment.appointment_date}</p>
          </div>
        </div>
      </div>

      <div>
        <div className="flex justify-between items-center mb-3">
          <h4 className="font-medium text-clinical-700 flex items-center gap-2">
            <Pill className="w-4 h-4 text-primary-500" />
            Medicines
          </h4>
          <Button type="button" variant="secondary" size="sm" onClick={addMedicine}>
            <Plus className="w-3.5 h-3.5 mr-1" />
            Add Medicine
          </Button>
        </div>

        {medicines.map((medicine, index) => (
          <Card key={index} variant="outline" padding="sm" hover={false} className="mb-3">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium text-clinical-600">Medicine {index + 1}</span>
              {medicines.length > 1 && (
                <button type="button" onClick={() => removeMedicine(index)} className="text-red-500 hover:text-red-700">
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input placeholder="Medicine Name" value={medicine.name} onChange={e => updateMedicine(index, 'name', e.target.value)} required />
              <Input placeholder="Dosage (e.g., 500mg)" value={medicine.dosage} onChange={e => updateMedicine(index, 'dosage', e.target.value)} required />
              <Input placeholder="Frequency (e.g., 1-0-1)" value={medicine.frequency} onChange={e => updateMedicine(index, 'frequency', e.target.value)} required />
              <Input placeholder="Duration (e.g., 5 days)" value={medicine.duration} onChange={e => updateMedicine(index, 'duration', e.target.value)} required />
            </div>
            <div className="mt-3">
              <Input placeholder="Special notes (optional)" value={medicine.notes || ''} onChange={e => updateMedicine(index, 'notes', e.target.value)} />
            </div>
          </Card>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-clinical-600 mb-1.5">General Instructions</label>
        <textarea
          value={instructions}
          onChange={e => setInstructions(e.target.value)}
          placeholder="Any additional instructions for the patient..."
          className="w-full px-4 py-2.5 bg-white/80 border border-clinical-200 rounded-xl text-clinical-800 placeholder:text-clinical-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all duration-200 h-24 resize-none"
        />
      </div>

      <Button type="submit" loading={isSubmitting} className="w-full" size="lg">
        <Send className="w-4 h-4 mr-2" />
        Create & Send Prescription
      </Button>
    </form>
  );
}

export default function PrescriptionsPage() {
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const queryClient = useQueryClient();

  const { data: appointments, isLoading: loadingAppointments } = useQuery<Appointment[]>({
    queryKey: ['completedAppointments'],
    queryFn: async () => {
      const res = await fetch('/api/appointments/completed', { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to load appointments');
      return res.json();
    },
  });

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
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
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
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
      {/* Left: Create Prescription */}
      <Card variant="solid" padding="lg" hover={false}>
        <h3 className="text-lg font-display font-semibold text-clinical-800 mb-5 flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary-500" />
          Create New Prescription
        </h3>

        {loadingAppointments ? (
          <CardSkeleton />
        ) : appointments?.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No Pending Prescriptions"
            description="All completed appointments have prescriptions."
          />
        ) : (
          <div className="space-y-4">
            <Select
              label="Select Patient"
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
            </Select>

            {selectedAppointment && (
              <PrescriptionFormNew
                appointment={selectedAppointment}
                onSubmit={data => createMutation.mutate(data)}
                isSubmitting={createMutation.isPending}
              />
            )}
          </div>
        )}
      </Card>

      {/* Right: Prescription History */}
      <Card variant="solid" padding="lg" hover={false}>
        <h3 className="text-lg font-display font-semibold text-clinical-800 mb-5 flex items-center gap-2">
          <Pill className="w-5 h-5 text-primary-500" />
          Prescription History
        </h3>

        {loadingPrescriptions ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)}
          </div>
        ) : prescriptions?.length === 0 ? (
          <EmptyState
            icon={Pill}
            title="No Prescriptions Yet"
            description="Prescriptions you create will appear here."
          />
        ) : (
          <div className="space-y-3">
            {prescriptions?.map(rx => (
              <div key={rx.id} className="glass-card p-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center text-sm font-medium text-primary-700">
                      {rx.patient_name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-clinical-800">{rx.patient_name}</p>
                      <p className="text-xs text-clinical-400">{rx.created_at.split('T')[0]}</p>
                    </div>
                  </div>
                  <Badge variant={rx.whatsapp_sent ? 'confirmed' : 'pending'}>
                    {rx.whatsapp_sent ? 'Sent' : 'Pending'}
                  </Badge>
                </div>
                <div className="mt-2">
                  <a
                    href={rx.download_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download PDF
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
