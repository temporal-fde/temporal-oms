# Worker Dockerfile for Enablements Service
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

COPY target/enablements-workers-*.jar app.jar

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

ENTRYPOINT ["java", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "-jar", "app.jar"]
