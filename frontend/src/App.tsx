import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './pages/Dashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
            <h1 className="text-xl font-semibold text-gray-800">DocBot Dashboard</h1>
            <a href="/auth/logout" className="text-sm text-gray-600 hover:text-gray-800">
              Logout
            </a>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-6">
          <Dashboard />
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
