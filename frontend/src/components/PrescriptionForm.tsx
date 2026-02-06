import { useState } from 'react';
import type { Appointment, Medicine, CreatePrescriptionData } from '../types';

interface Props {
  appointment: Appointment;
  onSubmit: (data: CreatePrescriptionData) => void;
  isSubmitting: boolean;
}

const emptyMedicine: Medicine = {
  name: '',
  dosage: '',
  frequency: '',
  duration: '',
  notes: '',
};

export function PrescriptionForm({ appointment, onSubmit, isSubmitting }: Props) {
  const [medicines, setMedicines] = useState<Medicine[]>([{ ...emptyMedicine }]);
  const [instructions, setInstructions] = useState('');

  const addMedicine = () => {
    setMedicines([...medicines, { ...emptyMedicine }]);
  };

  const removeMedicine = (index: number) => {
    setMedicines(medicines.filter((_, i) => i !== index));
  };

  const updateMedicine = (index: number, field: keyof Medicine, value: string) => {
    const updated = [...medicines];
    updated[index] = { ...updated[index], [field]: value };
    setMedicines(updated);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Filter out empty medicines
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
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-gray-50 p-4 rounded">
        <p><strong>Patient:</strong> {appointment.patient_name}</p>
        <p><strong>Age/Gender:</strong> {appointment.patient_age} / {appointment.patient_gender}</p>
        <p><strong>Date:</strong> {appointment.appointment_date}</p>
      </div>

      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="font-semibold">Medicines</label>
          <button
            type="button"
            onClick={addMedicine}
            className="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200"
          >
            + Add Medicine
          </button>
        </div>

        {medicines.map((medicine, index) => (
          <div key={index} className="border rounded p-4 mb-4 bg-white">
            <div className="flex justify-between mb-2">
              <span className="font-medium">Medicine {index + 1}</span>
              {medicines.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeMedicine(index)}
                  className="text-red-600 text-sm hover:underline"
                >
                  Remove
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Medicine Name"
                value={medicine.name}
                onChange={(e) => updateMedicine(index, 'name', e.target.value)}
                className="border rounded p-2"
                required
              />
              <input
                type="text"
                placeholder="Dosage (e.g., 500mg)"
                value={medicine.dosage}
                onChange={(e) => updateMedicine(index, 'dosage', e.target.value)}
                className="border rounded p-2"
                required
              />
              <input
                type="text"
                placeholder="Frequency (e.g., 1-0-1)"
                value={medicine.frequency}
                onChange={(e) => updateMedicine(index, 'frequency', e.target.value)}
                className="border rounded p-2"
                required
              />
              <input
                type="text"
                placeholder="Duration (e.g., 5 days)"
                value={medicine.duration}
                onChange={(e) => updateMedicine(index, 'duration', e.target.value)}
                className="border rounded p-2"
                required
              />
            </div>
            <input
              type="text"
              placeholder="Special notes (optional)"
              value={medicine.notes || ''}
              onChange={(e) => updateMedicine(index, 'notes', e.target.value)}
              className="border rounded p-2 w-full mt-2"
            />
          </div>
        ))}
      </div>

      <div>
        <label className="block font-semibold mb-2">General Instructions</label>
        <textarea
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          placeholder="Any additional instructions for the patient..."
          className="w-full border rounded p-2 h-24"
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {isSubmitting ? 'Creating Prescription...' : 'Create & Send Prescription'}
      </button>
    </form>
  );
}
