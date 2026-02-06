import { useMutation, useQueryClient } from '@tanstack/react-query';

// Get CSRF token from cookie
function getCSRFToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

// POST with CSRF token
async function postWithCSRF<T>(path: string, data?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': getCSRFToken(),
    },
    body: data ? JSON.stringify(data) : undefined,
  });

  if (response.status === 401) {
    window.location.href = '/';
    throw new Error('Not authenticated');
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}

export function useCancelAppointment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (appointmentId: string) =>
      postWithCSRF<{ status: string }>(`/api/appointments/${appointmentId}/cancel`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      queryClient.invalidateQueries({ queryKey: ['refunds'] });
    },
  });
}

export function useRetryRefund() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (refundId: string) =>
      postWithCSRF<{ status: string }>(`/api/refunds/${refundId}/retry`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['refunds'] });
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
    },
  });
}

export function useResendConfirmation() {
  return useMutation({
    mutationFn: (appointmentId: string) =>
      postWithCSRF<{ status: string }>(`/api/appointments/${appointmentId}/resend`),
  });
}
