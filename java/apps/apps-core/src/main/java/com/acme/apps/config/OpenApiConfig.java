package com.acme.apps.config;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeIn;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Contact;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.info.License;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import io.swagger.v3.oas.annotations.servers.Server;
import org.springframework.context.annotation.Configuration;

/**
 * OpenAPI / Swagger Configuration
 *
 * Exposes Swagger UI at /docs (MANDATORY per stack-api-rest skill)
 * OpenAPI spec available at /v3/api-docs
 */
@Configuration
@OpenAPIDefinition(
    info = @Info(
        title = "Temporal OMS API",
        version = "1.0.0",
        description = """
            Temporal Order Management System REST API

            ## Architecture

            This API serves as the entry point for the Temporal-based order management system.
            It exposes webhook endpoints for external integrations (commerce-app, payments-app)
            and order query endpoints for the frontend.

            ## URI Templates

            All endpoints are documented using RFC 6570 URI Template syntax:
            - `{variable}` - Path parameter
            - `{?param}` - Query parameter

            ## Authentication

            API Key authentication via `X-API-Key` header.
            Different keys for commerce-app and payments-app webhooks.
            """,
        contact = @Contact(
            name = "ACME Engineering",
            email = "engineering@acme.com"
        ),
        license = @License(
            name = "MIT",
            url = "https://opensource.org/licenses/MIT"
        )
    ),
    servers = {
        @Server(url = "http://localhost:8080", description = "Local development"),
        @Server(url = "https://api.acme.com", description = "Production")
    }
)
@SecurityScheme(
    name = "ApiKeyAuth",
    description = "API Key authentication for webhook endpoints",
    type = SecuritySchemeType.APIKEY,
    in = SecuritySchemeIn.HEADER,
    paramName = "X-API-Key"
)
public class OpenApiConfig {
    // Configuration is done via annotations
}