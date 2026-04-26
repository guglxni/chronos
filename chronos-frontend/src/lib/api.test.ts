import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from './api';

// Stub global fetch
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function errorResponse(status: number, detail: string): Response {
  return new Response(JSON.stringify({ detail }), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

beforeEach(() => {
  mockFetch.mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

// ── listIncidents ─────────────────────────────────────────────────────────────

describe('api.listIncidents', () => {
  it('returns incidents on 200', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ total: 2, incidents: [{ incident_id: 'a' }, { incident_id: 'b' }] })
    );
    const result = await api.listIncidents();
    expect(result.total).toBe(2);
    expect(result.incidents).toHaveLength(2);
  });

  it('forwards status/root_cause query params', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ total: 0, incidents: [] }));
    await api.listIncidents({ status: 'open', root_cause: 'SCHEMA_CHANGE', limit: 10 });
    const calledUrl = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain('status=open');
    expect(calledUrl).toContain('root_cause=SCHEMA_CHANGE');
    expect(calledUrl).toContain('limit=10');
  });

  it('throws with detail message on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce(errorResponse(400, 'Invalid status filter'));
    await expect(api.listIncidents({ status: 'bad' })).rejects.toThrow('Invalid status filter');
  });
});

// ── getIncident ───────────────────────────────────────────────────────────────

describe('api.getIncident', () => {
  it('returns typed incident on 200', async () => {
    const fixture = { incident_id: 'abc-123', status: 'open' };
    mockFetch.mockResolvedValueOnce(jsonResponse(fixture));
    const result = await api.getIncident('abc-123');
    expect(result.incident_id).toBe('abc-123');
  });

  it('throws "HTTP 404" when not found', async () => {
    mockFetch.mockResolvedValueOnce(errorResponse(404, 'Incident abc-999 not found'));
    await expect(api.getIncident('abc-999')).rejects.toThrow('Incident abc-999 not found');
  });
});

// ── acknowledgeIncident ───────────────────────────────────────────────────────

describe('api.acknowledgeIncident', () => {
  it('resolves on 200', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ status: 'acknowledged' }));
    await expect(api.acknowledgeIncident('id-1')).resolves.toBeUndefined();
  });

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce(errorResponse(404, 'Incident id-x not found'));
    await expect(api.acknowledgeIncident('id-x')).rejects.toThrow('Incident id-x not found');
  });

  it('uses POST method', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({}));
    await api.acknowledgeIncident('id-1');
    const [, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(opts.method).toBe('POST');
  });
});

// ── resolveIncident ───────────────────────────────────────────────────────────

describe('api.resolveIncident', () => {
  it('resolves on 200', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ status: 'resolved' }));
    await expect(api.resolveIncident('id-1')).resolves.toBeUndefined();
  });

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce(errorResponse(404, 'Incident id-x not found'));
    await expect(api.resolveIncident('id-x')).rejects.toThrow('Incident id-x not found');
  });
});

// ── getStats ──────────────────────────────────────────────────────────────────

describe('api.getStats', () => {
  it('returns stats on 200', async () => {
    const fixture = { total_incidents: 5, open_count: 2, critical_count: 1, avg_confidence: 0.82 };
    mockFetch.mockResolvedValueOnce(jsonResponse(fixture));
    const result = await api.getStats();
    expect(result.total_incidents).toBe(5);
  });

  it('throws on server error', async () => {
    mockFetch.mockResolvedValueOnce(errorResponse(500, 'internal_server_error'));
    await expect(api.getStats()).rejects.toThrow('internal_server_error');
  });
});

// ── triggerInvestigation ──────────────────────────────────────────────────────

describe('api.triggerInvestigation', () => {
  it('returns incident_id + stream_url on 200', async () => {
    const fixture = { incident_id: 'xyz', stream_url: '/api/v1/investigations/xyz/stream', status: 'triggered', entity_fqn: 'db.orders' };
    mockFetch.mockResolvedValueOnce(jsonResponse(fixture));
    const result = await api.triggerInvestigation('db.orders', 'not_null');
    expect(result.incident_id).toBe('xyz');
    expect(result.stream_url).toContain('xyz');
  });

  it('sends entity_fqn and test_name in body', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ incident_id: 'x', stream_url: '/s/x', status: 'triggered', entity_fqn: 'e' }));
    await api.triggerInvestigation('db.schema.orders', 'null_check');
    const [, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(opts.body as string) as { entity_fqn: string; test_name: string };
    expect(body.entity_fqn).toBe('db.schema.orders');
    expect(body.test_name).toBe('null_check');
  });
});

// ── getProvenanceUrl ──────────────────────────────────────────────────────────

describe('api.getProvenanceUrl', () => {
  it('returns correct URL for jsonld format', () => {
    const url = api.getProvenanceUrl('inc-1', 'jsonld');
    expect(url).toContain('/inc-1/provenance.jsonld');
  });
});
