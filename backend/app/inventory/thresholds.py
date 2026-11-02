"""Isolated best-effort tracking of comparable committed movement crossings."""
from uuid import uuid4
from sqlalchemy import select

from app.inventory.models import InventoryClinicItem
from app.inventory.threshold_models import InventoryThresholdState, InventoryThresholdTransition
from app.inventory.service import quantity


def crossing(before, after, threshold, tracked_threshold, episode):
    # Configuration changes or missed recovery invalidate any old open episode.
    if tracked_threshold != threshold or before >= threshold:
        episode = None
    if before >= threshold and after < threshold:
        episode = uuid4()
        return 'activated', episode, episode
    if before < threshold <= after and episode is not None:
        return 'cleared', episode, None
    return None, None, episode


async def observe(session, movement):
    try:
        if movement.kind not in {'in', 'out', 'adjust', 'correction'} or movement.jurisdiction_key not in {'US', 'UK'}:
            return None
        # Domain already holds clinic/item locks. A savepoint failure must not
        # turn optional tracking into a failure of the confirmed business move.
        async with session.begin_nested():
            if await session.scalar(select(InventoryThresholdTransition.id).where(
                    InventoryThresholdTransition.movement_id == movement.id)) is not None:
                return None
            config = await session.get(InventoryClinicItem, (movement.item_id, movement.clinic_id))
            if config is None:
                return None
            state = await session.scalar(select(InventoryThresholdState).where(
                InventoryThresholdState.item_id == movement.item_id,
                InventoryThresholdState.clinic_id == movement.clinic_id).with_for_update())
            total = await quantity(session, movement.item_id, movement.clinic_id)
            kind, episode, active = crossing(total - movement.delta, total, config.reorder_point,
                state.threshold if state else None, state.episode_id if state else None)
            if state is None:
                state = InventoryThresholdState(item_id=movement.item_id, clinic_id=movement.clinic_id,
                    threshold=config.reorder_point, episode_id=active)
                session.add(state)
            else:
                state.threshold, state.episode_id = config.reorder_point, active
            transition = None
            if kind is not None:
                transition = InventoryThresholdTransition(episode_id=episode, movement_id=movement.id,
                    kind=kind, threshold=config.reorder_point, jurisdiction_id=movement.jurisdiction_id,
                    jurisdiction_key=movement.jurisdiction_key)
                session.add(transition)
            await session.flush()
            return transition.id if transition is not None else None
    except Exception:
        return None
