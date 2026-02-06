interface Props {
  currentPage: 'calendar' | 'history' | 'settings' | 'prescriptions';
  onNavigate: (page: 'calendar' | 'history' | 'settings' | 'prescriptions') => void;
}

export function Navigation({ currentPage, onNavigate }: Props) {
  const tabs = [
    { id: 'calendar' as const, label: 'Calendar', icon: '📅' },
    { id: 'history' as const, label: 'History', icon: '📋' },
    { id: 'prescriptions' as const, label: 'Prescriptions', icon: '💊' },
    { id: 'settings' as const, label: 'Settings', icon: '⚙️' },
  ];

  return (
    <nav className="flex gap-1 mb-6 border-b">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onNavigate(tab.id)}
          className={`px-4 py-2 font-medium transition-colors ${
            currentPage === tab.id
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          {tab.icon} {tab.label}
        </button>
      ))}
    </nav>
  );
}
