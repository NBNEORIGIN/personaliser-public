export type QaWarning = {
  code: string
  message: string
  field?: string | null
  severity: 'info' | 'warn' | 'error'
}

export type IngestItem = {
  order_ref: string
  template_id?: string | null
  sku?: string | null
  quantity: number
  lines: { id: 'line_1' | 'line_2' | 'line_3'; value: string }[]
  graphics_key?: string | null
  photo_asset_id?: string | null
  photo_asset_url?: string | null
  photo_filename?: string | null
  assets: string[]
  colour?: string | null
  product_type?: string | null
  decoration_type?: string | null
  theme?: string | null
  processor?: string | null
  warnings?: QaWarning[]
}

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE as string) ||
  (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://localhost:8000');

// Debug logging
if (typeof window !== 'undefined') {
  console.log('API_BASE configured as:', API_BASE);
  console.log('NEXT_PUBLIC_API_BASE env:', process.env.NEXT_PUBLIC_API_BASE);
}

export async function ingestAmazon(input: { text?: string, file?: File }) {
  const url = `${API_BASE}/api/ingest/amazon`;
  if (input.file) {
    const fd = new FormData();
    fd.append('file', input.file);
    const res = await fetch(url, { method: 'POST', body: fd });
    if (!res.ok) throw new Error(`ingest failed: ${res.status}`);
    return res.json();
  } else {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: input.text || '' })
    });
    if (!res.ok) throw new Error(`ingest failed: ${res.status}`);
    return res.json();
  }
}

export async function generateJob(items: any[]) {
  const url = `${API_BASE}/api/jobs/generate`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ items, machine_id: 'MUTOH-UJF-461' })
    });
    const data = await res.json().catch(() => ({}));
    return { status: res.status, data };
  } catch (error) {
    console.error('Generate job error:', error);
    throw new Error(`Failed to connect to API: ${error instanceof Error ? error.message : 'Network error'}`);
  }
}

export async function previewItem(item: any) {
  const url = `${API_BASE}/api/jobs/preview`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item })
  });
  if (!res.ok) throw new Error(`preview failed: ${res.status}`);
  return res.json();
}

export async function ping() {
  return { ok: true };
}

