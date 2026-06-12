FROM --platform=linux/amd64 python:3.10

ARG SOURCE_GITHUB_REPOSITORY
ARG SOURCE_GITHUB_REF
ARG SOURCE_GITHUB_SHA

ENV vcf_validator_version=0.10.0
ENV NXF_VER=25.10.4
ENV DOCKER_VER=27.5.1


WORKDIR /opt

# Install JAVA 21 and Node
RUN apt update && apt -qq install -y wget apt-transport-https gnupg nodejs npm git curl \
    && wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor -o /usr/share/keyrings/adoptium.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb bookworm main" > /etc/apt/sources.list.d/adoptium.list \
    && apt update && apt -qq install -y temurin-21-jdk \
    && java -version

ENV JAVA_HOME=/usr/lib/jvm/temurin-21-jdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install VCF validator
RUN curl -LJo /usr/local/bin/vcf_validator  https://github.com/EBIvariation/vcf-validator/releases/download/v${vcf_validator_version}/vcf_validator_linux \
    && curl -LJo /usr/local/bin/vcf_assembly_checker  https://github.com/EBIvariation/vcf-validator/releases/download/v${vcf_validator_version}/vcf_assembly_checker_linux \
    && chmod 755 /usr/local/bin/vcf_assembly_checker /usr/local/bin/vcf_validator

# Install biovalidator and make it executable
RUN apt update && apt -qq install -y build-essential \
    && pip3 install --break-system-packages gyp-next \
    && git clone https://github.com/elixir-europe/biovalidator.git  \
    && cd biovalidator  \
    && npm install \
    && npm link

# Install nextflow
RUN curl -fsSL "https://github.com/nextflow-io/nextflow/releases/download/v${NXF_VER}/nextflow" -o /usr/local/bin/nextflow \
    && chmod +x /usr/local/bin/nextflow \
    && nextflow -version

# Install Docker CLI (not daemon)
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VER}.tgz | tar xzv \
    && mv docker/* /usr/local/bin/ \
    && chmod +x /usr/local/bin/docker

COPY install_repo.sh /opt/

ENV SOURCE_GITHUB_REPOSITORY $SOURCE_GITHUB_REPOSITORY
ENV SOURCE_GITHUB_REF $SOURCE_GITHUB_REF
ENV SOURCE_GITHUB_SHA $SOURCE_GITHUB_SHA

# Run the installation of the repository
RUN ./install_repo.sh

CMD tail -f /dev/null