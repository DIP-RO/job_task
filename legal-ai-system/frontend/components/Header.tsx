'use client';

interface HeaderProps {
  apiHealthy: boolean | null;
}

export default function Header({ apiHealthy }: HeaderProps) {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <h1 className="text-4xl font-bold mb-2">Legal AI Document Processing</h1>
        <p className="text-blue-100 text-lg">
          Grounded Document Understanding & Draft Generation
        </p>
        <div className="mt-4 flex items-center gap-2">
          <span
            className={`inline-block w-3 h-3 rounded-full ${
              apiHealthy === true ? 'bg-green-400' : apiHealthy === false ? 'bg-red-400' : 'bg-yellow-400'
            }`}
          ></span>
          <span className="text-sm">
            {apiHealthy === true
              ? 'API Connected ✓'
              : apiHealthy === false
              ? 'API Disconnected ✗'
              : 'Checking...'}
          </span>
        </div>
      </div>
    </header>
  );
}
