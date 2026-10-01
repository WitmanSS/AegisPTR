import cytoscape, { Core, ElementDefinition } from 'cytoscape';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getResource } from '../services/api';
import '../graph.css';

type GraphNode = { data: Record<string, string | number | boolean | null> };
type GraphEdge = { data: { id: string; source: string; target: string; relation: string } };
type GraphResponse = { elements: { nodes: GraphNode[]; edges: GraphEdge[] }; counts: { nodes: number; edges: number } };
type Assessment = { id: string; name: string; is_authorized: boolean; status: string };
type GraphFilters = { assessment_id: string; severity: string; q: string };

const kindLabel: Record<string, string> = { assessment: 'ASSESSMENT', target: 'TARGET', service: 'SERVICE', finding: 'FINDING' };

export function AttackSurfaceGraph() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [filters, setFilters] = useState<GraphFilters>({ assessment_id: '', severity: 'ALL', q: '' });
  const [graph, setGraph] = useState<GraphResponse>({ elements: { nodes: [], edges: [] }, counts: { nodes: 0, edges: 0 } });
  const [selected, setSelected] = useState<Record<string, string | number | boolean | null> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [layout, setLayout] = useState<'cose' | 'breadthfirst'>('cose');

  useEffect(() => {
    let active = true;
    getResource<Assessment[]>('/api/assessments').then((rows) => { if (active) setAssessments(Array.isArray(rows) ? rows : []); }).catch(() => undefined);
    return () => { active = false; };
  }, []);

  const loadGraph = useCallback(async () => {
    setLoading(true); setError('');
    const params = new URLSearchParams();
    if (filters.assessment_id) params.set('assessment_id', filters.assessment_id);
    if (filters.severity !== 'ALL') params.set('severity', filters.severity);
    if (filters.q.trim()) params.set('q', filters.q.trim());
    try {
      const result = await getResource<GraphResponse>(`/api/targets/graph?${params.toString()}`);
      setGraph(result);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load the attack surface graph.');
    } finally { setLoading(false); }
  }, [filters]);

  useEffect(() => { const timer = window.setTimeout(() => { void loadGraph(); }, 200); return () => window.clearTimeout(timer); }, [loadGraph]);

  const elements = useMemo<ElementDefinition[]>(() => [...graph.elements.nodes, ...graph.elements.edges], [graph]);

  useEffect(() => {
    if (!containerRef.current) return;
    if (!cyRef.current) {
      cyRef.current = cytoscape({
        container: containerRef.current,
        elements,
        minZoom: 0.2,
        maxZoom: 3,
        style: [
          { selector: 'node', style: { 'background-color': '#546d76', 'border-width': 1, 'border-color': '#8ca3a8', color: '#e8eff2', label: 'data(label)', 'font-family': 'DM Mono, monospace', 'font-size': '9px', 'text-wrap': 'wrap', 'text-max-width': '115px', 'text-valign': 'bottom', 'text-margin-y': 8, width: 34, height: 34, 'overlay-opacity': 0 } },
          { selector: 'node[kind = "assessment"]', style: { shape: 'round-rectangle', 'background-color': '#225f52', 'border-color': '#72dfba', width: 48, height: 34, 'font-size': '8px' } },
          { selector: 'node[kind = "target"]', style: { shape: 'ellipse', 'background-color': '#244e62', 'border-color': '#7ab8e8', width: 42, height: 42 } },
          { selector: 'node[kind = "service"]', style: { shape: 'hexagon', 'background-color': '#67512b', 'border-color': '#eabb69', width: 32, height: 32, 'font-size': '7px' } },
          { selector: 'node[kind = "finding"]', style: { shape: 'diamond', 'background-color': '#7c413e', 'border-color': '#f08078', width: 36, height: 36, 'font-size': '7px' } },
          { selector: 'edge', style: { width: 1.5, 'line-color': '#62777d', 'target-arrow-color': '#91a3ac', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', label: 'data(relation)', color: '#91a3ac', 'font-family': 'DM Mono, monospace', 'font-size': '6px', 'text-background-color': '#0b1117', 'text-background-opacity': 0.8, 'text-background-padding': '2px', 'overlay-opacity': 0 } },
          { selector: 'edge[relation = "excludes"]', style: { 'line-style': 'dashed', 'line-color': '#f08078', 'target-arrow-color': '#f08078' } },
          { selector: ':selected', style: { 'border-width': 3, 'border-color': '#f3f7f3', 'background-color': '#367b68', 'line-color': '#dcebe4', 'target-arrow-color': '#dcebe4', 'z-index': 10 } },
          { selector: '.dimmed', style: { opacity: 0.12 } },
          { selector: '.search-hit', style: { 'border-width': 4, 'border-color': '#f3d37d', 'z-index': 20 } },
        ],
        layout: { name: layout, animate: false, fit: true, padding: 35, nodeRepulsion: 6500, idealEdgeLength: 110, nodeDimensionsIncludeLabels: true } as cytoscape.LayoutOptions,
      });
      cyRef.current.on('tap', 'node', (event) => setSelected({ ...event.target.data() }));
      cyRef.current.on('tap', (event) => { if (event.target === cyRef.current) setSelected(null); });
    } else {
      const cy = cyRef.current;
      cy.elements().remove();
      cy.add(elements);
      cy.layout({ name: layout, animate: false, fit: true, padding: 35, nodeRepulsion: 6500, idealEdgeLength: 110, nodeDimensionsIncludeLabels: true } as cytoscape.LayoutOptions).run();
    }
    return () => undefined;
  }, [elements, layout]);

  useEffect(() => () => { cyRef.current?.destroy(); cyRef.current = null; }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver(() => {
      const cy = cyRef.current;
      if (!cy) return;
      cy.resize();
      cy.fit(undefined, 35);
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  function searchGraph(value: string) {
    setFilters((current) => ({ ...current, q: value }));
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass('dimmed search-hit');
    if (!value.trim()) return;
    const matches = cy.nodes().filter((node) => String(node.data('label') ?? '').toLowerCase().includes(value.trim().toLowerCase()) || String(node.data('cve') ?? '').toLowerCase().includes(value.trim().toLowerCase()));
    cy.elements().addClass('dimmed');
    matches.removeClass('dimmed').addClass('search-hit');
    matches.connectedEdges().removeClass('dimmed');
    matches.connectedEdges().connectedNodes().removeClass('dimmed');
  }

  function zoom(factor: number) { cyRef.current?.zoom({ level: cyRef.current.zoom() * factor, renderedPosition: { x: (cyRef.current.width() / 2), y: (cyRef.current.height() / 2) } }); }

  return <div className="page-frame attack-surface-page">
    <header className="page-heading"><div><p className="eyebrow">PHASE 7 / EXPOSURE INTELLIGENCE</p><h1>Attack surface graph</h1><p className="page-description">Explore only relationships recorded in assessments, target scope and finding evidence.</p></div><div className="graph-summary"><strong>{graph.counts.nodes}</strong><small>NODES</small><strong>{graph.counts.edges}</strong><small>LINKS</small></div></header>
    <section className="graph-toolbar"><label>SEARCH<input aria-label="Search graph" value={filters.q} onChange={(event) => searchGraph(event.target.value)} placeholder="Asset, host, CVE…" /></label><label>ASSESSMENT<select aria-label="Filter graph assessment" value={filters.assessment_id} onChange={(event) => setFilters((current) => ({ ...current, assessment_id: event.target.value }))}><option value="">All assessments</option>{assessments.map((assessment) => <option key={assessment.id} value={assessment.id}>{assessment.name}</option>)}</select></label><label>FINDING SEVERITY<select aria-label="Filter graph severity" value={filters.severity} onChange={(event) => setFilters((current) => ({ ...current, severity: event.target.value }))}><option value="ALL">All severities</option><option>CRITICAL</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option><option>INFO</option></select></label><button className="text-button" onClick={() => setLayout((current) => current === 'cose' ? 'breadthfirst' : 'cose')}>Layout: {layout === 'cose' ? 'Force' : 'Hierarchy'} ↻</button><div className="graph-zoom"><button aria-label="Zoom out" onClick={() => zoom(.8)}>−</button><button aria-label="Fit graph" onClick={() => cyRef.current?.fit(undefined, 35)}>Fit</button><button aria-label="Zoom in" onClick={() => zoom(1.25)}>＋</button></div></section>
    {error && <div className="inline-error" role="alert">{error}</div>}
    <div className="graph-workspace"><section className="graph-canvas-shell"><div className="graph-legend"><span><i className="legend-assessment" /> Assessment</span><span><i className="legend-target" /> Target</span><span><i className="legend-service" /> Service</span><span><i className="legend-finding" /> Finding</span></div><div className="attack-graph-canvas" ref={containerRef} role="img" aria-label="Interactive attack surface graph" />{loading && <div className="graph-loading">Updating graph…</div>}{!loading && graph.counts.nodes === 0 && <div className="graph-empty"><span>⌘</span><strong>No graph data yet</strong><p>Add target scope or ingest finding observations to establish explicit relationships.</p></div>}<div className="graph-integrity-note">Lines represent stored scope or tool-observed relationships. No inferred attack paths are shown.</div></section>
      <aside className="graph-inspector"><div className="panel-heading"><div><small>NODE INSPECTOR</small><h2>{selected ? String(selected.label ?? 'Selected node') : 'No selection'}</h2></div><span className="status-tag blue">{selected ? kindLabel[String(selected.kind)] ?? 'NODE' : 'READY'}</span></div>{selected ? <dl className="graph-node-fields">{Object.entries(selected).filter(([key]) => key !== 'id' && key !== 'label' && key !== 'kind').map(([key, value]) => <div key={key}><dt>{key.replace(/_/g, ' ')}</dt><dd>{value === null || value === undefined || value === '' ? 'Not recorded' : String(value)}</dd></div>)}</dl> : <div className="graph-inspector-empty"><span>◎</span><p>Select a node to review its stored properties and provenance.</p></div>}<div className="graph-relation-note"><small>RELATIONSHIP KEY</small><p><b>allows / excludes</b> comes from assessment scope.</p><p><b>observed service / finding</b> comes from persisted tool observations.</p></div></aside>
    </div>
  </div>;
}
