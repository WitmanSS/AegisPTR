export async function previewBulk(text: string, resolve = false) {
  const res = await fetch('/api/targets/bulk/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, resolve }),
  });
  return res.json();
}

export async function bulkCreate(items: any[]) {
  const res = await fetch('/api/targets/bulk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ items }),
  });
  return res.json();
}
