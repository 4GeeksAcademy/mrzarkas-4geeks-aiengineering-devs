import { createTelemetryService } from './telemetry-service.js';
import { observeVitals } from './vitals.js';

const disabled = { track() {}, async connect() { return false; }, async activateClinic() { return false; },
  navigate() {}, error() {}, timing() {}, disconnect() {}, destroy() {}, flush() {}, diagnostics: () => ({}) };

// Dynamic bootstrap isolates config/schema/module failures from existing business UI.
export async function bootstrapTelemetry(application) {
  try {
    const responses = await Promise.all(['config.json', 'event-contract.json'].map(name => fetch(new URL(name, import.meta.url),
      { cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(5000) })));
    if (responses.some(response => !response.ok)) return disabled;
    const [config, contract] = await Promise.all(responses.map(response => response.json()));
    if (Object.keys(config).sort().join(',') !== 'enabled,endpoint,environment' || config.enabled !== true) return disabled;
    const service = createTelemetryService({ contract, config: { ...config, application } });
    const onError = () => service.error('unexpected'); // Never inspect message/stack/reason/URL.
    window.addEventListener('error', onError);
    window.addEventListener('unhandledrejection', onError);
    const originalConnect = service.connect;
    service.connect = async (...args) => {
      const connected = await originalConnect(...args);
      if (connected) service.setObserversCleanup(observeVitals(service, application === 'management' ? 'management' : 'incidents'));
      return connected;
    };
    const originalDestroy = service.destroy;
    service.destroy = () => {
      window.removeEventListener('error', onError);
      window.removeEventListener('unhandledrejection', onError);
      originalDestroy();
    };
    return service;
  } catch { return disabled; }
}
