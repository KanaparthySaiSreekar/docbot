import { Navigate, Outlet } from 'react-router-dom';
import { useCurrentUser } from '@/api/auth';
import { PageSkeleton } from '@/components/ui/Skeleton';

export function AuthGuard() {
  const { data: user, isLoading, isError } = useCurrentUser();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8fafb]">
        <div className="w-full max-w-5xl px-8">
          <PageSkeleton />
        </div>
      </div>
    );
  }

  if (isError || !user) {
    return <Navigate to="/auth/login" replace />;
  }

  return <Outlet />;
}
