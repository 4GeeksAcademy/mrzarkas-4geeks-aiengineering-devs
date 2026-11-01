// The JSON contract is the only catalogue. Unsupported schema vocabulary fails closed.
const allowed = new Set(['type', 'required', 'properties', 'additionalProperties', 'enum', 'const',
  'pattern', 'format', 'minimum', 'maximum', 'anyOf', '$ref', 'allOf', 'oneOf', 'description']);
export function validate(schema, value, root, depth = 0) {
  if (depth > 12 || !schema || Object.keys(schema).some(key => !allowed.has(key))) return false;
  if (schema.$ref) {
    const parts = schema.$ref.split('/');
    if (parts.length !== 3 || parts[0] !== '#' || parts[1] !== 'definitions') return false;
    return validate(root.definitions[parts[2]], value, root, depth + 1);
  }
  for (const [key, predicate] of [['allOf', values => values.every(Boolean)],
    ['anyOf', values => values.some(Boolean)], ['oneOf', values => values.filter(Boolean).length === 1]]) {
    if (schema[key] && !predicate(schema[key].map(item => validate(item, value, root, depth + 1)))) return false;
  }
  const types = schema.type ? [].concat(schema.type) : [];
  const actual = value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value;
  if (types.length && !types.some(type => type === actual || (type === 'integer' && actual === 'number' && Number.isInteger(value)))) return false;
  if (schema.enum && !schema.enum.some(item => item === value)) return false;
  if ('const' in schema && schema.const !== value) return false;
  if (actual === 'number') {
    if (!Number.isFinite(value) || ('minimum' in schema && value < schema.minimum) || ('maximum' in schema && value > schema.maximum)) return false;
  }
  if (actual === 'string') {
    if (schema.pattern && !(new RegExp(schema.pattern)).test(value)) return false;
    if (schema.format === 'date-time') {
      if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/.test(value) || !Number.isFinite(Date.parse(value))) return false;
      const [year, month, day] = value.slice(0, 10).split('-').map(Number);
      const days = new Date(Date.UTC(year, month, 0)).getUTCDate();
      if (month < 1 || month > 12 || day < 1 || day > days || +value.slice(11, 13) > 23 || +value.slice(14, 16) > 59 || +value.slice(17, 19) > 59) return false;
    } else if (schema.format) return false;
  }
  if (actual === 'object') {
    if (Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null) return false;
    const fields = schema.properties || {};
    if (schema.required?.some(key => !Object.hasOwn(value, key))) return false;
    if (schema.additionalProperties === false && Object.keys(value).some(key => !Object.hasOwn(fields, key))) return false;
    for (const [key, child] of Object.entries(fields)) {
      if (Object.hasOwn(value, key) && !validate(child, value[key], root, depth + 1)) return false;
    }
  }
  return true;
}

export function compileContract(contract) {
  const envelope = contract.definitions.envelope;
  const version = envelope.properties.schemaVersion.const;
  // Browser admission is a producer policy, independent of nullable scope.
  const general = new Set(['navigation_viewed', 'frontend_timing_measured',
    'application_error_observed', 'session_started', 'session_ended']);
  return { version, general, validDiagnostic: value => {
    const name = value?.event_type;
    return ['telemetry_contract_rejected', 'telemetry_delivery_failed'].includes(name)
      && value.properties?.producer === 'frontend' && value.properties?.jurisdiction === null
      && validate(contract.definitions[name], value, contract);
  }, validEvent: value => {
    const definition = contract.definitions[value?.event_type];
    return Boolean(definition && general.has(value.event_type) && validate(definition, value, contract));
  } };
}
