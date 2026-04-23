package com.acme.apps.workflows.activities;

import com.acme.apps.workflows.PreloadedWarehouse;
import com.easypost.service.EasyPostClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Pre-loads EasyPost address IDs for all integration warehouses at workflow startup.
 *
 * Two collections share SKU prefixes so find_alternate_warehouse always has a candidate:
 *   A (primary)  — WH-EAST-01 (ELEC, GADG, TECH), WH-WEST-01 (APRL, HOME, SPRT)
 *   B (alternate) — WH-EAST-02 (ELEC, GADG), WH-WEST-02 (APRL, SPRT), WH-CENT-01 (TECH, HOME)
 *
 * Falls back to deterministic placeholder IDs if EasyPost is not configured.
 */
@Component("integrations-setup-activities")
public class IntegrationsSetupImpl implements IntegrationsSetup {

    private static final Logger logger = LoggerFactory.getLogger(IntegrationsSetupImpl.class);

    private record WarehouseConfig(
            String warehouseId, String street1, String city,
            String state, String zip, String country, List<String> skuPrefixes) {
    }

    // Collection A first, Collection B after — ordering drives lookupInventoryAddress precedence.
    private static final List<WarehouseConfig> WAREHOUSES = List.of(
            // ── Collection A (primary) ─────────────────────────────────────────────
            new WarehouseConfig("WH-EAST-01", "100 Commerce Drive",    "Newark",      "NJ", "07102", "US", List.of("ELEC-", "GADG-", "TECH-")),
            new WarehouseConfig("WH-WEST-01", "500 Industrial Blvd",   "Los Angeles", "CA", "90058", "US", List.of("APRL-", "HOME-", "SPRT-")),
            // ── Collection B (alternates, share SKU prefixes with A) ───────────────
            new WarehouseConfig("WH-EAST-02", "75 State Street",       "Boston",      "MA", "02109", "US", List.of("ELEC-", "GADG-")),
            new WarehouseConfig("WH-WEST-02", "400 Broad Street",      "Seattle",     "WA", "98109", "US", List.of("APRL-", "SPRT-")),
            new WarehouseConfig("WH-CENT-01", "200 Freight Way",       "Chicago",     "IL", "60612", "US", List.of("TECH-", "HOME-"))
    );

    @Autowired(required = false)
    private EasyPostClient easyPostClient;

    @Override
    public List<PreloadedWarehouse> preloadWarehouseAddresses() {
        return WAREHOUSES.stream().map(this::verifyWarehouse).toList();
    }

    private PreloadedWarehouse verifyWarehouse(WarehouseConfig config) {
        if (easyPostClient == null) {
            return placeholder(config);
        }
        try {
            Map<String, Object> fields = new HashMap<>();
            fields.put("street1", config.street1());
            fields.put("city",    config.city());
            fields.put("state",   config.state());
            fields.put("zip",     config.zip());
            fields.put("country", config.country());

            var verified = easyPostClient.address.createAndVerify(fields);
            logger.info("EasyPost verified {} → id={}", config.warehouseId(), verified.getId());
            return new PreloadedWarehouse(
                    config.warehouseId(),
                    config.skuPrefixes(),
                    verified.getId(),
                    verified.getStreet1() != null ? verified.getStreet1() : config.street1(),
                    verified.getCity()    != null ? verified.getCity()    : config.city(),
                    verified.getState()   != null ? verified.getState()   : config.state(),
                    verified.getZip()     != null ? verified.getZip()     : config.zip(),
                    config.country()
            );
        } catch (Exception e) {
            logger.warn("EasyPost verification failed for {} ({}): {} — using placeholder",
                    config.warehouseId(), config.street1(), e.getMessage());
            return placeholder(config);
        }
    }

    private static PreloadedWarehouse placeholder(WarehouseConfig config) {
        String id = "adr_" + config.warehouseId().toLowerCase().replace("-", "_");
        return new PreloadedWarehouse(
                config.warehouseId(), config.skuPrefixes(),
                id, config.street1(), config.city(), config.state(), config.zip(), config.country());
    }
}
