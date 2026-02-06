export interface Appointment {
  id: string;
  patient_name: string;
  patient_age: number;
  patient_gender: 'Male' | 'Female' | 'Other';
  patient_phone: string;  // Masked: ****1234
  consultation_type: 'online' | 'offline';
  appointment_date: string;  // YYYY-MM-DD
  slot_time: string;  // HH:MM
  status: 'PENDING_PAYMENT' | 'CONFIRMED' | 'CANCELLED' | 'REFUNDED';
  google_meet_link: string | null;
  refund_status: 'PENDING' | 'PROCESSED' | 'FAILED' | null;
}

export interface FailedRefund {
  id: string;
  appointment_id: string;
  patient_name: string;
  appointment_date: string;
  amount_paise: number;
  status: 'PENDING' | 'FAILED';
  retry_count: number;
  created_at: string;
}

export interface ScheduleSettings {
  working_days: number[];
  start_time: string;
  end_time: string;
  break_start: string;
  break_end: string;
  slot_duration_minutes: number;
}

export type CalendarView = 'day' | 'week';

export interface Medicine {
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
  notes?: string;
}

export interface CreatePrescriptionData {
  appointment_id: string;
  medicines: Medicine[];
  instructions?: string;
}

export interface Prescription {
  id: string;
  appointment_id: string;
  patient_name: string;
  created_at: string;
  whatsapp_sent: boolean;
  download_url: string;
}
