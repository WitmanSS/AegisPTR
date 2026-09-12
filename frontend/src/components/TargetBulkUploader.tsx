import React, { useEffect, useRef, useState } from 'react'
import { previewBulk, bulkCreate } from '../services/targets'

type EditableItem = {
  original: string
  canonical: string
  type: string
  validation?: any
  selected: boolean
}

export default function TargetBulkUploader() {
  const [text, setText] = useState('')
  const [preview, setPreview] = useState<any>(null)
  const [items, setItems] = useState<EditableItem[]>([])
  const [loading, setLoading] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const modalRef = useRef<HTMLDivElement | null>(null)
  const lastFocusedRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!confirmOpen) return
    lastFocusedRef.current = document.activeElement as HTMLElement
    const modal = modalRef.current
    const focusable = modal ? Array.from(modal.querySelectorAll<HTMLElement>("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])")) : []
    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setConfirmOpen(false)
      }
      if (e.key === 'Tab') {
        if (focusable.length === 0) {
          e.preventDefault()
          return
        }
        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault()
            last?.focus()
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault()
            first?.focus()
          }
        }
      }
    }

    document.addEventListener('keydown', onKey)
    // focus first element
    setTimeout(() => first?.focus(), 0)

    return () => {
      document.removeEventListener('keydown', onKey)
      // restore focus
      try { lastFocusedRef.current?.focus() } catch (e) {}
    }
  }, [confirmOpen])

  async function handlePreview() {
    setLoading(true)
    const res = await previewBulk(text, false)
    setPreview(res)
    setLoading(false)
  }

  useEffect(() => {
    if (!preview) return
    const mapped: EditableItem[] = preview.items.map((it: any) => ({
      original: it.original,
      canonical: it.canonical || it.original,
      type: it.type,
      validation: it.validation,
      selected: true,
    }))
    setItems(mapped)
  }, [preview])

  function toggleSelect(idx: number) {
    setItems(curr => curr.map((it, i) => i === idx ? { ...it, selected: !it.selected } : it))
  }

  function updateItem(idx: number, patch: Partial<EditableItem>) {
    setItems(curr => curr.map((it, i) => i === idx ? { ...it, ...patch } : it))
  }

  function toggleSelectAll(e: React.ChangeEvent<HTMLInputElement>) {
    const v = e.target.checked
    setItems(curr => curr.map(it => ({ ...it, selected: v })))
  }

  function openConfirm() {
    setConfirmOpen(true)
  }

  async function doCreate() {
    const toCreate = items.filter(it => it.selected).map(it => ({ original: it.original, canonical: it.canonical, target_type: it.type }))
    if (toCreate.length === 0) {
      alert('No items selected')
      return
    }
    setLoading(true)
    const res = await bulkCreate(toCreate)
    setLoading(false)
    setConfirmOpen(false)
    alert(`Created ${res.created} / ${res.total}, failed ${res.failed}`)
  }

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{ width: '48%' }}>
        <h3>Paste targets</h3>
        <textarea style={{ width: '100%', height: 360 }} value={text} onChange={e => setText(e.target.value)} />
        <div style={{ marginTop: 12 }}>
          <button onClick={handlePreview} disabled={loading}>Parse Preview</button>
          <button onClick={() => setText('')} style={{ marginLeft: 8 }}>Clear</button>
        </div>
      </div>

      <div style={{ width: '52%' }}>
        <h3>Preview</h3>
        {loading && <div>Loading…</div>}
        {!preview && <div className='muted'>No preview yet</div>}
        {preview && (
          <div>
            <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>Total: {preview.count} · Overlaps: {preview.overlaps?.length || 0}</div>
              <div><label><input type="checkbox" onChange={toggleSelectAll} checked={items.every(i => i.selected)} aria-label="Select all preview targets" /> Select All</label></div>
            </div>
            <table>
              <thead>
                <tr>
                  <th style={{ width: 36 }}></th>
                  <th>Original</th>
                  <th>Canonical</th>
                  <th style={{ width: 120 }}>Type</th>
                  <th style={{ width: 96 }}>Validation</th>
                </tr>
              </thead>
              <tbody>
                {items.map((it, idx) => (
                  <tr key={idx}>
                    <td>
                      <input className="table-checkbox" type="checkbox" checked={it.selected} onChange={() => toggleSelect(idx)} aria-label={`Select ${it.original}`} />
                    </td>
                    <td>{it.original}</td>
                    <td>
                      <input className="table-input" value={it.canonical} onChange={e => updateItem(idx, { canonical: e.target.value })} aria-label={`Canonical for ${it.original}`} />
                    </td>
                    <td>
                      <select className="table-select" value={it.type} onChange={e => updateItem(idx, { type: e.target.value })} aria-label={`Type for ${it.original}`}>
                        <option value="ip">ip</option>
                        <option value="cidr">cidr</option>
                        <option value="fqdn">fqdn</option>
                        <option value="url">url</option>
                      </select>
                    </td>
                    <td>{it.validation?.valid ? <span className="valid">OK</span> : <span className="invalid">Invalid</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ marginTop: 12 }}>
              <button onClick={openConfirm} disabled={loading}>Add to Scope</button>
            </div>
          </div>
        )}
      </div>

      {confirmOpen && (
        <div className="modal-backdrop" onKeyDown={(e) => {
          if (e.key === 'Escape') setConfirmOpen(false)
        }}>
          <div className="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title" ref={modalRef}>
            <h4 id="confirm-title">Confirm Add to Scope</h4>
            <div className="muted" style={{ marginBottom: 12 }}>You are about to add <strong>{items.filter(i => i.selected).length}</strong> targets to scope.</div>
            <div className="modal-list">
              <table className="table">
                <thead><tr><th>Canonical</th><th>Type</th></tr></thead>
                <tbody>
                  {items.filter(i => i.selected).map((it, idx) => (
                    <tr key={idx}><td>{it.canonical}</td><td>{it.type}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="modal-actions">
              <button onClick={() => setConfirmOpen(false)} className="btn-cancel" aria-label="Cancel adding targets">Cancel</button>
              <button onClick={doCreate} disabled={loading} aria-label="Confirm adding targets">Confirm Add</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

