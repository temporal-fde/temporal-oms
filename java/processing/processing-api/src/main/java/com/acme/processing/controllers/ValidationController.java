package com.acme.processing.controllers;

import com.acme.processing.workflows.SupportTeam;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.temporal.client.WorkflowClient;
import io.temporal.client.WorkflowOptions;
import io.temporal.client.WorkflowUpdateException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * Validation Controller
 *
 * Exposes REST endpoints for workflow validation updates.
 * Replaces temporal CLI calls for manual validation workflows.
 *
 * URI Template: /api/v1/validations/{orderId}
 */
@RestController
@RequestMapping("/api/v1/validations")
@Tag(name = "Validations", description = "REST endpoints for order validation updates")
public class ValidationController {

    private static final Logger logger = LoggerFactory.getLogger(ValidationController.class);

    private final WorkflowClient workflowClient;

    public ValidationController(WorkflowClient workflowClient) {
        this.workflowClient = workflowClient;
    }

    /**
     * Complete order validation through support team
     *
     * Executes the completeOrderValidation update on the support-team workflow
     * in the processing namespace.
     *
     * URI Template: POST /api/v1/validations/{orderId}/complete
     *
     * @param orderId the order ID that validation is being completed for
     * @return 202 Accepted with operation details
     */
    @PostMapping("/{orderId}/complete")
    @Operation(
        summary = "Complete order validation",
        description = "Executes the completeOrderValidation update on the support-team workflow in the processing namespace. " +
                      "This signals that manual validation has been completed and the order can proceed."
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "202", description = "Validation update accepted",
            content = @Content(schema = @Schema(implementation = ValidationUpdateResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request or missing orderId"),
        @ApiResponse(responseCode = "409", description = "Workflow conflict or validation already completed"),
        @ApiResponse(responseCode = "500", description = "Unexpected error executing validation update")
    })
    public ResponseEntity<ValidationUpdateResponse> completeValidation(
            @Parameter(description = "Order ID for validation completion", required = true)
            @PathVariable String orderId) {

        logger.info("Received validation completion request for orderId: {}", orderId);

        try {
            // Get workflow stub for the support-team workflow
            SupportTeam workflow = workflowClient.newWorkflowStub(SupportTeam.class, "support-team");

            // Execute the completeOrderValidation update
            workflow.completeOrderValidation(orderId);

            logger.info("Validation completion update executed successfully for orderId: {}", orderId);

            var response = new ValidationUpdateResponse(
                orderId,
                "accepted",
                "completeOrderValidation",
                "Update accepted - support team workflow will process validation completion"
            );

            return ResponseEntity.accepted().body(response);

        } catch (WorkflowUpdateException e) {
            logger.error("Failed to execute validation update: {}", e.getMessage(), e);
            var errorResponse = new ValidationUpdateResponse(
                orderId,
                "failed",
                "completeOrderValidation",
                "Workflow conflict or update failed: " + e.getMessage()
            );
            return ResponseEntity.status(HttpStatus.CONFLICT).body(errorResponse);

        } catch (Exception e) {
            logger.error("Unexpected error executing validation update: {}", e.getMessage(), e);
            var errorResponse = new ValidationUpdateResponse(
                orderId,
                "error",
                "completeOrderValidation",
                "Unexpected error: " + e.getMessage()
            );
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Response DTO for validation updates
     */
    public static class ValidationUpdateResponse {
        public String orderId;
        public String status;
        public String updateName;
        public String message;

        public ValidationUpdateResponse(String orderId, String status, String updateName, String message) {
            this.orderId = orderId;
            this.status = status;
            this.updateName = updateName;
            this.message = message;
        }

        public String getOrderId() {
            return orderId;
        }

        public String getStatus() {
            return status;
        }

        public String getUpdateName() {
            return updateName;
        }

        public String getMessage() {
            return message;
        }
    }
}
