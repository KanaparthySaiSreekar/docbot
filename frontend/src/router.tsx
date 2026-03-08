import { lazy, Suspense } from 'react';
import { createBrowserRouter } from 'react-router-dom';
import { AuthGuard } from '@/layouts/AuthGuard';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { PageSkeleton } from '@/components/ui/Skeleton';

// Lazy-loaded pages
const LandingPage = lazy(() => import('@/pages/landing/LandingPage'));
const LoginPage = lazy(() => import('@/pages/landing/LoginPage'));
const CalendarPage = lazy(() => import('@/pages/dashboard/CalendarPage'));
const HistoryPage = lazy(() => import('@/pages/dashboard/HistoryPage'));
const PrescriptionsPage = lazy(() => import('@/pages/dashboard/PrescriptionsPage'));
const SettingsPage = lazy(() => import('@/pages/dashboard/SettingsPage'));

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageSkeleton />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <Suspense fallback={<div className="min-h-screen gradient-hero" />}>
        <LandingPage />
      </Suspense>
    ),
  },
  {
    path: '/login',
    element: (
      <Suspense fallback={<div className="min-h-screen gradient-hero" />}>
        <LoginPage />
      </Suspense>
    ),
  },
{
    element: <AuthGuard />,
    children: [
      {
        element: <DashboardLayout />,
        children: [
          {
            path: '/dashboard',
            element: <SuspenseWrapper><CalendarPage /></SuspenseWrapper>,
          },
          {
            path: '/dashboard/history',
            element: <SuspenseWrapper><HistoryPage /></SuspenseWrapper>,
          },
          {
            path: '/dashboard/prescriptions',
            element: <SuspenseWrapper><PrescriptionsPage /></SuspenseWrapper>,
          },
          {
            path: '/dashboard/settings',
            element: <SuspenseWrapper><SettingsPage /></SuspenseWrapper>,
          },
        ],
      },
    ],
  },
]);
