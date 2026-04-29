from __future__ import annotations

from temporalio import activity
from temporalio.exceptions import ApplicationError

from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    GetShippingRatesRequest,
    GetShippingRatesResponse,
)
from acme.fulfillment.domain.v1.workflows_p2p import (
    VerifyAddressRequest,
    VerifyAddressResponse,
)
from src.services.enablements_integrations import (
    EnablementsIntegrationError,
    EnablementsIntegrationsClient,
)


class ShippingActivities:
    """Temporal activities that call fixture-backed shipping endpoints."""

    def __init__(self, client: EnablementsIntegrationsClient | None = None) -> None:
        self._client = client or EnablementsIntegrationsClient()

    @activity.defn
    def verify_address(
        self,
        request: VerifyAddressRequest,
    ) -> VerifyAddressResponse:
        try:
            activity.logger.info("verify_address via enablements-api")
            return self._client.verify_address(request)
        except EnablementsIntegrationError as e:
            raise ApplicationError(str(e), type=e.code, non_retryable=e.status < 500) from e

    @activity.defn
    def get_carrier_rates(
        self,
        request: GetShippingRatesRequest,
    ) -> GetShippingRatesResponse:
        selected_shipment_id = (
            request.selected_shipment.easypost.shipment_id
            if request.selected_shipment and request.selected_shipment.easypost
            else ""
        )
        if (not request.from_easypost_id or not request.to_easypost_id) and not selected_shipment_id:
            raise ApplicationError(
                "get_carrier_rates requires valid from_easypost_id and to_easypost_id, "
                "or selected_shipment.easypost.shipment_id",
                non_retryable=True,
            )

        try:
            activity.logger.info(
                "get_carrier_rates via enablements-api, from=%s, to=%s",
                request.from_easypost_id,
                request.to_easypost_id,
            )
            return self._client.get_carrier_rates(request)
        except EnablementsIntegrationError as e:
            raise ApplicationError(str(e), type=e.code, non_retryable=e.status < 500) from e
