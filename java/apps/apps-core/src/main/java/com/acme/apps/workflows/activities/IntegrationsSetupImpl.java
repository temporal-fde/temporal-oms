package com.acme.apps.workflows.activities;

import com.acme.apps.workflows.PreloadedWarehouse;
import com.easypost.exception.EasyPostException;
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
 * Requires a configured EasyPostClient. Throws if the client is absent or verification fails.
 */
@Component("integrations-setup-activities")
public class IntegrationsSetupImpl implements IntegrationsSetup {

    private static final Logger logger = LoggerFactory.getLogger(IntegrationsSetupImpl.class);

    public IntegrationsSetupImpl(EasyPostClient easyPostClient) {
        this.easyPostClient = easyPostClient;
    }

    private record WarehouseConfig(
            String warehouseId, String street1, String city,
            String state, String zip, String country, List<String> skuPrefixes) {
    }

    // Collection A first, Collection B after — ordering drives lookupInventoryAddress precedence.
    private static final List<WarehouseConfig> WAREHOUSES = List.of(
            // ── Collection A (primary) ─────────────────────────────────────────────
            new WarehouseConfig("WH-EAST-01", "540 Broad St",              "Newark",        "NJ", "07102", "US", List.of("ELEC-", "GADG-", "TECH-")),
            new WarehouseConfig("WH-WEST-01", "388 Townsend St",           "San Francisco", "CA", "94107", "US", List.of("APRL-", "HOME-", "SPRT-")),
            // ── Collection B (alternates, share SKU prefixes with A) ───────────────
            new WarehouseConfig("WH-EAST-02", "417 Montgomery St",         "San Francisco", "CA", "94104", "US", List.of("ELEC-", "GADG-")),
            new WarehouseConfig("WH-WEST-02", "1600 Amphitheatre Pkwy",    "Mountain View", "CA", "94043", "US", List.of("APRL-", "SPRT-")),
            new WarehouseConfig("WH-CENT-01", "1901 W Madison St",         "Chicago",       "IL", "60612", "US", List.of("TECH-", "HOME-"))
    );


    private EasyPostClient easyPostClient;

    @Override
    public List<PreloadedWarehouse> preloadWarehouseAddresses() {
        return WAREHOUSES.stream().map(this::verifyWarehouse).toList();
    }

    private PreloadedWarehouse verifyWarehouse(WarehouseConfig config) {

        Map<String, Object> fields = new HashMap<>();
        fields.put("street1", config.street1());
        fields.put("city",    config.city());
        fields.put("state",   config.state());
        fields.put("zip",     config.zip());
        fields.put("country", config.country());

        final com.easypost.model.Address verified;
        try {
            verified = easyPostClient.address.createAndVerify(fields);
        } catch (EasyPostException e) {
            throw new RuntimeException("EasyPost address verification failed for " + config.warehouseId() + ": " + e.getMessage(), e);
        }
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
    }
}
