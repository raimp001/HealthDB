import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Pages
import LandingPage from './pages/LandingPage';
import PatientPortal from './pages/PatientPortal';
import ResearcherDashboard from './pages/ResearcherDashboard';
import DataMarketplace from './pages/DataMarketplace';
import CohortBuilder from './pages/CohortBuilder';
import Login from './pages/Login';
import Register from './pages/Register';
import ForPatients from './pages/ForPatients';
import ForResearchers from './pages/ForResearchers';
import ForInstitutions from './pages/ForInstitutions';
import InstitutionDashboard from './pages/InstitutionDashboard';
import Resources from './pages/Resources';
import Pricing from './pages/Pricing';
import About from './pages/About';
import Contact from './pages/Contact';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';
import PlatformFocusAreas from './pages/PlatformFocusAreas';
import SecurityPostureMap from './pages/SecurityPostureMap';
import DataFlowDiagram from './pages/DataFlowDiagram';
import RepoAnalyzer from './pages/RepoAnalyzer';
import NotFound from './pages/NotFound';

// Components
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import PilotBanner from './components/PilotBanner';
import RequireSession from './components/RequireSession';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

function App() {
  return (
    <Router>
      <ScrollToTop />
      <div className="min-h-screen bg-black flex flex-col pt-20">
        <a href="#main-content" className="skip-link">Skip to content</a>
        <Navbar />
        <PilotBanner />
        <main id="main-content" tabIndex={-1} className="flex-grow">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            {/* Public info pages */}
            <Route path="/patients" element={<ForPatients />} />
            <Route path="/researchers" element={<ForResearchers />} />
            <Route path="/institutions" element={<ForInstitutions />} />
            {/* Authenticated dashboards */}
            <Route path="/patient" element={<RequireSession roles={['patient']}><PatientPortal /></RequireSession>} />
            <Route path="/research" element={<RequireSession roles={['researcher', 'admin']}><ResearcherDashboard /></RequireSession>} />
            <Route path="/institution" element={<RequireSession roles={['institution', 'admin']}><InstitutionDashboard /></RequireSession>} />
            <Route path="/cohort-builder" element={<RequireSession roles={['researcher', 'admin']}><CohortBuilder /></RequireSession>} />
            {/* Platform pages */}
            <Route path="/platform" element={<PlatformFocusAreas />} />
            <Route path="/security-posture" element={<SecurityPostureMap />} />
            <Route path="/data-flow" element={<DataFlowDiagram />} />
            <Route path="/repo-analyzer" element={<RepoAnalyzer />} />
            {/* Other pages */}
            <Route path="/marketplace" element={<DataMarketplace />} />
            <Route path="/resources" element={<Resources />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            {/* Catch-all: unknown URLs must not render the homepage */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <Footer />
        <Toaster position="top-right" />
      </div>
    </Router>
  );
}

export default App;

