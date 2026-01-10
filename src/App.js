import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Pages
import LandingPage from './pages/LandingPage';
import PatientPortal from './pages/PatientPortal';
import ResearcherDashboard from './pages/ResearcherDashboard';
import DataMarketplace from './pages/DataMarketplace';
import Login from './pages/Login';
import Register from './pages/Register';
import ForPatients from './pages/ForPatients';
import ForResearchers from './pages/ForResearchers';

// Components
import Navbar from './components/Navbar';
import Footer from './components/Footer';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            {/* Public info pages */}
            <Route path="/patients" element={<ForPatients />} />
            <Route path="/researchers" element={<ForResearchers />} />
            {/* Authenticated dashboards */}
            <Route path="/patient" element={<PatientPortal />} />
            <Route path="/research" element={<ResearcherDashboard />} />
            {/* Other pages */}
            <Route path="/marketplace" element={<DataMarketplace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
          </Routes>
        </main>
        <Footer />
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;
