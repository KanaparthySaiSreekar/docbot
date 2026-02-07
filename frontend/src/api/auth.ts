import { useQuery } from '@tanstack/react-query';

export interface CurrentUser {
  email: string;
  name?: string;
  picture?: string;
}

export function useCurrentUser() {
  return useQuery<CurrentUser>({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const res = await fetch('/api/me', { credentials: 'include' });
      if (!res.ok) throw new Error('Not authenticated');
      return res.json();
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}
