package com.acme.apps.workflows;

import com.acme.apps.workflows.activities.IntegrationsSetup;
import com.acme.proto.acme.apps.domain.apps.v1.StartIntegrationsRequest;
import com.acme.proto.acme.common.v1.Address;
import com.acme.proto.acme.common.v1.EasyPostAddress;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FindAlternateWarehouseResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.LookupInventoryAddressResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.ShippingLineItem;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichOrderResponse;
import com.acme.proto.acme.processing.domain.processing.v1.EnrichedItem;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidateOrderResponse;
import com.acme.proto.acme.processing.domain.processing.v1.ValidatePaymentRequest;
import com.acme.proto.acme.processing.domain.processing.v1.ValidatePaymentResponse;
import io.temporal.activity.ActivityOptions;
import io.temporal.common.VersioningBehavior;
import io.temporal.workflow.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class IntegrationsImpl implements Integrations {

    private static final Logger logger = LoggerFactory.getLogger(IntegrationsImpl.class);

    // ── Static item catalog ───────────────────────────────────────────────────
    // sku_id prefixes correspond to warehouse SKU prefix lists in IntegrationsSetupImpl.
    private static final Map<String, EnrichedItem> ITEM_CATALOG = Map.of(
            "ITEM-ELEC-001", item("ITEM-ELEC-001", "ELEC-SKU-001", "NEXGEN"),
            "ITEM-ELEC-002", item("ITEM-ELEC-002", "ELEC-SKU-002", "NEXGEN"),
            "ITEM-GADG-001", item("ITEM-GADG-001", "GADG-SKU-001", "GADGETCO"),
            "ITEM-GADG-002", item("ITEM-GADG-002", "GADG-SKU-002", "GADGETCO"),
            "ITEM-TECH-001", item("ITEM-TECH-001", "TECH-SKU-001", "TECHCORE"),
            "ITEM-APRL-001", item("ITEM-APRL-001", "APRL-SKU-001", "STYLEHAUS"),
            "ITEM-HOME-001", item("ITEM-HOME-001", "HOME-SKU-001", "HOMECO"),
            "ITEM-SPRT-001", item("ITEM-SPRT-001", "SPRT-SKU-001", "SPORTMAX"),
            "ITEM-SPRT-002", item("ITEM-SPRT-002", "SPRT-SKU-002", "SPORTMAX"),
            "ITEM-APRL-002", item("ITEM-APRL-002", "APRL-SKU-002", "STYLEHAUS")
    );

    private final IntegrationsSetup setup;

    // Populated in execute() after preload activity completes.
    // Order: Collection A (primary) first, Collection B (alternates) second.
    private List<PreloadedWarehouse> warehouses;

    @WorkflowInit
    public IntegrationsImpl(StartIntegrationsRequest request) {
        this.setup = Workflow.newActivityStub(IntegrationsSetup.class,
                ActivityOptions.newBuilder()
                        .setStartToCloseTimeout(Duration.ofSeconds(60))
                        .build());
    }

    @Override
    @WorkflowVersioningBehavior(VersioningBehavior.PINNED)
    public void execute(StartIntegrationsRequest request) {
        logger.info("apps.Integrations started (singleton) — preloading warehouse addresses");
        this.warehouses = setup.preloadWarehouseAddresses();
        logger.info("apps.Integrations ready with {} warehouses", warehouses.size());
        Workflow.await(() -> false);
    }

    // ── CommerceApp ───────────────────────────────────────────────────────────

    @Override
    public void validateValidateOrder(ValidateOrderRequest request) {}

    @Override
    public ValidateOrderResponse validateOrder(ValidateOrderRequest request) {
        boolean invalid = request.getOrder().getOrderId().contains("invalid");
        logger.info("validateOrder orderId={}, invalid={}", request.getOrder().getOrderId(), invalid);
        return ValidateOrderResponse.newBuilder()
                .setOrder(request.getOrder())
                .setManualCorrectionNeeded(invalid)
                .build();
    }

    // ── PIMS ──────────────────────────────────────────────────────────────────

    @Override
    public void validateEnrichOrder(EnrichOrderRequest request) {}

    @Override
    public EnrichOrderResponse enrichOrder(EnrichOrderRequest request) {
        logger.info("enrichOrder orderId={}", request.getOrder().getOrderId());
        List<EnrichedItem> enriched = request.getOrder().getItemsList().stream()
                .map(item -> {
                    EnrichedItem catalogEntry = ITEM_CATALOG.get(item.getItemId());
                    if (catalogEntry != null) {
                        return catalogEntry.toBuilder().setQuantity(item.getQuantity()).build();
                    }
                    // Unknown item: assign an ELEC- SKU so it deterministically maps to WH-EAST-01
                    return EnrichedItem.newBuilder()
                            .setItemId(item.getItemId())
                            .setSkuId("ELEC-" + item.getItemId())
                            .setBrandCode("GENERIC")
                            .setQuantity(item.getQuantity())
                            .build();
                })
                .toList();
        return EnrichOrderResponse.newBuilder()
                .setOrder(request.getOrder())
                .addAllItems(enriched)
                .build();
    }

    // ── Payments ──────────────────────────────────────────────────────────────

    @Override
    public void validateValidatePayment(ValidatePaymentRequest request) {}

    @Override
    public ValidatePaymentResponse validatePayment(ValidatePaymentRequest request) {
        logger.info("validatePayment rrn={}", request.getRrn());
        return ValidatePaymentResponse.newBuilder()
                .setValid(true)
                .setPaymentStatus("AUTHORIZED")
                .setActualAmountCents(request.getExpectedAmountCents())
                .build();
    }

    // ── Inventory ─────────────────────────────────────────────────────────────

    @Override
    public void validateLookupInventoryAddress(LookupInventoryAddressRequest request) {}

    @Override
    public LookupInventoryAddressResponse lookupInventoryAddress(LookupInventoryAddressRequest request) {
        Workflow.await(() -> warehouses != null);
        logger.info("lookupInventoryAddress items={}", request.getItemsCount());

        // If a specific address_id is provided, return that warehouse directly.
        if (request.hasAddressId() && !request.getAddressId().isBlank()) {
            return warehouses.stream()
                    .filter(wh -> wh.easypostId().equals(request.getAddressId()))
                    .findFirst()
                    .map(wh -> LookupInventoryAddressResponse.newBuilder().setAddress(toAddress(wh)).build())
                    .orElse(LookupInventoryAddressResponse.getDefaultInstance());
        }

        // Find the first warehouse (collection A first) whose SKU prefixes cover the items.
        String skuId = request.getItemsCount() > 0
                ? request.getItems(0).getSkuId()
                : "";

        PreloadedWarehouse match = warehouses.stream()
                .filter(wh -> handlesSkuId(wh, skuId))
                .findFirst()
                .orElse(warehouses.get(0));

        logger.info("lookupInventoryAddress resolved to locationId={}, easypostId={}",
                match.locationId(), match.easypostId());
        return LookupInventoryAddressResponse.newBuilder().setAddress(toAddress(match)).build();
    }

    @Override
    public void validateFindAlternateWarehouse(FindAlternateWarehouseRequest request) {}

    @Override
    public FindAlternateWarehouseResponse findAlternateWarehouse(FindAlternateWarehouseRequest request) {
        Workflow.await(() -> warehouses != null);
        logger.info("findAlternateWarehouse currentAddressId={}", request.getCurrentAddressId());

        String skuId = request.getItemsCount() > 0
                ? request.getItems(0).getSkuId()
                : "";

        Optional<PreloadedWarehouse> alt = warehouses.stream()
                .filter(wh -> !wh.easypostId().equals(request.getCurrentAddressId()))
                .filter(wh -> handlesSkuId(wh, skuId))
                .findFirst();

        alt.ifPresentOrElse(
                wh -> logger.info("findAlternateWarehouse resolved to locationId={}, easypostId={}",
                        wh.warehouseId(), wh.easypostId()),
                () -> logger.info("findAlternateWarehouse: no alternate found for skuId={}", skuId));

        FindAlternateWarehouseResponse.Builder resp = FindAlternateWarehouseResponse.newBuilder();
        alt.ifPresent(wh -> resp.setAddress(toAddress(wh)));
        return resp.build();
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static boolean handlesSkuId(PreloadedWarehouse wh, String skuId) {
        if (wh.skuPrefixes().isEmpty()) return true;
        return wh.skuPrefixes().stream().anyMatch(skuId::startsWith);
    }

    private static Address toAddress(PreloadedWarehouse wh) {
        return Address.newBuilder()
                .setEasypost(EasyPostAddress.newBuilder()
                        .setId(wh.easypostId())
                        .setStreet1(wh.street1())
                        .setCity(wh.city())
                        .setState(wh.state())
                        .setZip(wh.zip())
                        .setCountry(wh.country())
                        .build())
                .build();
    }

    private static EnrichedItem item(String itemId, String skuId, String brandCode) {
        return EnrichedItem.newBuilder()
                .setItemId(itemId)
                .setSkuId(skuId)
                .setBrandCode(brandCode)
                .build();
    }
}
