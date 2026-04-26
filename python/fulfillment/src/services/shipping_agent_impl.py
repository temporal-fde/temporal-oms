from __future__ import annotations

import uuid

from nexusrpc.handler import StartOperationContext, service_handler, sync_operation
from temporalio import nexus
from temporalio.client import WithStartWorkflowOperation
from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy

from acme.fulfillment.domain.v1.shipping_agent_p2p import (
    CalculateShippingOptionsRequest,
    CalculateShippingOptionsResponse,
    StartShippingAgentRequest,
)
from src.agents.workflows.shipping_agent import ShippingAgent


@service_handler(name="ShippingAgent")
class ShippingAgentImpl:
    @sync_operation(name="calculateShippingOptions")
    async def calculate_shipping_options(
        self,
        ctx: StartOperationContext,
        input: CalculateShippingOptionsRequest,
    ) -> CalculateShippingOptionsResponse:
        client = nexus.client()
        # Use request_id from the Nexus context as the update ID so that
        # retries of the same Nexus operation reuse the same update attempt
        # (idempotent), but a genuinely new call gets a new update.
        update_id = ctx.request_id or str(uuid.uuid4())
        return await client.execute_update_with_start_workflow(
            ShippingAgent.calculate_shipping_options,
            args=[input],
            id=update_id,
            result_type=CalculateShippingOptionsResponse,
            start_workflow_operation=WithStartWorkflowOperation(
                ShippingAgent.run,
                args=[StartShippingAgentRequest(customer_id=input.customer_id)],
                id=input.customer_id,
                task_queue="agents",
                id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING,
                id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
            ),
        )
