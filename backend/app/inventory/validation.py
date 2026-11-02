"""Explicit domain rejections; public HTTP status and detail remain unchanged."""
from fastapi import HTTPException

REASONS = frozenset({'reference', 'lot', 'unit', 'insufficient_stock'})


class InventoryValidationError(HTTPException):
    def __init__(self, status_code, detail, reason_code):
        if reason_code not in REASONS:
            raise ValueError('Unsupported inventory validation code')
        super().__init__(status_code=status_code, detail=detail)
        self.reason_code = reason_code
