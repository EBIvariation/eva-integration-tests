# Build stage
FROM maven:3.9-eclipse-temurin-21 AS build

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone the source code
RUN git clone https://github.com/EBIvariation/contig-alias.git .

# Leverage Docker layer caching for dependencies
RUN mvn dependency:go-offline -B

# Build
RUN mvn clean package -DskipTests -Dmaven.gitcommitid.skip=true

# Runtime stage
FROM eclipse-temurin:21-jre
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r contigalias && useradd -r -g contigalias contigalias

# Create config directory for runtime application.properties mount
RUN mkdir -p /app/config && chown -R contigalias:contigalias /app

# Copy the JAR file from build stage
COPY --from=build /app/target/*.jar app.jar

# Copy application.properties from your local build context
COPY contig_alias_ws/application.properties /app/config/application.properties

# Set ownership
RUN chown -R contigalias:contigalias /app

USER contigalias

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/eva/webservices/contig-alias/health || exit 1

# JVM options for containerized environments
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]