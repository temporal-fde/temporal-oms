package com.acme.apps.workflows.activities;

import com.acme.config.OmsProperties;
import com.acme.proto.acme.apps.domain.apps.v1.CompleteOrderRequestExecutionOptions;
import com.acme.proto.acme.apps.domain.apps.v1.GetCompleteOrderStateResponse;
import com.acme.proto.acme.apps.domain.apps.v1.GetOptionsRequest;
import com.acme.proto.acme.oms.v1.OmsProperties.BoundedContextConfig;
import com.acme.proto.acme.oms.v1.OmsProperties.BoundedContextConfig.NexusConfig;
import io.temporal.activity.Activity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component("options-activities")
public class OptionsImpl implements Options {
    private final OmsProperties properties;
    private Logger logger = LoggerFactory.getLogger(OptionsImpl.class);
    public OptionsImpl(OmsProperties properties) {
        this.properties = properties;
        logger.info("OmsProperties injected - Apps endpoints: {}, Processing endpoints: {}, Risk endpoints: {}",
                properties.getApps().getNexus().getEndpoints(),
                properties.getProcessing().getNexus().getEndpoints(),
                properties.getRisk().getNexus().getEndpoints());
    }
    @Override
    public CompleteOrderRequestExecutionOptions getOptions(GetOptionsRequest cmd) {
        var props = com.acme.proto.acme.oms.v1.OmsProperties.newBuilder()
                .setApps(mapBoundedContextConfig(properties.getApps()))
                .setProcessing(mapBoundedContextConfig(properties.getProcessing()))
                .setRisk(mapBoundedContextConfig(properties.getRisk()))
                .build();

        logger.info("Options: {}", props);
        // TODO load from environment
        var originalTimeoutSecs = Math.max(86400 * 30, cmd.getOptions().getCompletionTimeoutSecs());
        var actualTtl = getRemainingTimeoutSecs(originalTimeoutSecs, cmd.getTimestamp().getSeconds());
        return CompleteOrderRequestExecutionOptions.newBuilder()
                .setOmsProperties(props)
                .setCompletionTimeoutSecs(actualTtl)
                .setProcessingTimeoutSecs(actualTtl)
                .build();
    }

    /**
     * Calculate remaining timeout accounting for wall-clock elapsed time since transaction start.
     * This is important when Temporal workers are down - the timeout should consider the
     * time elapsed since the original request, not restart from when workers come back online.
     */
    public long getRemainingTimeoutSecs(long originalTimeoutSecs, long transactionStartSecs) {

        long activityScheduledSecs = Activity.getExecutionContext().getInfo().getScheduledTimestamp() / 1000;
        long elapsedSecs = activityScheduledSecs - transactionStartSecs;
        long remainingSecs = originalTimeoutSecs - elapsedSecs;
        return Math.max(0, remainingSecs);
    }

    private BoundedContextConfig mapBoundedContextConfig(OmsProperties.BoundedContextConfig config) {
        return BoundedContextConfig.newBuilder()
                .setNexus(NexusConfig.newBuilder()
                        .putAllEndpoints(config.getNexus().getEndpoints())
                        .build())
                .build();
    }
}
