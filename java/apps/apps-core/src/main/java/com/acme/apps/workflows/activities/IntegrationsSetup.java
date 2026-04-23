package com.acme.apps.workflows.activities;

import com.acme.apps.workflows.PreloadedWarehouse;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

import java.util.List;

@ActivityInterface
public interface IntegrationsSetup {

    @ActivityMethod
    List<PreloadedWarehouse> preloadWarehouseAddresses();
}
