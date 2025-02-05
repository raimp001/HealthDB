import { useAuth } from '../context/AuthContext';
import DataOverview from './DataOverview';
import ProtocolStatus from './ProtocolStatus';

export default function ResearcherDashboard() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Research Collaboration Portal
          </h1>
          <p className="mt-1 text-sm text-gray-600">
            {user.institution.name} - {user.role}
          </p>
        </div>
      </header>

      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Protocol Status */}
            <div className="col-span-1">
              <ProtocolStatus />
            </div>

            {/* Data Overview */}
            <div className="col-span-2">
              <DataOverview />
            </div>

            {/* Recent Activity */}
            <div className="col-span-full">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
                {/* Activity timeline component */}
              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
} 