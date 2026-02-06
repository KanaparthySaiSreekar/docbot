import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import type { Appointment, FailedRefund, ScheduleSettings } from '../types';
import { format } from 'date-fns';

export function useAppointments(dateFrom: Date, dateTo: Date) {
  return useQuery({
    queryKey: ['appointments', format(dateFrom, 'yyyy-MM-dd'), format(dateTo, 'yyyy-MM-dd')],
    queryFn: () => apiClient.get<Appointment[]>(
      `/api/appointments?date_from=${format(dateFrom, 'yyyy-MM-dd')}&date_to=${format(dateTo, 'yyyy-MM-dd')}`
    ),
    staleTime: 30000,  // 30 seconds
  });
}

export function useAppointmentsHistory(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ['appointments', 'history', limit, offset],
    queryFn: () => apiClient.get<Appointment[]>(
      `/api/appointments/history?limit=${limit}&offset=${offset}`
    ),
  });
}

export function useFailedRefunds() {
  return useQuery({
    queryKey: ['refunds', 'failed'],
    queryFn: () => apiClient.get<FailedRefund[]>('/api/refunds/failed'),
    refetchInterval: 60000,  // Refetch every minute
  });
}

export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => apiClient.get<ScheduleSettings>('/api/settings'),
    staleTime: 300000,  // 5 minutes
  });
}
