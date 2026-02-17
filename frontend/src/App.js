import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Header from './components/Header';
import LandingPage from './pages/LandingPage';
import CreateCampaign from './pages/CreateCampaign';
import CampaignList from './pages/CampaignList';
import CampaignWorkspace from './pages/CampaignWorkspace';
function NavigationWrapper() {
  const location = useLocation();
  const isWorkspace = location.pathname.startsWith('/workspace');

  return (
    <>
      {!isWorkspace && <Header />}
      <div className={cn("min-h-screen bg-transparent font-sans antialiased text-slate-900", !isWorkspace && "pt-0")}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/create-campaign" element={<CreateCampaign />} />
          <Route path="/active-campaigns" element={<CampaignList type="active" />} />
          <Route path="/inactive-campaigns" element={<CampaignList type="inactive" />} />
          <Route path="/workspace/:campaign_id" element={<CampaignWorkspace />} />
        </Routes>
      </div>
    </>
  );
}

// Helper to provide cn in App if needed, or just use class string
const cn = (...classes) => classes.filter(Boolean).join(' ');

function App() {
  return (
    <Router>
      <NavigationWrapper />
    </Router>
  );
}

export default App;
