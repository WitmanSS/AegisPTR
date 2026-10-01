import { FormEvent, useEffect, useRef, useState } from 'react';
import { apiRequest, getResource } from '../services/api';
import '../ai.css';

type Assessment = { id: string; name: string; status: string; is_authorized: boolean };
type Finding = { finding_id: string; assessment_id: string; title: string; severity: string; risk_score: number; asset?: string | null; status: string; source_tool?: string | null };
type AIStatus = { provider: string; model: string; status: string; mode: string };
type Evidence = { finding_id: string; assessment_id?: string | null; title: string; severity: string; risk_score: number; asset?: string | null; source_tool?: string | null; status?: string; validation_status?: string; evidence?: unknown[]; cve?: string | null };
type CopilotReply = { answer: string; classification: string; provider: string; model: string; provider_status: string; confidence: number | null; evidence: Evidence[]; evidence_count: number; read_only: boolean; actions_executed: string[]; notice?: string | null };
type Message = { role: 'user' | 'assistant'; text: string; reply?: CopilotReply };

const suggestions = [
  'Which findings have the highest risk?',
  'Show critical findings in this assessment.',
  'Why is this asset high risk?',
  'Which observations need validation?',
];

export function AICopilot() {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [provider, setProvider] = useState<AIStatus | null>(null);
  const [assessmentId, setAssessmentId] = useState('');
  const [findingId, setFindingId] = useState('');
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [contextLoading, setContextLoading] = useState(true);
  const [error, setError] = useState('');
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      getResource<Assessment[]>('/api/assessments'),
      getResource<{ items: Finding[] }>('/api/findings/explorer?page=1&size=100'),
      getResource<AIStatus>('/api/ai/status'),
    ]).then((results) => {
      if (!active) return;
      const [assessmentResult, findingResult, statusResult] = results;
      if (assessmentResult.status === 'fulfilled') {
        setAssessments(assessmentResult.value);
        setAssessmentId((current) => current || assessmentResult.value[0]?.id || '');
      }
      if (findingResult.status === 'fulfilled') setFindings(findingResult.value.items ?? []);
      if (statusResult.status === 'fulfilled') setProvider(statusResult.value);
      setContextLoading(false);
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (typeof endRef.current?.scrollIntoView === 'function') {
      endRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages, loading]);

  async function ask(event?: FormEvent<HTMLFormElement>, suggested?: string) {
    event?.preventDefault();
    const question = (suggested ?? prompt).trim();
    if (!question || loading) return;
    setError(''); setPrompt(''); setMessages((current) => [...current, { role: 'user', text: question }]); setLoading(true);
    try {
      const response = await apiRequest('/api/ai/ask', { method: 'POST', body: JSON.stringify({ prompt: question, assessment_id: assessmentId || undefined, finding_id: findingId || undefined }) });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.detail ?? `Copilot request failed (${response.status})`);
      setMessages((current) => [...current, { role: 'assistant', text: body.answer, reply: body as CopilotReply }]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not ask the copilot.');
    } finally { setLoading(false); }
  }

  const selectedFinding = findings.find((finding) => finding.finding_id === findingId);
  const scopedFindings = findings.filter((finding) => !assessmentId || finding.assessment_id === assessmentId);
  const criticalCount = scopedFindings.filter((finding) => finding.severity.toUpperCase() === 'CRITICAL').length;

  return <div className="page-frame ai-workspace">
    <header className="page-heading"><div><p className="eyebrow">PHASE 6 / EVIDENCE-GROUNDED ASSISTANT</p><h1>AI Security Copilot</h1><p className="page-description">Ask about stored assessment evidence. Answers cite findings; actions remain under your control.</p></div><div className={`ai-provider-status ${provider?.status === 'ready' ? 'ready' : 'offline'}`}><i />{provider?.provider ?? 'Checking'} · {provider?.model ?? 'provider'}</div></header>
    <div className="ai-safety-bar"><span>READ ONLY</span><p>Finding text and tool output are untrusted evidence, not instructions. The copilot cannot start scans, change finding state, or create remediation tasks.{provider?.provider === 'openai-compatible' ? ' Matching finding context is sent to the configured remote provider.' : ''}</p><span className="ai-provider-mode">{provider?.mode === 'read_only' ? 'EVIDENCE MODE' : 'MODEL ANALYSIS'}</span></div>
    <div className="ai-layout">
      <section className="ai-chat-panel" aria-label="Copilot conversation">
        <div className="ai-chat-header"><div className="ai-sigil">✦</div><div><strong>Assessment analyst</strong><small>{provider?.status === 'ready' && provider.provider !== 'evidence-only' ? `${provider.provider} / ${provider.model}` : 'Database-backed evidence assistant'}</small></div><span className="status-tag success">NO ACTIONS ENABLED</span></div>
        <div className="ai-messages" aria-live="polite">
          {!messages.length && <div className="ai-welcome"><div className="ai-welcome-mark">✦</div><h2>Ask about the evidence.</h2><p>Answers are grounded in findings saved by the current assessment. If there is no matching record, the copilot will say so.</p><div className="suggestion-list">{suggestions.map((item) => <button key={item} onClick={() => void ask(undefined, item)}>{item}<span>↗</span></button>)}</div></div>}
          {messages.map((message, index) => <article className={`chat-message ${message.role}`} key={`${message.role}-${index}`}><span className="message-author">{message.role === 'user' ? 'YOU' : 'AEGIS / READ-ONLY'}</span><p>{message.text}</p>{message.reply && <div className="ai-answer-meta"><span>{message.reply.classification.replace(/_/g, ' ')}</span><span>{message.reply.evidence_count} evidence record(s)</span><span>{message.reply.read_only ? 'No action executed' : 'Action state unknown'}</span></div>}{message.reply?.notice && <small className="ai-notice">{message.reply.notice}</small>}{message.reply && message.reply.evidence.length > 0 && <div className="ai-citations"><small>EVIDENCE CITED</small>{message.reply.evidence.map((item) => <button key={item.finding_id} onClick={() => { setFindingId(item.finding_id); setAssessmentId(item.assessment_id ?? ''); }}><span className={`severity-pill ${item.severity.toLowerCase()}`}>{item.severity}</span><strong>{item.finding_id} · {item.title}</strong><small>{item.asset || 'Asset not specified'} · risk {item.risk_score} · {item.source_tool || 'unattributed'}</small></button>)}</div>}</article>)}
          {loading && <div className="chat-pending"><span className="ai-sigil">✦</span><span>Retrieving relevant findings…</span></div>}
          <div ref={endRef} />
        </div>
        {error && <div className="inline-error" role="alert">{error}</div>}
        <form className="ai-composer" onSubmit={(event) => void ask(event)}><textarea aria-label="Ask Aegis AI" rows={2} maxLength={2000} value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ask about findings, assets, risk or validation…" onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void ask(); } }} /><div><small>Evidence only · Enter to send · Shift+Enter for a new line</small><button className="primary-button" disabled={!prompt.trim() || loading}>{loading ? 'Working…' : 'Ask'} <span>↗</span></button></div></form>
      </section>
      <aside className="ai-context-panel"><div className="panel-heading"><div><small>LIVE CONTEXT</small><h2>Analysis scope</h2></div><span className="context-lock">▣</span></div><label className="ai-context-select">ASSESSMENT<select aria-label="Copilot assessment context" value={assessmentId} onChange={(event) => { setAssessmentId(event.target.value); setFindingId(''); }}><option value="">All assessments</option>{assessments.map((assessment) => <option key={assessment.id} value={assessment.id}>{assessment.name}</option>)}</select></label><div className="ai-context-metrics"><div><small>FINDINGS LOADED</small><strong>{contextLoading ? '…' : scopedFindings.length}</strong></div><div><small>CRITICAL</small><strong className="critical-text">{contextLoading ? '…' : criticalCount}</strong></div></div><div className="context-divider" /><div className="panel-heading context-findings-heading"><div><small>SELECTED FINDING</small><h2>{selectedFinding ? selectedFinding.finding_id : 'No selection'}</h2></div></div>{selectedFinding ? <button className="selected-context-card" onClick={() => setFindingId('')}><strong>{selectedFinding.title}</strong><span>{selectedFinding.asset || 'Unknown asset'} · risk {selectedFinding.risk_score}</span><small>Click to clear selected finding context</small></button> : <div className="context-hint">Choose a finding in the list below to focus a question on its saved evidence.</div>}<div className="context-finding-list"><small>RECENT HIGH-RISK RECORDS</small>{findings.slice(0, 6).map((finding) => <button className={findingId === finding.finding_id ? 'active' : ''} key={finding.finding_id} onClick={() => { setFindingId(finding.finding_id); setAssessmentId(finding.assessment_id); }}><span className={`finding-severity-mark ${finding.severity.toLowerCase()}`} /><span><strong>{finding.title}</strong><small>{finding.finding_id} · {finding.asset || 'Unknown asset'}</small></span></button>)}{!contextLoading && findings.length === 0 && <p>No persisted findings yet. Ingest assessment observations to build context.</p>}</div><div className="ai-context-foot"><span>MODEL</span><strong>{provider?.status === 'ready' ? provider.model : 'Not configured'}</strong><p>Conversation is held in this browser session and is not persisted.</p></div></aside>
    </div>
  </div>;
}
