// Private read-through to the existing API; no token validation or permission
// decision here. The API independently authorizes BOTH history reads.
export const dynamic = 'force-dynamic';
const headers = { 'Cache-Control': 'private, no-store' };
export async function POST(request) {
  const authorization = request.headers.get('authorization');
  if (!authorization?.startsWith('Bearer ')) return Response.json({ detail: 'Missing bearer token' }, { status: 401, headers });
  let incident;
  try { ({ incident } = await request.json()); } catch { return Response.json({ detail: 'Invalid request' }, { status: 422, headers }); }
  if (typeof incident !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(incident)) return Response.json({ detail: 'Invalid incident UUID' }, { status: 422, headers });
  try {
    const responses = await Promise.all(['history', 'assignment-history'].map(path => fetch(`${process.env.BACKEND_URL}/incidents/${incident}/${path}`, {
      headers: { Authorization: authorization }, cache: 'no-store', signal: AbortSignal.timeout(5000), redirect: 'error',
    })));
    const failure = responses.find(response => !response.ok);
    if (failure) return Response.json({ detail: 'History unavailable' }, { status: failure.status, headers });
    const [statusHistory, assignmentHistory] = await Promise.all(responses.map(response => response.json()));
    return Response.json({ statusHistory, assignmentHistory }, { headers });
  } catch { return Response.json({ detail: 'API unavailable' }, { status: 503, headers }); }
}
