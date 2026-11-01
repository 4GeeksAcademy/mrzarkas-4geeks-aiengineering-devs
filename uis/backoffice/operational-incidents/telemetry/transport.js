export function receiverURL(value, environment) {
  try {
    const url = new URL(value);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash
      || url.pathname !== '/telemetry/events' || (environment === 'production' && url.protocol !== 'https:')) return null;
    return url.href;
  } catch { return null; }
}

export class TransportTimeoutError extends Error {
  constructor() { super('Telemetry timeout'); this.name = 'TransportTimeoutError'; }
}

export async function boundedFetch(fetcher, url, options, timers, timeout = 5000) {
  const controller = new AbortController();
  const upstream = options.signal;
  const abort = () => controller.abort();
  if (upstream?.aborted) controller.abort();
  else upstream?.addEventListener('abort', abort, { once: true });
  let timedOut = false;
  const id = timers.set(() => { timedOut = true; controller.abort(); }, timeout);
  try { return await fetcher(url, { ...options, signal: controller.signal, redirect: 'error', cache: 'no-store' }); }
  catch (error) { if (timedOut) throw new TransportTimeoutError(); throw error; }
  finally { timers.clear(id); upstream?.removeEventListener('abort', abort); }
}

export function retryDelay(response, retry, wallNow) {
  let delay = 1000 * 2 ** (retry - 1);
  if ([429, 503].includes(response?.status)) {
    const hint = response.headers?.get('Retry-After');
    if (hint) {
      const millis = /^\d+$/.test(hint) ? Number(hint) * 1000 : Date.parse(hint) - wallNow;
      if (Number.isFinite(millis) && millis > 0) delay = Math.max(delay, Math.min(millis, 30000));
    }
  }
  return delay;
}
export const recoverable = status => [408, 429, 500, 502, 503, 504].includes(status);
