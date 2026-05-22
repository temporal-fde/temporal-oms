package com.acme.processing.workflows.activities;

import com.acme.config.OmsProperties;
import com.acme.proto.acme.oms.v1.OmsProperties.BoundedContextConfig;
import com.acme.proto.acme.oms.v1.OmsProperties.BoundedContextConfig.NexusConfig;
import com.acme.proto.acme.processing.domain.processing.v1.ProcessOrderRequestExecutionOptions;
import org.springframework.stereotype.Component;

@Component("processing-options-activities")
public class OptionsImpl implements Options {

    private final OmsProperties omsProperties;

    public OptionsImpl(OmsProperties omsProperties) {
        this.omsProperties = omsProperties;
    }

    @Override
    public ProcessOrderRequestExecutionOptions getOptions(ProcessOrderRequestExecutionOptions input) {
        var props = com.acme.proto.acme.oms.v1.OmsProperties.newBuilder()
                .setApps(mapConfig(omsProperties.getApps()))
                .setProcessing(mapConfig(omsProperties.getProcessing()))
                .build();
        return input.toBuilder().setOmsProperties(props).build();
    }

    private BoundedContextConfig mapConfig(OmsProperties.BoundedContextConfig config) {
        return BoundedContextConfig.newBuilder()
                .setNexus(NexusConfig.newBuilder()
                        .putAllEndpoints(config.getNexus().getEndpoints())
                        .build())
                .build();
    }
}
