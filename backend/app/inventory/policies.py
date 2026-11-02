from fastapi import HTTPException
from app.auth.dependencies import Actor

INVENTORY_ADMIN = "inventoryAdmin"
INVENTORY_OPERATOR = "inventoryOperator"
INVENTORY_MANAGER = "inventoryManager"
INVENTORY_REGIONAL = "inventoryRegional"
INVENTORY_AUDITOR = "inventoryAuditor"
INVENTORY_ROLES = {INVENTORY_ADMIN, INVENTORY_OPERATOR, INVENTORY_MANAGER, INVENTORY_REGIONAL, INVENTORY_AUDITOR}
PERMISSIONS = {
    INVENTORY_ADMIN: {"catalog:manage", "catalog:read"},
    INVENTORY_OPERATOR: {"catalog:read", "stock:read", "movement:write", "history:read"},
    INVENTORY_MANAGER: {"catalog:read", "stock:read", "movement:write", "history:read", "adjust:write", "config:write"},
    INVENTORY_REGIONAL: {"catalog:read", "stock:read", "history:read"},
    INVENTORY_AUDITOR: {"catalog:read", "stock:read", "history:read", "audit:read"},
}


def allow(actor: Actor, permission: str):
    if permission not in PERMISSIONS.get(actor.role, set()):
        raise HTTPException(403, "Inventory permission denied")


def scope(actor: Actor, clinic):
    if not clinic.is_active:
        raise HTTPException(409, "Clinic is inactive")
    if actor.role in {INVENTORY_OPERATOR, INVENTORY_MANAGER}:
        accepted = clinic.id in actor.clinic_ids
    elif actor.role in {INVENTORY_REGIONAL, INVENTORY_AUDITOR}:
        accepted = clinic.jurisdiction_id in actor.jurisdiction_ids
    else:
        accepted = False
    if not accepted:
        raise HTTPException(403, "Clinic outside inventory scope")
