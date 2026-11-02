"""Recognize rejected top-level stock writes without inspecting their values."""
from uuid import UUID


def attempt(request, error, route):
    body = error.body
    if not isinstance(body, dict) or 'stock' not in body:
        return None
    if not any(e.get('type') == 'extra_forbidden' and tuple(e.get('loc', ())) == ('body', 'stock')
               for e in error.errors()):
        return None
    if request.method != 'POST':
        return None
    if route == '/inventory/items/{item_id}/clinics/{clinic_id}/configuration':
        values, kind = request.path_params, 'configuration'
    elif route == '/inventory/movements':
        values, kind = body, body.get('kind')
        if kind not in {'in', 'out', 'adjust'}:
            return None
    else:
        return None
    try:
        return UUID(str(values['item_id'])), UUID(str(values['clinic_id'])), kind
    except (KeyError, ValueError, TypeError):
        return None
