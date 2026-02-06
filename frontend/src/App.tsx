import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './pages/Dashboard';
import { History } from './pages/History';
import { Settings } from './pages/Settings';
import { Navigation } from './components/Navigation';
import { EmergencyBanner } from './components/EmergencyBanner';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

type Page = 'calendar' | 'history' | 'settings';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('calendar');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
            <h1 className="text-xl font-semibold text-gray-800">DocBot Dashboard</h1>
            <a href="/auth/logout" className="text-sm text-gray-600 hover:text-gray-800">
              Logout
            </a>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 py-6">
          <EmergencyBanner />
          <Navigation currentPage={currentPage} onNavigate={setCurrentPage} />

          {currentPage === 'calendar' && <Dashboard />}
          {currentPage === 'history' && <History />}
          {currentPage === 'settings' && <Settings />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
