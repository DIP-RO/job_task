'use client';

type Tab = 'upload' | 'generate' | 'edit' | 'history';

interface NavigationProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const tabs: { id: Tab; label: string; icon: string }[] = [
  { id: 'upload', label: 'Upload Document', icon: '📤' },
  { id: 'generate', label: 'Generate Draft', icon: '✍️' },
  { id: 'edit', label: 'Record Edit', icon: '📝' },
  { id: 'history', label: 'History', icon: '📋' },
];

export default function Navigation({ activeTab, onTabChange }: NavigationProps) {
  return (
    <div className="container mx-auto px-4 max-w-6xl">
      <div className="flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 px-6 py-3 font-medium whitespace-nowrap transition-all ${
              activeTab === tab.id
                ? 'border-b-2 border-blue-600 text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
