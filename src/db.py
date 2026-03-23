"""Compatibility exports for the repository layer.

Keyword arguments:
None."""

from src.repository.vn30_repository import (
    SQLiteConnectionManager,
    VN30Repository,
    VN30Row,
    create_connection_manager,
    create_vn30_repository,
)

# Compatibility aliases for older import paths and names.
VN30StockDAO = VN30Repository
create_vn30_stock_dao = create_vn30_repository
