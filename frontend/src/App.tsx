import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './pages/Dashboard';
import { History } from './pages/History';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

type Page = 'dashboard' | 'history';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex justify-between items-center mb-3">
              <h1 className="text-xl font-semibold text-gray-800">DocBot Dashboard</h1>
              <a href="/auth/logout" className="text-sm text-gray-600 hover:text-gray-800">
                Logout
              </a>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage('dashboard')}
                className={`px-4 py-2 rounded text-sm font-medium ${
                  currentPage === 'dashboard'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setCurrentPage('history')}
                className={`px-4 py-2 rounded text-sm font-medium ${
                  currentPage === 'history'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                History
              </button>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-6">
          {currentPage === 'dashboard' && <Dashboard />}
          {currentPage === 'history' && <History />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
