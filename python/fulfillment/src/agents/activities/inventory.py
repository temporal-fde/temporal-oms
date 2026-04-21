from __future__ import annotations

import toml
from temporalio import activity

from src.config import settings

from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    LookupInventoryLocationRequest,
    LookupInventoryLocationResponse,
)
from acme.common.v1.values_p2p import Address, EasyPostAddress

def _load_warehouses() -> list[dict]:
    path = settings.warehouse_config_path
    data = toml.load(path)
    return data.get("warehouses", [])


def _warehouse_to_address(w: dict) -> Address:
    return Address(
        easypost=EasyPostAddress(
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
    async def lookup_inventory_location(
        self,
        request: LookupInventoryLocationRequest,
    ) -> LookupInventoryLocationResponse:
        if request.location_id:
            for w in self._warehouses:
                if w["location_id"] == request.location_id:
                    return LookupInventoryLocationResponse(
                        location_id=w["location_id"],
                        address=_warehouse_to_address(w),
                    )

        # Cart path: match on sku prefix
        item_skus = [item.sku_id for item in request.items]
        for w in self._warehouses:
            prefixes = w.get("sku_prefixes", [])
            if any(sku.startswith(tuple(prefixes)) for sku in item_skus if prefixes):
                return LookupInventoryLocationResponse(
                    location_id=w["location_id"],
                    address=_warehouse_to_address(w),
                )

        # Fallback: first warehouse (V1 simplification)
        if self._warehouses:
            w = self._warehouses[0]
            return LookupInventoryLocationResponse(
                location_id=w["location_id"],
                address=_warehouse_to_address(w),
            )

        raise RuntimeError("No warehouses configured")
