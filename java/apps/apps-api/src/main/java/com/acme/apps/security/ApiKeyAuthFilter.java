//package com.acme.apps.security;
//
//import jakarta.servlet.FilterChain;
//import jakarta.servlet.ServletException;
//import jakarta.servlet.http.HttpServletRequest;
//import jakarta.servlet.http.HttpServletResponse;
//import org.slf4j.Logger;
//import org.slf4j.LoggerFactory;
//import org.springframework.beans.factory.annotation.Value;
//import org.springframework.stereotype.Component;
//import org.springframework.web.filter.OncePerRequestFilter;
//
//import java.io.IOException;
//import java.util.Map;
//
///**
// * API Key Authentication Filter
// *
// * Validates X-API-Key header for webhook endpoints
// * Different keys for commerce-app and payments-app
// */
//@Component
//public class ApiKeyAuthFilter extends OncePerRequestFilter {
//
//    private static final Logger logger = LoggerFactory.getLogger(ApiKeyAuthFilter.class);
//    private static final String API_KEY_HEADER = "X-API-Key";
//
//    @Value("${api.keys.commerce-app}")
//    private String commerceApiKey;
//
//    @Value("${api.keys.payments-app}")
//    private String paymentsApiKey;
//
//    @Override
//    protected void doFilterInternal(
//            HttpServletRequest request,
//            HttpServletResponse response,
//            FilterChain filterChain) throws ServletException, IOException {
//
//        String path = request.getRequestURI();
//
//        // Skip authentication for health checks, actuator, and Swagger
//        if (path.startsWith("/actuator") ||
//            path.startsWith("/docs") ||
//            path.startsWith("/v3/api-docs") ||
//            path.startsWith("/swagger-ui")) {
//            filterChain.doFilter(request, response);
//            return;
//        }
//
//        // Check if this is a protected webhook endpoint
//        if (path.contains("/commerce-app/") || path.contains("/payments-app/")) {
//            String apiKey = request.getHeader(API_KEY_HEADER);
//
//            if (apiKey == null || apiKey.isEmpty()) {
//                logger.warn("Missing API key for path: {}", path);
//                response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Missing API key");
//                return;
//            }
//
//            // Validate API key based on endpoint
//            Map<String, String> validKeys = Map.of(
//                "commerce-app", commerceApiKey,
//                "payments-app", paymentsApiKey
//            );
//
//            boolean isValid = validKeys.entrySet().stream()
//                .anyMatch(entry -> path.contains("/" + entry.getKey() + "/") &&
//                                  apiKey.equals(entry.getValue()));
//
//            if (!isValid) {
//                logger.warn("Invalid API key for path: {}", path);
//                response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Invalid API key");
//                return;
//            }
//
//            logger.debug("API key validated for path: {}", path);
//        }
//
//        filterChain.doFilter(request, response);
//    }
//}