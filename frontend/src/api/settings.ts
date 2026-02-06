import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { ScheduleSettings } from '../types';

// Get CSRF token from cookie
function getCSRFToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (schedule: ScheduleSettings) => {
      const response = await fetch('/api/settings', {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCSRFToken(),
        },
        body: JSON.stringify(schedule),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Update failed');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });
}
