package com.acme.fulfillment.workflows.activities;

import com.acme.proto.acme.common.v1.Address;
import com.acme.proto.acme.common.v1.EasyPostAddress;
import com.acme.proto.acme.common.v1.Money;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.CarrierRate;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.Errors;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.FulfillmentItem;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.GetCarrierRatesResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.PrintShippingLabelResponse;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressRequest;
import com.acme.proto.acme.fulfillment.domain.fulfillment.v1.VerifyAddressResponse;
import com.easypost.exception.APIException;
import com.easypost.exception.EasyPostException;
import com.easypost.model.FieldError;
import com.easypost.model.Rate;
import com.easypost.model.Shipment;
import com.easypost.service.EasyPostClient;
import io.temporal.failure.ApplicationFailure;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * All EasyPost shipping operations: address verification, carrier rate queries, and label printing.
 * Requires EASYPOST_API_KEY — use an EZT-prefixed test key to avoid purchasing real labels.
 */
@Component("carriersActivities")
public class CarriersImpl implements Carriers {

    private static final Logger logger = LoggerFactory.getLogger(CarriersImpl.class);

    // Parcel estimation constants (EasyPost uses oz for weight, inches for dimensions)
    private static final float BASE_WEIGHT_OZ  = 16.0f;  // 1 lb base
    private static final float WEIGHT_PER_UNIT = 8.0f;   // 0.5 lb per unit
    private static final float PARCEL_LENGTH   = 12.0f;
    private static final float PARCEL_WIDTH    = 8.0f;
    private static final float PARCEL_HEIGHT   = 6.0f;

    @Autowired
    private EasyPostClient easyPostClient;

    @Value("${easypost.warehouse.from-address-id:}")
    private String fromAddressId;

    // ── verifyAddress ─────────────────────────────────────────────────────────

    @Override
    public VerifyAddressResponse verifyAddress(VerifyAddressRequest request) {

        var address = request.getAddress();
        var ep = address.getEasypost();

        logger.info("verifyAddress: {}", ep.getStreet1());

        if (address.hasEasypost() && !ep.getId().isEmpty()) {
            return VerifyAddressResponse.newBuilder().setAddress(address).build();
        }

        Map<String, Object> fields = new HashMap<>();
        fields.put("name",    request.getCustomerId());
        fields.put("street1", ep.getStreet1());
        fields.put("city",    ep.getCity());
        fields.put("state",   ep.getState());
        fields.put("zip",     ep.getZip());
        fields.put("country", ep.getCountry());

        try {
            com.easypost.model.Address verified = easyPostClient.address.createAndVerify(fields);

            boolean isVerified = verified.getVerifications() != null
                    && verified.getVerifications().getDelivery() != null
                    && Boolean.TRUE.equals(verified.getVerifications().getDelivery().getSuccess());

            var easyPostAddress = EasyPostAddress.newBuilder()
                    .setId(verified.getId())
                    .setStreet1(verified.getStreet1() != null ? verified.getStreet1() : ep.getStreet1())
                    .setCity(verified.getCity()       != null ? verified.getCity()    : ep.getCity())
                    .setState(verified.getState()     != null ? verified.getState()   : ep.getState())
                    .setZip(verified.getZip()         != null ? verified.getZip()     : ep.getZip())
                    .setCountry(verified.getCountry() != null ? verified.getCountry() : ep.getCountry())
                    .setResidential(Boolean.TRUE.equals(verified.getResidential()))
                    .build();

            logger.info("verifyAddress succeeded: easypost_id={}, verified={}", verified.getId(), isVerified);

            return VerifyAddressResponse.newBuilder()
                    .setAddress(Address.newBuilder().setEasypost(easyPostAddress).build())
                    .build();

        } catch (EasyPostException e) {
            String addressError = "undefined";
            String failedField  = "undefined";
            List<?> errors = ((APIException) e).getErrors();
            if (errors != null && !errors.isEmpty()) {
                FieldError fieldError = (FieldError) errors.getFirst();
                failedField  = fieldError.getField();
                addressError = fieldError.getMessage();
            }
            throw ApplicationFailure.newNonRetryableFailureWithCause(
                    addressError + ". Error with field '" + failedField + "'",
                    Errors.ERROR_ADDRESS_VERIFY_FAILED.name(), e);
        }
    }

    // ── getCarrierRates ───────────────────────────────────────────────────────

    @Override
    public GetCarrierRatesResponse getCarrierRates(GetCarrierRatesRequest request) {
        if (easyPostClient == null) {
            throw ApplicationFailure.newNonRetryableFailure(
                    "EasyPost API key is not configured — set EASYPOST_API_KEY",
                    "EASYPOST_NOT_CONFIGURED");
        }

        float weightOz = estimateWeightOz(request.getItemsList());

        Map<String, Object> parcel = Map.of(
                "weight", weightOz,
                "length", PARCEL_LENGTH,
                "width",  PARCEL_WIDTH,
                "height", PARCEL_HEIGHT);

        Map<String, Object> params = new HashMap<>();
        params.put("to_address",   Map.of("id", request.getEasypostAddressId()));
        params.put("from_address", buildFromAddress());
        params.put("parcel",       parcel);

        try {
            Shipment shipment = easyPostClient.shipment.create(params);

            List<CarrierRate> rates = shipment.getRates().stream()
                    .map(this::toCarrierRate)
                    .toList();

            logger.info("getCarrierRates: order_id={}, shipment_id={}, rates={}",
                    request.getOrderId(), shipment.getId(), rates.size());

            return GetCarrierRatesResponse.newBuilder()
                    .setShipmentId(shipment.getId())
                    .addAllRates(rates)
                    .build();

        } catch (EasyPostException e) {
            throw ApplicationFailure.newFailureWithCause(
                    "Failed to retrieve carrier rates for order " + request.getOrderId(),
                    "CARRIER_RATES_FAILED", e);
        }
    }

    // ── printShippingLabel ────────────────────────────────────────────────────

    @Override
    public PrintShippingLabelResponse printShippingLabel(PrintShippingLabelRequest request) {

        try {
            Shipment shipment = easyPostClient.shipment.retrieve(request.getShipmentId());

            logger.info("Shipment ID: {}", shipment.getId());
            logger.info("Shipment status: {}", shipment.getStatus());

            for (Rate r : shipment.getRates()) {
                logger.info("Available rate: {}", r.getId());
            }

            logger.info("Using rate: {}", request.getRateId());
            Map<String, Object> buyParams = new HashMap<>();
            buyParams.put("rate",  request.getRateId());

            Shipment purchased = easyPostClient.shipment.buy(request.getShipmentId(), buyParams);

            String trackingNumber = purchased.getTrackingCode() != null ? purchased.getTrackingCode() : "";
            String labelUrl = purchased.getPostageLabel() != null
                    ? purchased.getPostageLabel().getLabelUrl()
                    : "";

            logger.info("printShippingLabel: order_id={}, tracking={}", request.getOrderId(), trackingNumber);

            return PrintShippingLabelResponse.newBuilder()
                    .setTrackingNumber(trackingNumber)
                    .setLabelUrl(labelUrl)
                    .build();

        } catch (EasyPostException e) {
            logger.error("EasyPost EasyPostException: {}", e.getMessage());

            if (e.getCause() instanceof com.easypost.exception.API.InvalidRequestError ire) {

                if (ire.getErrors() != null) {
                    for (Object err : ire.getErrors()) {
                        logger.error("EasyPost field error: {}", err);
                    }
                }
//
//                if (ire.getParam() != null) {
//                    logger.error("Invalid param: {}", ire.getParam());
//                }
            }
            throw ApplicationFailure.newFailureWithCause(
                    "Failed to purchase label for shipment " + request.getShipmentId(),
                    "LABEL_PRINT_FAILED", e);
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private Map<String, Object> buildFromAddress() {
        if (fromAddressId != null && !fromAddressId.isBlank()) {
            return Map.of("id", fromAddressId);
        }
        // Matches WH-EAST-01 in IntegrationsSetupImpl; override with EASYPOST_WAREHOUSE_FROM_ADDRESS_ID.
        return Map.of(
                "street1", "100 Commerce Drive",
                "city",    "Newark",
                "state",   "NJ",
                "zip",     "07102",
                "country", "US");
    }

    private static float estimateWeightOz(List<FulfillmentItem> items) {
        int totalUnits = items.stream().mapToInt(FulfillmentItem::getQuantity).sum();
        return BASE_WEIGHT_OZ + (WEIGHT_PER_UNIT * Math.max(1, totalUnits));
    }

    private CarrierRate toCarrierRate(Rate rate) {
        long costCents = rate.getRate() != null ? Math.round(rate.getRate() * 100) : 0L;
        int deliveryDays = rate.getDeliveryDays() != null ? rate.getDeliveryDays().intValue() : 0;
        return CarrierRate.newBuilder()
                .setRateId(rate.getId())
                .setCarrier(rate.getCarrier()   != null ? rate.getCarrier()  : "")
                .setServiceLevel(rate.getService() != null ? rate.getService() : "")
                .setCost(Money.newBuilder().setCurrency("USD").setUnits(costCents).build())
                .setEstimatedDays(deliveryDays)
                .build();
    }
}
