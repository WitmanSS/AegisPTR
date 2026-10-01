import { Suspense, lazy, useEffect, useRef, useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Dashboard } from './components/Dashboard';
import TargetBulkUploader from './components/TargetBulkUploader';
import { WorkspacePage } from './components/WorkspacePage';
import { OperationsBoard } from './components/OperationsBoard';
import { FindingsExplorer } from './components/FindingsExplorer';
import { AICopilot } from './components/AICopilot';
const AttackSurfaceGraph = lazy(() => import('./components/AttackSurfaceGraph').then((module) => ({ default: module.AttackSurfaceGraph })));
import { getResource, login, setAccessToken } from './services/api';

const navigation = [
  { label: 'Command center', path: '/', glyph: '⌁', section: 'OPERATE' },
  { label: 'Assessments', path: '/assessments', glyph: '◈', section: 'OPERATE' },
  { label: 'Targets & scope', path: '/targets/bulk', glyph: '◎', section: 'OPERATE' },
  { label: 'Operations', path: '/operations', glyph: '↗', section: 'OPERATE' },
  { label: 'Attack surface', path: '/attack-surface', glyph: '⌘', section: 'UNDERSTAND' },
  { label: 'Findings', path: '/findings', glyph: '◉', section: 'UNDERSTAND' },
  { label: 'Risk center', path: '/risk', glyph: '△', section: 'UNDERSTAND' },
  { label: 'Remediation', path: '/remediation', glyph: '✓', section: 'RESOLVE' },
  { label: 'Retesting', path: '/retesting', glyph: '↻', section: 'RESOLVE' },
  { label: 'AI copilot', path: '/ai', glyph: '✦', section: 'RESOLVE' },
  { label: 'Monitoring', path: '/monitoring', glyph: '◌', section: 'REPORT' },
  { label: 'Reports', path: '/reports', glyph: '▤', section: 'REPORT' },
];

function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{ title: string; detail: string; path: string; key: string }>>([]);
  const [searching, setSearching] = useState(false);
  const commands = [
    { label: 'Open command center', path: '/' },
    { label: 'Add targets to scope', path: '/targets/bulk' },
    { label: 'Review active operations', path: '/operations' },
    { label: 'Investigate findings', path: '/findings' },
    { label: 'Open AI copilot', path: '/ai' },
  ].filter((command) => command.label.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    if (!open || query.trim().length < 2) return;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setSearching(true);
      const sources = [
        { path: '/api/assessments', route: '/assessments', label: 'Assessment' },
        { path: '/api/targets/?limit=100', route: '/attack-surface', label: 'Target' },
        { path: '/api/findings', route: '/findings', label: 'Finding' },
        { path: '/api/tasks', route: '/operations', label: 'Operation' },
        { path: '/api/remediation/plans', route: '/remediation', label: 'Remediation' },
        { path: '/api/retests', route: '/retesting', label: 'Retest' },
      ];
      const results = await Promise.allSettled(sources.map((source) => getResource<unknown>(source.path).then((value) => ({ source, value }))));
      if (cancelled) return;
      const normalized = results.flatMap((result) => {
        if (result.status !== 'fulfilled' || !Array.isArray(result.value.value)) return [];
        const { source, value } = result.value;
        return value.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object'))
          .filter((item) => JSON.stringify(item).toLowerCase().includes(query.trim().toLowerCase()))
          .slice(0, 5)
          .map((item, index) => ({
            title: String(item.name ?? item.title ?? item.canonical ?? item.target ?? item.finding_id ?? item.task_id ?? item.plan_id ?? item.retest_id ?? `${source.label} ${index + 1}`),
            detail: `${source.label} · ${String(item.status ?? item.severity ?? item.target_type ?? 'record')}`,
            path: source.route,
            key: String(item.id ?? item.task_id ?? item.finding_id ?? item.plan_id ?? item.retest_id ?? index),
          }));
      });
      setSearchResults(normalized);
      setSearching(false);
    }, 250);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [open, query]);

  useEffect(() => {
    if (!open) { setQuery(''); setSearchResults([]); }
  }, [open]);

  if (!open) return null;
  return (
    <div className="command-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="command-palette" role="dialog" aria-modal="true" aria-label="Command palette" onMouseDown={(event) => event.stopPropagation()}>
        <div className="command-search"><span>⌕</span><input autoFocus value={query} onChange={(event) => { setQuery(event.target.value); if (event.target.value.trim().length < 2) setSearchResults([]); }} placeholder="Search assets, findings, commands..." /><kbd>ESC</kbd></div>
        <div className="command-list">
          {query.trim().length >= 2 && <><small>SECURITY RECORDS {searching ? '/ SEARCHING' : ` / ${searchResults.length} MATCHES`}</small>{searchResults.map((result) => <button key={`${result.path}-${result.key}`} onClick={() => { navigate(result.path); onClose(); }}><span className="search-result"><strong>{result.title}</strong><small>{result.detail}</small></span><span>↵</span></button>)}{!searching && searchResults.length === 0 && <p className="search-empty">No matching records returned by connected endpoints.</p>}</>}
          <small>QUICK ACTIONS</small>
          {commands.map((command) => <button key={command.path} onClick={() => { navigate(command.path); onClose(); }}>{command.label}<span>↵</span></button>)}
        </div>
      </section>
    </div>
  );
}

function Shell() {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [loginPending, setLoginPending] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const shortcutSequence = useRef('');

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setPaletteOpen(true); }
      if (event.key === 'Escape') setPaletteOpen(false);
      const target = event.target as HTMLElement;
      const editingText = target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
      if (editingText) return;
      if (event.key.toLowerCase() === 'g' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        shortcutSequence.current = 'g';
        window.setTimeout(() => { shortcutSequence.current = ''; }, 900);
      } else if (shortcutSequence.current === 'g') {
        const destinations: Record<string, string> = { d: '/', t: '/targets/bulk', f: '/findings', r: '/risk', a: '/ai' };
        const destination = destinations[event.key.toLowerCase()];
        if (destination) { event.preventDefault(); navigate(destination); }
        shortcutSequence.current = '';
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [navigate]);

  const pageName = navigation.find((item) => item.path === location.pathname)?.label ?? 'Workspace';
  const sections = [...new Set(navigation.map((item) => item.section))];

  async function handleLogin(username: string, password: string) {
    setLoginPending(true);
    setLoginError('');
    try {
      const result = await login(username, password);
      setAccessToken(result.access_token);
      setAuthenticated(true);
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : 'Sign-in failed. Check your credentials and API connection.');
    } finally {
      setLoginPending(false);
    }
  }

  if (!authenticated) return <LoginScreen onSubmit={handleLogin} error={loginError} pending={loginPending} />;

  function logout() {
    setAccessToken(null);
    setAuthenticated(false);
    navigate('/');
  }

  return (
    <div className={`app-shell ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className="sidebar">
        <div className="brand-lockup"><div className="brand-mark">A</div><div className="brand-copy"><strong>AEGIS<span>PTR</span></strong><small>SECURITY OPERATIONS</small></div></div>
        <button className="collapse-button" onClick={() => setSidebarCollapsed((value) => !value)} aria-label="Toggle sidebar">{sidebarCollapsed ? '→' : '←'}</button>
        <nav className="side-nav" aria-label="Primary navigation">
          {sections.map((section) => <div className="nav-section" key={section}><small>{section}</small>{navigation.filter((item) => item.section === section).map((item) => <NavLink key={item.path} to={item.path} end={item.path === '/'} className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`} title={item.label}><span className="nav-glyph">{item.glyph}</span><span className="nav-label">{item.label}</span></NavLink>)}</div>)}
        </nav>
        <div className="sidebar-footer"><div className="system-status"><span className="status-dot" /> <span className="nav-label">API connected</span></div><div className="user-chip"><div className="avatar">AE</div><div className="nav-label"><strong>Signed in</strong><small>Session memory only</small></div><button className="logout-button" onClick={logout}>Sign out</button></div></div>
      </aside>
      <div className="workspace">
        <header className="topbar"><button className="mobile-menu" onClick={() => setSidebarCollapsed((value) => !value)} aria-label="Toggle navigation">☰</button><div className="breadcrumb"><span>AEGISPTR</span><i>/</i><strong>{pageName}</strong></div><button className="global-search" onClick={() => setPaletteOpen(true)}><span>⌕</span> Search anything... <kbd>Ctrl K</kbd></button><div className="top-actions"><button className="icon-button" aria-label="Open AI copilot" onClick={() => navigate('/ai')}>✦</button><button className="icon-button" aria-label="Notifications" title="Notifications API not connected">♢</button><div className="assessment-context"><span>Assessment context</span><b>⌄</b></div></div></header>
        <main className="main-workspace"><Routes><Route path="/" element={<Dashboard />} /><Route path="/targets/bulk" element={<TargetBulkUploader />} />{navigation.filter((item) => !['/', '/targets/bulk'].includes(item.path)).map((item) => <Route key={item.path} path={item.path} element={item.label === 'Operations' ? <OperationsBoard /> : item.label === 'Findings' ? <FindingsExplorer /> : item.label === 'AI copilot' ? <AICopilot /> : item.label === 'Attack surface' ? <Suspense fallback={<div className="empty-inline">Loading attack surface graph…</div>}><AttackSurfaceGraph /></Suspense> : <WorkspacePage section={item.label} />} />)}</Routes></main>
      </div>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  );
}

function LoginScreen({ onSubmit, error, pending }: { onSubmit: (username: string, password: string) => void; error: string; pending: boolean }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  return <main className="login-screen"><div className="login-grid" /><section className="login-panel"><div className="login-brand"><div className="brand-mark">A</div><div className="brand-copy"><strong>AEGIS<span>PTR</span></strong><small>SECURITY OPERATIONS</small></div></div><p className="eyebrow">SECURE ACCESS / AUTHORIZED USERS</p><h1>Enter the<br /><em>operations room.</em></h1><p className="login-copy">Sign in to access assessment scope, findings, and security operations.</p><form onSubmit={(event) => { event.preventDefault(); onSubmit(username, password); }}><label>USERNAME<input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required /></label><label>PASSWORD<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>{error && <div className="inline-error" role="alert">{error}</div>}<button className="primary-button login-submit" disabled={pending}>{pending ? 'Authenticating…' : 'Sign in securely'} <span>↗</span></button></form><small className="login-footnote">Bearer token is held in memory and cleared when you sign out or reload.</small></section><div className="login-aside"><small>AEGISPTR / COMMAND CENTER</small><p>SEE<br />WHAT MATTERS.</p><span>Operate within scope.<br />Investigate with evidence.<br />Verify every fix.</span></div></main>;
}

export default function App() {
  return <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><Shell /></BrowserRouter>;
}
