import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Dashboard } from './components/Dashboard';
import TargetBulkUploader from './components/TargetBulkUploader';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="top-nav">
          <NavLink to="/" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Dashboard
          </NavLink>
          <NavLink to="/targets/bulk" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Bulk Targets
          </NavLink>
        </nav>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/targets/bulk" element={<TargetBulkUploader />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
