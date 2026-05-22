# Worker Dockerfile for Fulfillment Service
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

COPY target/fulfillment-workers-*.jar app.jar

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:9072/actuator/health || exit 1

EXPOSE 8061 9072

ENTRYPOINT ["java", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "-jar", "app.jar"]
