package com.acme.apps.workflows.activities;

import com.acme.apps.workflows.PreloadedWarehouse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Pre-loads deterministic fixture address IDs for all integration warehouses at workflow startup.
 *
 * Two collections share SKU prefixes so find_alternate_warehouse always has a candidate:
 *   A (primary)  — WH-EAST-01 (ELEC, GADG, TECH), WH-WEST-01 (APRL, HOME, SPRT)
 *   B (alternate) — WH-EAST-02 (ELEC, GADG), WH-WEST-02 (APRL, SPRT), WH-CENT-01 (TECH, HOME)
 */
@Component("integrations-setup-activities")
public class IntegrationsSetupImpl implements IntegrationsSetup {

    private static final Logger logger = LoggerFactory.getLogger(IntegrationsSetupImpl.class);

    private record WarehouseConfig(
            String warehouseId, String fixtureAddressId, String company, String street1, String city,
            String state, String zip, String country, List<String> skuPrefixes) {
    }

    // Collection A first, Collection B after — ordering drives lookupInventoryAddress precedence.
    private static final List<WarehouseConfig> WAREHOUSES = List.of(
            // ── Collection A (primary) ─────────────────────────────────────────────
            new WarehouseConfig("WH-EAST-01", "adr_wh_east_01", "acme", "540 Broad St",              "Newark",        "NJ", "07102", "US", List.of("ELEC-", "GADG-", "TECH-")),
            new WarehouseConfig("WH-WEST-01", "adr_wh_west_01", "acme", "388 Townsend St",           "San Francisco", "CA", "94107", "US", List.of("APRL-", "HOME-", "SPRT-")),
            // ── Collection B (alternates, share SKU prefixes with A) ───────────────
            new WarehouseConfig("WH-EAST-02", "adr_wh_east_02", "acme", "417 Montgomery St",         "San Francisco", "CA", "94104", "US", List.of("ELEC-", "GADG-")),
            new WarehouseConfig("WH-WEST-02", "adr_wh_west_02", "acme", "1600 Amphitheatre Pkwy",    "Mountain View", "CA", "94043", "US", List.of("APRL-", "SPRT-")),
            new WarehouseConfig("WH-CENT-01", "adr_wh_cent_01", "acme", "1901 W Madison St",         "Chicago",       "IL", "60612", "US", List.of("TECH-", "HOME-"))
    );

    @Override
    public List<PreloadedWarehouse> preloadWarehouseAddresses() {
        return WAREHOUSES.stream().map(this::toPreloadedWarehouse).toList();
    }

    private PreloadedWarehouse toPreloadedWarehouse(WarehouseConfig config) {
        logger.info("Loaded fixture warehouse {} with address id={}", config.warehouseId(), config.fixtureAddressId());
        return new PreloadedWarehouse(
                config.warehouseId(),
                config.skuPrefixes(),
                config.fixtureAddressId(),
                config.company(),
                config.street1(),
                config.city(),
                config.state(),
                config.zip(),
                config.country()
        );
    }
}
