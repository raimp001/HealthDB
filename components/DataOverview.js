export default function DataOverview() {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Research Data Summary</h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-600">Total Patients</p>
          <p className="text-2xl font-bold mt-2">1,234</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <p className="text-sm text-gray-600">Active Studies</p>
          <p className="text-2xl font-bold mt-2">15</p>
        </div>
      </div>
    </div>
  );
} 