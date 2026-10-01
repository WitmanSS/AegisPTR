import { ChangeEvent, DragEvent, useEffect, useRef, useState } from 'react';
import { bulkCreate, previewBulk, TargetPreview } from '../services/targets';

type EditableItem = {
  original: string;
  canonical: string;
  type: string;
  validation?: { valid: boolean; errors?: string[] };
  selected: boolean;
};

function readFileTargets(contents: string, filename: string): string {
  const extension = filename.toLowerCase().split('.').pop();
  if (extension === 'json') {
    const parsed: unknown = JSON.parse(contents);
    const entries = Array.isArray(parsed) ? parsed : (parsed as { targets?: unknown[]; items?: unknown[] })?.targets ?? (parsed as { items?: unknown[] })?.items;
    if (!Array.isArray(entries)) throw new Error('JSON file must contain a targets or items array.');
    return entries.map((entry) => typeof entry === 'string' ? entry : String((entry as { target?: unknown; value?: unknown }).target ?? (entry as { value?: unknown }).value ?? '')).filter(Boolean).join('\n');
  }
  if (extension === 'csv') {
    return contents.split(/\r?\n/).map((line) => line.split(',')[0]?.trim().replace(/^"|"$/g, '') ?? '').filter((line, index) => line && !(index === 0 && /^(target|value|host|domain)$/i.test(line))).join('\n');
  }
  return contents;
}

export default function TargetBulkUploader() {
  const [text, setText] = useState('');
  const [preview, setPreview] = useState<TargetPreview | null>(null);
  const [items, setItems] = useState<EditableItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement | null>(null);
  const lastFocusedRef = useRef<HTMLElement | null>(null);
  const selectedCount = items.filter((item) => item.selected && item.validation?.valid).length;
  const validCount = items.filter((item) => item.validation?.valid).length;

  useEffect(() => {
    if (!confirmOpen) return;
    lastFocusedRef.current = document.activeElement as HTMLElement;
    const modal = modalRef.current;
    const focusable = modal ? Array.from(modal.querySelectorAll<HTMLElement>("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])")) : [];
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setConfirmOpen(false);
      if (event.key === 'Tab' && focusable.length) {
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    }
    document.addEventListener('keydown', onKey);
    first?.focus();
    return () => { document.removeEventListener('keydown', onKey); lastFocusedRef.current?.focus(); };
  }, [confirmOpen]);

  async function handlePreview() {
    setError('');
    setMessage('');
    if (!text.trim()) { setError('Add at least one target before validating scope.'); return; }
    setLoading(true);
    try {
      const result = await previewBulk(text, false);
      setPreview(result);
      setItems(result.items.map((item) => ({ original: item.original, canonical: item.canonical || item.original, type: item.type || 'unknown', validation: item.validation, selected: Boolean(item.validation?.valid) })));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Target preview failed. Check the API connection and try again.');
    } finally { setLoading(false); }
  }

  function updateItem(index: number, patch: Partial<EditableItem>) {
    setItems((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, ...patch } : item));
  }

  async function importFile(file?: File) {
    if (!file) return;
    setError(''); setMessage('');
    try {
      const contents = await file.text();
      setText((current) => [current.trim(), readFileTargets(contents, file.name)].filter(Boolean).join('\n'));
      setPreview(null); setItems([]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not read this target file.');
    }
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    void importFile(event.target.files?.[0]);
    event.target.value = '';
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault(); setDragging(false); void importFile(event.dataTransfer.files[0]);
  }

  async function doCreate() {
    const selected = items.filter((item) => item.selected && item.validation?.valid).map((item) => ({ original: item.original, canonical: item.canonical, target_type: item.type }));
    if (!selected.length) { setError('Select at least one valid target.'); setConfirmOpen(false); return; }
    setLoading(true); setError('');
    try {
      const result = await bulkCreate(selected);
      setConfirmOpen(false);
      setMessage(`${result.created} targets added to scope${result.failed ? `; ${result.failed} could not be added` : ''}.`);
      if (result.failed) setError(result.items?.filter((item) => item.status !== 'created').map((item) => `${item.original}: ${item.error || 'create failed'}`).join(' · ') || `${result.failed} targets failed to create.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not add targets to scope.');
    } finally { setLoading(false); }
  }

  return <div className="page-frame target-board">
    <header className="target-intro"><div><p className="eyebrow">AUTHORIZED SCOPE / CONTROL BOARD</p><h1>Targets &amp; scope</h1><p>Validate targets before adding them to an assessment. New targets default to draft, unauthorized scope.</p></div><button className="secondary-button" onClick={() => fileInput.current?.click()}>Import targets <span>＋</span></button></header>
    <div className="target-layout">
      <section className="target-input-panel" aria-labelledby="target-input-title"><h2 id="target-input-title">Add targets</h2><p>Paste IPs, CIDRs, domains, hostnames or URLs. One target per line.</p>
        <div className={`drop-input ${dragging ? 'dragging' : ''}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop}>
          <textarea className="target-textarea" aria-label="Targets to validate" value={text} onChange={(event) => { setText(event.target.value); setPreview(null); }} placeholder={'api.example.com\n192.0.2.12\n198.51.100.0/24\nhttps://portal.example.com'} />
          {dragging && <div className="drop-overlay">Drop target file to import</div>}
        </div>
        <input ref={fileInput} type="file" accept=".txt,.csv,.json,text/plain,text/csv,application/json" onChange={onFileChange} hidden aria-label="Import target file" />
        <div className="target-tools"><div className="target-tools-left"><label className="upload-button">Choose file<input type="file" accept=".txt,.csv,.json,text/plain,text/csv,application/json" onChange={onFileChange} /></label><button className="ghost-button" onClick={() => { setText(''); setPreview(null); setItems([]); setError(''); setMessage(''); }}>Clear</button></div><button className="primary-button" onClick={handlePreview} disabled={loading}>{loading ? 'Validating…' : 'Validate scope'} <span>↗</span></button></div>
        <p className="safety-note"><span>ⓘ</span> Validation does not authorize a target. Confirm written permission before any assessment.</p>
      </section>
      <section className="target-preview-panel" aria-labelledby="preview-title"><div className="panel-heading"><div><small>SCOPE VALIDATION</small><h2 id="preview-title">Review targets</h2></div>{preview && <span className="status-tag blue">{preview.count} PARSED</span>}</div>
        {!preview && <div className="target-empty"><div className="empty-target-mark">◎</div><strong>No scope preview yet</strong><p>Paste targets, import a TXT/CSV/JSON file, then validate them before saving.</p></div>}
        {preview && <><div className="preview-summary"><span>{preview.count} parsed</span><span className="valid">{validCount} valid</span><span className="invalid">{preview.count - validCount} invalid</span><label><input type="checkbox" className="table-checkbox" aria-label="Select all preview targets" checked={selectedCount === validCount && validCount > 0} onChange={(event) => setItems((current) => current.map((item) => ({ ...item, selected: Boolean(event.target.checked && item.validation?.valid) })))} /> Select valid</label></div>
          <div className="target-table-wrap"><table><thead><tr><th><span className="sr-only">Select</span></th><th>INPUT</th><th>CANONICAL</th><th>TYPE</th><th>CHECK</th></tr></thead><tbody>{items.map((item, index) => <tr key={`${item.original}-${index}`}><td><input className="table-checkbox" type="checkbox" checked={item.selected} disabled={!item.validation?.valid} onChange={() => updateItem(index, { selected: !item.selected })} aria-label={`Select ${item.original}`} /></td><td>{item.original}</td><td><input className="table-input" value={item.canonical} onChange={(event) => updateItem(index, { canonical: event.target.value })} aria-label={`Canonical for ${item.original}`} /></td><td><select className="table-select" value={item.type} onChange={(event) => updateItem(index, { type: event.target.value })} aria-label={`Type for ${item.original}`}><option value="ip">IP</option><option value="cidr_or_ip">CIDR/IP</option><option value="ip_range">IP range</option><option value="domain_or_hostname">Domain / host</option><option value="url">URL</option><option value="host_port">Host:port</option><option value="unknown">Unknown</option></select></td><td><span className={`validation-mark ${item.validation?.valid ? 'good' : 'bad'}`}>{item.validation?.valid ? 'VALID' : item.validation?.errors?.[0] || 'INVALID'}</span></td></tr>)}</tbody></table></div>
          <div className="target-footer"><small>{preview.overlaps.length ? `${preview.overlaps.length} overlapping range(s) detected. Review before adding.` : 'Saved targets remain draft and unauthorized until approved.'}</small><button className="primary-button" onClick={() => { setError(''); setConfirmOpen(true); }} disabled={!selectedCount || loading}>Add {selectedCount} to scope <span>↗</span></button></div>
        </>}
        {error && <div className="inline-error" role="alert">{error}</div>}{message && <div className="success-message" role="status">{message}</div>}
      </section>
    </div>
    {confirmOpen && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setConfirmOpen(false); }}><div className="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title" ref={modalRef}><p className="eyebrow">SCOPE CHANGE / CONFIRMATION</p><h2 id="confirm-title">Confirm add to scope</h2><p>You are adding <strong>{selectedCount}</strong> validated target(s). They will be stored as draft, unauthorized scope; this does not start a scan.</p><div className="modal-list"><table><thead><tr><th>CANONICAL TARGET</th><th>TYPE</th></tr></thead><tbody>{items.filter((item) => item.selected && item.validation?.valid).map((item, index) => <tr key={`${item.canonical}-${index}`}><td>{item.canonical}</td><td>{item.type}</td></tr>)}</tbody></table></div><div className="modal-actions"><button className="btn-cancel" onClick={() => setConfirmOpen(false)}>Cancel</button><button className="primary-button" onClick={doCreate} disabled={loading}>{loading ? 'Adding…' : 'Confirm add'}</button></div></div></div>}
  </div>;
}
