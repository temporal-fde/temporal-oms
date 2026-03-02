package com.acme.config;

import java.util.HashMap;
import java.util.Map;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * Binds the 'oms' configuration from acme.oms.yaml to a POJO.
 * Injectable into Activities and other Spring beans.
 */
@Component
@ConfigurationProperties(prefix = "oms")
public class OmsProperties {

    private BoundedContextConfig apps = new BoundedContextConfig();
    private BoundedContextConfig processing = new BoundedContextConfig();
    private BoundedContextConfig risk = new BoundedContextConfig();

    public static class BoundedContextConfig {
        private NexusConfig nexus = new NexusConfig();

        public NexusConfig getNexus() {
            return nexus;
        }

        public void setNexus(NexusConfig nexus) {
            this.nexus = nexus;
        }
    }

    public static class NexusConfig {
        private Map<String, String> endpoints = new HashMap<>();

        public Map<String, String> getEndpoints() {
            return endpoints;
        }

        public void setEndpoints(Map<String, String> endpoints) {
            this.endpoints = endpoints;
        }
    }

    public BoundedContextConfig getApps() {
        return apps;
    }

    public void setApps(BoundedContextConfig apps) {
        this.apps = apps;
    }

    public BoundedContextConfig getProcessing() {
        return processing;
    }

    public void setProcessing(BoundedContextConfig processing) {
        this.processing = processing;
    }

    public BoundedContextConfig getRisk() {
        return risk;
    }

    public void setRisk(BoundedContextConfig risk) {
        this.risk = risk;
    }
}