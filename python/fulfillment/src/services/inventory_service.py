from __future__ import annotations

import nexusrpc

from acme.fulfillment.domain.v1.inventory_p2p import (
    FindAlternateWarehouseRequest,
    FindAlternateWarehouseResponse,
    LookupInventoryAddressRequest,
    LookupInventoryAddressResponse,
)


@nexusrpc.service(name="InventoryService")
class InventoryService:
    lookupInventoryAddress: nexusrpc.Operation[LookupInventoryAddressRequest, LookupInventoryAddressResponse]
    findAlternateWarehouse: nexusrpc.Operation[FindAlternateWarehouseRequest, FindAlternateWarehouseResponse]
