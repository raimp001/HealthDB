import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { API_URL } from '../lib/api';

const InstitutionDashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [institution, setInstitution] = useState(null);
  const [agreements, setAgreements] = useState([]);
  const [irbProtocols, setIrbProtocols] = useState([]);
  const [emrConnections, setEmrConnections] = useState([]);
  const [collaborations, setCollaborations] = useState([]);
  const [stats, setStats] = useState({});

  const token = sessionStorage.getItem('token');

  const fetchData = useCallback(async () => {
    if (!token) {
      navigate('/login');
      return;
    }
    
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      const [instRes, agreementsRes, irbRes, emrRes, collabRes] = await Promise.all([
        fetch(`${API_URL}/api/institution/profile`, { headers }),
        fetch(`${API_URL}/api/institution/agreements`, { headers }),
        fetch(`${API_URL}/api/institution/irb-protocols`, { headers }),
        fetch(`${API_URL}/api/institution/emr-connections`, { headers }),
        fetch(`${API_URL}/api/institution/collaborations`, { headers })
      ]);

      if (instRes.ok) {
        const instData = await instRes.json();
        setInstitution(instData);
      }
      // Hold the fetched values locally. Deriving the stats from the state
      // variables instead read the *previous* render's data, because the
      // setters above have not applied yet, so the counts were always one
      // fetch behind (all zeros on first load).
      const agreementData = agreementsRes.ok ? await agreementsRes.json() : [];
      const irbData = irbRes.ok ? await irbRes.json() : [];
      const emrData = emrRes.ok ? await emrRes.json() : [];
      const collabData = collabRes.ok ? await collabRes.json() : [];

      setAgreements(agreementData);
      setIrbProtocols(irbData);
      setEmrConnections(emrData);
      setCollaborations(collabData);

      setStats({
        activeAgreements: agreementData.filter(a => a.status === 'signed' || a.status === 'approved').length,
        pendingAgreements: agreementData.filter(a => a.status === 'pending' || a.status === 'under_review').length,
        approvedIRBs: irbData.filter(p => p.status === 'approved').length,
        activeStudies: collabData.filter(c => c.status === 'active').length,
      });
    } catch (err) {
      console.error('Error fetching institution data:', err);
    } finally {
      setLoading(false);
    }
  }, [token, navigate, agreements, irbProtocols, collaborations]);

  useEffect(() => {
    fetchData();
  }, []);

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'irb', label: 'IRB Protocols' },
    { id: 'agreements', label: 'Agreements' },
    { id: 'emr', label: 'EMR Integration' },
    { id: 'collaborations', label: 'Collaborations' },
    { id: 'compliance', label: 'Compliance' }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white/40">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white pt-24 pb-12 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Institution Dashboard</h1>
          <p className="text-white/40">{institution?.name || 'Manage regulatory compliance and collaborations'}</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Approved IRBs', value: stats.approvedIRBs ?? 0, color: 'text-green-400' },
            { label: 'Active Agreements', value: stats.activeAgreements ?? 0, color: 'text-blue-400' },
            { label: 'Pending Reviews', value: stats.pendingAgreements ?? 0, color: 'text-yellow-400' },
            { label: 'Active Studies', value: stats.activeStudies ?? 0, color: 'text-purple-400' }
          ].map((stat, i) => (
            <div key={i} className="p-4 border border-white/10 bg-white/[0.02]">
              <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
              <div className="text-xs text-white/40">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-8 overflow-x-auto border-b border-white/10">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'text-white border-b-2 border-white -mb-px'
                  : 'text-white/40 hover:text-white/60'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <OverviewTab 
            agreements={agreements} 
            irbProtocols={irbProtocols} 
            collaborations={collaborations}
            emrConnections={emrConnections}
            onNavigateTab={setActiveTab}
          />
        )}
        {activeTab === 'irb' && <IRBTab protocols={irbProtocols} />}
        {activeTab === 'agreements' && <AgreementsTab agreements={agreements} />}
        {activeTab === 'emr' && <EMRTab connections={emrConnections} />}
        {activeTab === 'collaborations' && <CollaborationsTab collaborations={collaborations} />}
        {activeTab === 'compliance' && <ComplianceTab />}
      </div>
    </div>
  );
};

// Overview Tab
const OverviewTab = ({ agreements, irbProtocols, collaborations, emrConnections, onNavigateTab }) => {
  const recentActivity = [
    ...irbProtocols.slice(0, 3).map(p => ({ type: 'irb', item: p, date: p.submitted_at })),
    ...agreements.slice(0, 3).map(a => ({ type: 'agreement', item: a, date: a.created_at })),
  ].sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 5);

  const pendingActions = [
    ...agreements.filter(a => a.status === 'pending' || a.status === 'under_review'),
    ...irbProtocols.filter(p => p.status === 'revision_required')
  ];

  return (
    <div className="grid md:grid-cols-2 gap-8">
      {/* Pending Actions */}
      <div className="p-6 border border-white/10">
        <h3 className="font-medium mb-4">Action Required</h3>
        {pendingActions.length === 0 ? (
          <p className="text-white/40 text-sm">No pending actions</p>
        ) : (
          <div className="space-y-3">
            {pendingActions.map((item, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                <div>
                  <div className="text-sm">{item.protocol_number || item.document_type}</div>
                  <div className="text-xs text-white/40">{item.status}</div>
                </div>
                <button
                  onClick={() => onNavigateTab(item.protocol_number ? 'irb' : 'agreements')}
                  className="text-xs text-blue-400 hover:underline"
                >
                  Review
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="p-6 border border-white/10">
        <h3 className="font-medium mb-4">Quick Stats</h3>
        <div className="space-y-4">
          <div className="flex justify-between text-sm">
            <span className="text-white/60">EMR Connections</span>
            <span>{emrConnections.length} active</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-white/60">IRB Protocols</span>
            <span>{irbProtocols.length} total</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-white/60">Data Use Agreements</span>
            <span>{agreements.filter(a => a.document_type === 'dua').length}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-white/60">Active Collaborations</span>
            <span>{collaborations.length}</span>
          </div>
        </div>
      </div>

      {/* Expiring Soon */}
      <div className="p-6 border border-white/10">
        <h3 className="font-medium mb-4">Expiring Soon</h3>
        {[...agreements, ...irbProtocols]
          .filter(item => item.expires_at)
          .sort((a, b) => new Date(a.expires_at) - new Date(b.expires_at))
          .slice(0, 5)
          .map((item, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
              <div className="text-sm">{item.protocol_number || item.document_type}</div>
              <div className="text-xs text-yellow-400">
                {new Date(item.expires_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        {[...agreements, ...irbProtocols].filter(item => item.expires_at).length === 0 && (
          <p className="text-white/40 text-sm">No items expiring soon</p>
        )}
      </div>

      {/* Recent Activity */}
      <div className="p-6 border border-white/10">
        <h3 className="font-medium mb-4">Recent Activity</h3>
        {recentActivity.length === 0 ? (
          <p className="text-white/40 text-sm">No recent activity</p>
        ) : (
          <div className="space-y-3">
            {recentActivity.map((activity, i) => (
              <div key={i} className="flex items-center gap-3 py-2 border-b border-white/5 last:border-0">
                <div className={`w-2 h-2 rounded-full ${
                  activity.type === 'irb' ? 'bg-green-400' : 'bg-blue-400'
                }`} />
                <div className="flex-1">
                  <div className="text-sm">{activity.item.protocol_number || activity.item.document_type}</div>
                  <div className="text-xs text-white/40">{activity.item.status}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// IRB Tab
const IRBTab = ({ protocols }) => {
  const [filter, setFilter] = useState('all');

  const filteredProtocols = filter === 'all' 
    ? protocols 
    : protocols.filter(p => p.status === filter);

  const statusColors = {
    approved: 'bg-green-400/10 text-green-400',
    submitted: 'bg-blue-400/10 text-blue-400',
    under_review: 'bg-yellow-400/10 text-yellow-400',
    revision_required: 'bg-orange-400/10 text-orange-400',
    draft: 'bg-white/10 text-white/60'
  };

  const institutionProtocols = protocols;

  return (
    <div>
      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {['all', 'approved', 'under_review', 'draft'].map(status => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-3 py-1.5 text-xs uppercase tracking-wider transition-colors ${
              filter === status
                ? 'bg-white text-black'
                : 'border border-white/20 text-white/60 hover:border-white/40'
            }`}
          >
            {status.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Protocols Table */}
      <div className="border border-white/10">
        <div className="grid grid-cols-12 gap-4 p-4 bg-white/[0.02] text-xs text-white/40 uppercase tracking-wider">
          <div className="col-span-2">Protocol #</div>
          <div className="col-span-4">Study Name</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-2">Approval Date</div>
          <div className="col-span-2">Expires</div>
        </div>
        {institutionProtocols.length === 0 && (
          <div className="p-8 text-center text-white/40 text-sm border-t border-white/5">
            No IRB protocols yet. Protocols submitted for your institution's studies appear here.
          </div>
        )}
        {institutionProtocols.map((protocol, i) => (
          <div 
            key={protocol.id} 
            className="grid grid-cols-12 gap-4 p-4 border-t border-white/5 hover:bg-white/[0.02] cursor-pointer"
          >
            <div className="col-span-2 font-mono text-sm">{protocol.protocol_number}</div>
            <div className="col-span-4 text-sm">{protocol.name}</div>
            <div className="col-span-2">
              <span className={`text-xs px-2 py-1 ${statusColors[protocol.status] || 'bg-white/10'}`}>
                {protocol.status?.replace('_', ' ')}
              </span>
            </div>
            <div className="col-span-2 text-sm text-white/60">
              {protocol.approved_at ? new Date(protocol.approved_at).toLocaleDateString() : '-'}
            </div>
            <div className="col-span-2 text-sm text-white/60">
              {protocol.expires_at ? new Date(protocol.expires_at).toLocaleDateString() : '-'}
            </div>
          </div>
        ))}
      </div>

      {/* Add Protocol Button */}
      <div className="mt-6">
        <Link
          to="/contact"
          className="px-4 py-2 border border-white/20 text-sm hover:bg-white/5 transition-colors"
        >
          Submit New Protocol
        </Link>
      </div>
    </div>
  );
};

// Agreements Tab
const AgreementsTab = ({ agreements }) => {
  const agreementTypes = [
    { type: 'dua', label: 'Data Use Agreements (DUA)', desc: 'Governs how data can be used' },
    { type: 'baa', label: 'Business Associate Agreements (BAA)', desc: 'HIPAA compliance requirement' },
    { type: 'reliance', label: 'Reliance Agreements', desc: 'sIRB reliance with partner sites' },
    { type: 'contract', label: 'Contracts & SOWs', desc: 'Sub-contracts and scopes of work' }
  ];

  const statusColors = {
    signed: 'bg-green-400/10 text-green-400',
    approved: 'bg-green-400/10 text-green-400',
    pending: 'bg-yellow-400/10 text-yellow-400',
    under_review: 'bg-blue-400/10 text-blue-400',
    expired: 'bg-red-400/10 text-red-400',
    draft: 'bg-white/10 text-white/60'
  };

  const institutionAgreements = agreements;

  return (
    <div>
      {/* Agreement Categories */}
      <div className="grid md:grid-cols-4 gap-4 mb-8">
        {agreementTypes.map(type => {
          const count = institutionAgreements.filter(a => a.document_type === type.type).length;
          return (
            <div key={type.type} className="p-4 border border-white/10 hover:border-white/20 cursor-pointer transition-colors">
              <div className="text-2xl font-bold mb-1">{count}</div>
              <div className="text-sm font-medium">{type.label}</div>
              <div className="text-xs text-white/40 mt-1">{type.desc}</div>
            </div>
          );
        })}
      </div>

      {/* Agreements List */}
      <div className="border border-white/10">
        <div className="p-4 bg-white/[0.02] flex justify-between items-center">
          <h3 className="font-medium">All Agreements</h3>
          <Link to="/contact" className="text-xs text-blue-400 hover:underline">New Agreement</Link>
        </div>
        {institutionAgreements.length === 0 && (
          <div className="p-8 text-center text-white/40 text-sm border-t border-white/5">
            No agreements yet. DUAs, BAAs, and reliance agreements for your institution appear here.
          </div>
        )}
        {institutionAgreements.map((agreement, i) => (
          <div 
            key={agreement.id} 
            className="p-4 border-t border-white/5 hover:bg-white/[0.02] cursor-pointer"
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="font-medium text-sm">{agreement.name}</div>
                <div className="text-xs text-white/40 mt-1">{agreement.counterparty}</div>
              </div>
              <span className={`text-xs px-2 py-1 ${statusColors[agreement.status]}`}>
                {agreement.status}
              </span>
            </div>
            <div className="flex gap-6 mt-3 text-xs text-white/40">
              <span>Type: {agreement.document_type?.toUpperCase()}</span>
              {agreement.signed_at && <span>Signed: {new Date(agreement.signed_at).toLocaleDateString()}</span>}
              {agreement.expires_at && <span>Expires: {new Date(agreement.expires_at).toLocaleDateString()}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// EMR Tab
const EMRTab = ({ connections }) => {
  const emrVendors = [
    { name: 'Epic', status: 'available', icon: 'E' },
    { name: 'Cerner', status: 'available', icon: 'C' },
    { name: 'Meditech', status: 'available', icon: 'M' },
    { name: 'athenahealth', status: 'available', icon: 'A' }
  ];

  const institutionConnections = connections;

  const statusColors = {
    active: 'bg-green-400/10 text-green-400',
    pending_baa: 'bg-yellow-400/10 text-yellow-400',
    setup: 'bg-blue-400/10 text-blue-400',
    error: 'bg-red-400/10 text-red-400',
    inactive: 'bg-white/10 text-white/40'
  };

  return (
    <div>
      {/* Active Connections */}
      <div className="mb-8">
        <h3 className="font-medium mb-4">Active Connections</h3>
        {institutionConnections.length === 0 ? (
          <div className="p-8 border border-white/10 text-center">
            <p className="text-white/40 mb-4">No EMR connections configured</p>
            <Link
              to="/contact"
              className="px-4 py-2 bg-white text-black text-sm hover:bg-gray-100 transition-colors"
            >
              Connect EMR
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {institutionConnections.map(conn => (
              <div key={conn.id} className="p-6 border border-white/10">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-white/10 flex items-center justify-center text-xl font-bold">
                      {conn.emr_vendor[0]}
                    </div>
                    <div>
                      <div className="font-medium">{conn.emr_vendor}</div>
                      <div className="text-xs text-white/40">{conn.connection_type?.toUpperCase()}</div>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 ${statusColors[conn.status]}`}>
                    {conn.status}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-white/40 text-xs">Last Sync</div>
                    <div>{conn.last_sync ? new Date(conn.last_sync).toLocaleString() : 'Never'}</div>
                  </div>
                  <div>
                    <div className="text-white/40 text-xs">Patients</div>
                    <div>{conn.patient_count?.toLocaleString() || 0}</div>
                  </div>
                  <div>
                    <div className="text-white/40 text-xs">Connection Type</div>
                    <div>{conn.connection_type}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Available Integrations */}
      <div>
        <h3 className="font-medium mb-4">Available Integrations</h3>
        <div className="grid md:grid-cols-4 gap-4">
          {emrVendors.map(vendor => (
            <div key={vendor.name} className="p-4 border border-white/10 hover:border-white/20 transition-colors cursor-pointer">
              <div className="w-10 h-10 bg-white/10 flex items-center justify-center font-bold mb-3">
                {vendor.icon}
              </div>
              <div className="font-medium text-sm">{vendor.name}</div>
              <div className="text-xs text-green-400 mt-1">Supported</div>
            </div>
          ))}
        </div>
      </div>

      {/* Integration Methods */}
      <div className="mt-8 p-6 border border-white/10">
        <h3 className="font-medium mb-4">Integration Methods</h3>
        <div className="grid md:grid-cols-3 gap-6">
          <div>
            <div className="font-medium text-sm mb-2">FHIR R4</div>
            <p className="text-xs text-white/40">Real-time API access with OAuth 2.0 authentication</p>
          </div>
          <div>
            <div className="font-medium text-sm mb-2">Bulk FHIR</div>
            <p className="text-xs text-white/40">Scheduled batch exports for large datasets</p>
          </div>
          <div>
            <div className="font-medium text-sm mb-2">SFTP</div>
            <p className="text-xs text-white/40">Secure file transfer for flat file imports</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Collaborations Tab
const CollaborationsTab = ({ collaborations }) => {
  const institutionCollaborations = collaborations;

  const statusColors = {
    active: 'bg-green-400/10 text-green-400',
    pending: 'bg-yellow-400/10 text-yellow-400',
    invited: 'bg-blue-400/10 text-blue-400',
    completed: 'bg-white/10 text-white/60'
  };

  return (
    <div>
      {/* Active Collaborations */}
      <div className="border border-white/10">
        <div className="p-4 bg-white/[0.02] flex justify-between items-center">
          <h3 className="font-medium">Study Collaborations</h3>
          <span className="text-xs text-white/40">{institutionCollaborations.length} total</span>
        </div>
        {institutionCollaborations.length === 0 && (
          <div className="p-8 text-center text-white/40 text-sm border-t border-white/5">
            No collaborations yet. Studies you join as a participating site appear here.
          </div>
        )}
        {institutionCollaborations.map((collab, i) => (
          <div 
            key={collab.id} 
            className="p-4 border-t border-white/5 hover:bg-white/[0.02] cursor-pointer"
          >
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="font-medium text-sm">{collab.study_name}</div>
                <div className="text-xs text-white/40 mt-1">PI: {collab.pi}</div>
              </div>
              <span className={`text-xs px-2 py-1 ${statusColors[collab.status]}`}>
                {collab.status}
              </span>
            </div>
            <div className="flex gap-6 mt-3 text-xs">
              <span className="text-white/60">Role: {collab.role}</span>
              <span className="text-white/60">Patients Contributed: {collab.patient_contributed}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Pending Invitations */}
      <div className="mt-8">
        <h3 className="font-medium mb-4">Pending Invitations</h3>
        <div className="p-6 border border-white/10 text-center">
          <p className="text-white/40 text-sm">No pending invitations</p>
        </div>
      </div>

      {/* Partner Sites */}
      <div className="mt-8">
        <h3 className="font-medium mb-4">Partner Sites in Network</h3>
        <div className="grid md:grid-cols-4 gap-4">
          {['Sample Site A', 'Sample Site B', 'Sample Site C', 'Sample Site D'].map((site, i) => (
            <div key={site} className="p-3 border border-white/10 text-sm text-center">
              {site}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Compliance Tab
const ComplianceTab = () => {
  // Nothing here is a certification. These are controls implemented in the
  // platform, stated without dates or attestations, because HealthDB has not
  // completed any third-party audit. Anything unverified is listed as such.
  const implemented = [
    {
      category: 'Access control',
      items: [
        'Roles resolved from the database on every privileged request',
        'Study-scoped authorization for cohort and export access',
        'Separation of duties on regulatory approval',
        'PBKDF2-SHA256 password hashing (600,000 iterations)',
      ],
    },
    {
      category: 'Data protection',
      items: [
        'HIPAA Safe Harbor identifier removal before research access',
        'Small-cell suppression on aggregate results',
        'Consent checked at query time, revocable by the patient',
        'Append-only access log, visible to the patient',
      ],
    },
  ];

  const notInPlace = [
    { name: 'SOC 2 Type II', note: 'No audit commenced' },
    { name: 'HIPAA Business Associate Agreements', note: 'None executed' },
    { name: 'Independent penetration test', note: 'Not performed' },
    { name: 'Security risk assessment', note: 'Not performed' },
    { name: 'GDPR readiness review', note: 'Not assessed' },
    { name: '21 CFR Part 11', note: 'Not assessed' },
    { name: 'IRB reliance agreements', note: 'None executed' },
    { name: 'Workforce compliance training', note: 'Not established' },
  ];

  return (
    <div>
      <div className="p-4 border border-amber-400/30 bg-amber-400/5 mb-8">
        <p className="text-amber-400 text-sm font-medium mb-1">Closed pilot — no certifications held</p>
        <p className="text-white/50 text-sm">
          HealthDB holds no compliance certifications and has no executed BAAs, DUAs, or
          IRB reliance agreements. Do not process real PHI on this platform until those
          are independently verified.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {implemented.map((category) => (
          <div key={category.category} className="p-6 border border-emerald-400/20">
            <h3 className="font-medium mb-4 text-emerald-400">{category.category}</h3>
            <div className="space-y-3">
              {category.items.map((item) => (
                <div key={item} className="flex items-start gap-3 py-1">
                  <span className="text-emerald-400 text-xs mt-1">✓</span>
                  <span className="text-sm text-white/60">{item}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 p-6 border border-white/10">
        <h3 className="font-medium mb-4">Not in place</h3>
        <div className="grid md:grid-cols-2 gap-x-8">
          {notInPlace.map((item) => (
            <div key={item.name} className="flex items-center justify-between py-2 border-b border-white/5">
              <span className="text-sm text-white/60">{item.name}</span>
              <span className="text-xs text-amber-400/60">{item.note}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default InstitutionDashboard;

