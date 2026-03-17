# Worker Dockerfile for Apps Service
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Copy the Worker JAR
COPY target/apps-workers-*.jar app.jar

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Health check via actuator
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:9091/actuator/health || exit 1

EXPOSE 9091

# Run the Worker with graceful shutdown
ENTRYPOINT ["java", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "-jar", "app.jar"]
