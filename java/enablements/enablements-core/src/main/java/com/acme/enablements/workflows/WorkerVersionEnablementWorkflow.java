package com.acme.enablements.workflows;

import com.acme.proto.acme.enablements.v1.DeployWorkerVersionRequest;
import com.acme.proto.acme.enablements.v1.StartWorkerVersionEnablementRequest;
import com.acme.proto.acme.enablements.v1.WorkerVersionEnablementState;
import io.temporal.workflow.QueryMethod;
import io.temporal.workflow.SignalMethod;
import io.temporal.workflow.WorkflowInterface;
import io.temporal.workflow.WorkflowMethod;

/**
 * Workflow for demonstrating safe worker version transitions under load.
 *
 * This workflow submits orders to the OMS while allowing manual control over
 * worker version transitions. It demonstrates that version changes don't affect
 * external callers or order processing.
 *
 * Life cycle:
 * 1. RUNNING_V1_ONLY: Submit orders, all handled by v1 workers
 * 2. transitionToV2() signal received: Deploy v2 workers
 * 3. RUNNING_BOTH: Continue submitting orders, new ones go to v2
 * 4. COMPLETE: All orders submitted and workflow ends
 */
@WorkflowInterface
public interface WorkerVersionEnablementWorkflow {

  /**
   * Start a new enablement demonstration.
   *
   * @param request Contains demonstration ID, order count, submission rate, and timeout
   */
  @WorkflowMethod
  void execute(StartWorkerVersionEnablementRequest request);

  /**
   * Query current workflow execution state.
   *
   * @return Current state including phase, submission count, rate, and active versions
   */
  @QueryMethod
  WorkerVersionEnablementState getState();

  /**
   * Pause order submission.
   */
  @SignalMethod
  void pause();

  /**
   * Resume order submission.
   */
  @SignalMethod
  void resume();

  /**
   * Trigger deployment of v2 workers and transition to RUNNING_BOTH phase.
   */
  @SignalMethod
  void deployWorkerVersion(DeployWorkerVersionRequest cmd);
}
