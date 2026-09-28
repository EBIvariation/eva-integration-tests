# Build stage
FROM maven:3.9-eclipse-temurin-21 AS build

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone the source code
RUN git clone https://github.com/EBIvariation/eva-ws.git .

# Copy the full project
RUN mvn dependency:go-offline -B

# Build only count-stats and its required dependencies
RUN mvn -pl count-stats -am clean package -DskipTests -Dmaven.gitcommitid.skip=true

# Runtime stage
FROM eclipse-temurin:21-jre
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r count_stats && useradd -r -g count_stats count_stats

# Create config directory for runtime application.properties mount
RUN mkdir -p /app/config && chown -R count_stats:count_stats /app

# Copy the JAR file from build stage
COPY --from=build /app/count-stats/target/*.jar app.jar

# Copy application.properties from your local build context
COPY eva_ws/application.properties /app/config/application.properties

# Set ownership
RUN chown -R count_stats:count_stats /app

USER count_stats

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/eva/webservices/count-stats/health || exit 1

# JVM options for containerized environments
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]