from __future__ import annotations

import toml
from temporalio import activity

from src.config import settings

from acme.fulfillment.domain.v1.inventory_p2p import (
    FindAlternateWarehouseRequest,
    FindAlternateWarehouseResponse,
    LookupInventoryAddressRequest,
    LookupInventoryAddressResponse,
)
from acme.common.v1.values_p2p import Address, EasyPostAddress

def _load_warehouses() -> list[dict]:
    path = settings.warehouse_config_path
    data = toml.load(path)
    return data.get("warehouses", [])


def _warehouse_to_address(w: dict) -> Address:
    return Address(
        easypost=EasyPostAddress(
            id=w.get("easypost_id", ""),
            street1=w["street1"],
            street2=w.get("street2", ""),
            city=w["city"],
            state=w["state"],
            zip=w["zip"],
            country=w["country"],
        ),
    )


class LookupInventoryActivities:
    """Resolves sku_ids to a warehouse address from static TOML config.

    V1 simplification: static config lookup only.
    Future: query Inventory Locations service.
    """

    def __init__(self) -> None:
        self._warehouses = _load_warehouses()

    @activity.defn
    async def lookup_inventory_address(
        self,
        request: LookupInventoryAddressRequest,
    ) -> LookupInventoryAddressResponse:
        if request.address_id:
            for w in self._warehouses:
                if w["location_id"] == request.address_id:
                    return LookupInventoryAddressResponse(
                        address=_warehouse_to_address(w),
                    )

        # Cart path: match on sku prefix
        item_skus = [item.sku_id for item in request.items]
        for w in self._warehouses:
            prefixes = w.get("sku_prefixes", [])
            if any(sku.startswith(tuple(prefixes)) for sku in item_skus if prefixes):
                return LookupInventoryAddressResponse(
                    address=_warehouse_to_address(w),
                )

        # Fallback: first warehouse (V1 simplification)
        if self._warehouses:
            w = self._warehouses[0]
            return LookupInventoryAddressResponse(
                address=_warehouse_to_address(w),
            )

        raise RuntimeError("No warehouses configured")

    @activity.defn
    async def find_alternate_warehouse(
        self,
        request: FindAlternateWarehouseRequest,
    ) -> FindAlternateWarehouseResponse:
        # TODO: persist the SKU→alternate routing decision for a time window so
        # subsequent orders don't redundantly re-discover the same alternate.
        # A per-SKU Temporal workflow (SkuAvailabilityAgent) is the natural home for this state.
        item_skus = [item.sku_id for item in request.items]
        for w in self._warehouses:
            if w.get("easypost_id", "") == request.current_address_id:
                continue
            prefixes = w.get("sku_prefixes", [])
            # empty sku_prefixes = catch-all warehouse
            if not prefixes or any(sku.startswith(tuple(prefixes)) for sku in item_skus):
                return FindAlternateWarehouseResponse(address=_warehouse_to_address(w))
        return FindAlternateWarehouseResponse()
