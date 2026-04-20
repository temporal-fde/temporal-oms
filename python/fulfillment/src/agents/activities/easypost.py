from __future__ import annotations

import easypost
from temporalio import activity

from src.config import settings
from acme.common.v1.values_p2p import Address, Coordinate, EasyPostAddress, Money
from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    GetShippingRatesRequest,
    GetShippingRatesResponse,
    ShippingOption,
)
from acme.fulfillment.domain.v1.workflows_p2p import (
    VerifyAddressRequest,
    VerifyAddressResponse,
)

# V1 default parcel: 1 lb, 6×6×4 inches — no proto field; hardcoded for all rate calculations.
_DEFAULT_PARCEL = {"weight": 16, "length": 6, "width": 6, "height": 4}


def _get_client() -> easypost.EasyPostClient:
    return easypost.EasyPostClient(settings.easypost_api_key)


class EasyPostActivities:
    """Temporal activities that call the EasyPost API.

    Rate-limited to 5 rps via the fulfillment-easypost task queue worker config.
    """

    @activity.defn
    async def verify_address(
        self,
        request: VerifyAddressRequest,
    ) -> VerifyAddressResponse:
        client = _get_client()
        addr = request.address

        ep_addr = client.address.create_and_verify(
            street1=addr.street,
            city=addr.city,
            state=addr.state,
            zip=addr.postal_code,
            country=addr.country,
        )

        lat = getattr(ep_addr, "latitude", None)
        lng = getattr(ep_addr, "longitude", None)
        coordinate = Coordinate(latitude=lat or 0.0, longitude=lng or 0.0) if lat else None

        easypost_address = EasyPostAddress(
            id=ep_addr.id,
            residential=bool(getattr(ep_addr, "residential", False)),
            verified=True,
            coordinate=coordinate,
        )

        verified_address = Address(
            street=getattr(ep_addr, "street1", addr.street),
            city=getattr(ep_addr, "city", addr.city),
            state=getattr(ep_addr, "state", addr.state),
            postal_code=getattr(ep_addr, "zip", addr.postal_code),
            country=getattr(ep_addr, "country", addr.country),
            easypost_address=easypost_address,
        )
        return VerifyAddressResponse(address=verified_address)

    @activity.defn
    async def get_carrier_rates(
        self,
        request: GetShippingRatesRequest,
    ) -> GetShippingRatesResponse:
        client = _get_client()

        # V1: default parcel (1 lb, 6×6×4 in) — no proto field for dimensions.
        shipment = client.shipment.create(
            from_address={"id": request.from_easypost_id},
            to_address={"id": request.to_easypost_id},
            parcel=_DEFAULT_PARCEL,
        )

        options: list[ShippingOption] = []
        for rate in getattr(shipment, "rates", []):
            cost_units = int(float(getattr(rate, "rate", "0")) * 100)
            options.append(ShippingOption(
                id=rate.id,
                carrier=getattr(rate, "carrier", ""),
                service_level=getattr(rate, "service", ""),
                cost=Money(currency=getattr(rate, "currency", "USD"), units=cost_units),
                estimated_days=int(getattr(rate, "est_delivery_days", 0) or 0),
                rate_id=rate.id,
            ))

        return GetShippingRatesResponse(
            shipment_id=shipment.id,
            options=options,
        )
