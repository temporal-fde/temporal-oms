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


def _ep_get(obj: object, key: str) -> object:
    """Get a field from an EasyPost SDK object, which may be a dict or an attribute-style object."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _extract_coordinate(ep_addr: object) -> Coordinate | None:
    lat = _ep_get(ep_addr, "latitude")
    lng = _ep_get(ep_addr, "longitude")
    if not lat:
        verifications = _ep_get(ep_addr, "verifications")
        for key in ("delivery", "zip4"):
            details = _ep_get(_ep_get(verifications, key), "details")
            if details:
                lat = _ep_get(details, "latitude")
                lng = _ep_get(details, "longitude")
                if lat:
                    break
    if not lat:
        return None
    return Coordinate(latitude=float(lat), longitude=float(lng) if lng else 0.0)  # type: ignore[arg-type]


def _get_client() -> easypost.EasyPostClient:
    return easypost.EasyPostClient(settings.easypost_api_key)


class EasyPostActivities:
    """Temporal activities that call the EasyPost API.

    Rate-limited to 5 rps via the fulfillment-easypost task queue worker config.
    """

    @activity.defn
    def verify_address(
        self,
        request: VerifyAddressRequest,
    ) -> VerifyAddressResponse:
        client = _get_client()
        ep = request.address.easypost or EasyPostAddress()

        activity.logger.info(f"Verifying address: {ep}")

        ep_addr = client.address.create_and_verify(
            street1=ep.street1,
            street2=ep.street2,
            city=ep.city,
            state=ep.state,
            zip=ep.zip,
            country=ep.country or "US",
        )
        activity.logger.info(f"Verified address: {ep_addr}")
        coordinate = _extract_coordinate(ep_addr)

        return VerifyAddressResponse(
            address=Address(
                easypost=EasyPostAddress(
                    id=ep_addr.id,
                    street1=getattr(ep_addr, "street1", ep.street1),
                    street2=getattr(ep_addr, "street2", ep.street2),
                    city=getattr(ep_addr, "city", ep.city),
                    state=getattr(ep_addr, "state", ep.state),
                    zip=getattr(ep_addr, "zip", ep.zip),
                    country=getattr(ep_addr, "country", ep.country),
                    residential=bool(getattr(ep_addr, "residential", False)),
                    coordinate=coordinate,
                ),
            ),
        )

    @activity.defn
    def get_carrier_rates(
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
