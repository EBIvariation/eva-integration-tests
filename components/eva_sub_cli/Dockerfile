FROM python:3.10

ARG SOURCE_GITHUB_REPOSITORY
ARG SOURCE_GITHUB_REF
ARG SOURCE_GITHUB_SHA

ENV vcf_validator_version=0.10.0
ENV NXF_VER=23.10.0
ENV DOCKER_VER=24.0.7


WORKDIR /opt

# Install JAVA and Node
RUN apt update && apt install -y default-jdk nodejs npm git curl

# Install VCF validator
RUN curl -LJo /usr/local/bin/vcf_validator  https://github.com/EBIvariation/vcf-validator/releases/download/v${vcf_validator_version}/vcf_validator_linux \
    && curl -LJo /usr/local/bin/vcf_assembly_checker  https://github.com/EBIvariation/vcf-validator/releases/download/v${vcf_validator_version}/vcf_assembly_checker_linux \
    && chmod 755 /usr/local/bin/vcf_assembly_checker /usr/local/bin/vcf_validator

# Install biovalidator and make it executable
RUN git clone https://github.com/elixir-europe/biovalidator.git  \
    && cd biovalidator  \
    && npm install \
    && npm link

# Install nextflow
RUN curl -L "https://github.com/nextflow-io/nextflow/releases/download/v${NXF_VER}/nextflow-${NXF_VER}-all" | bash \
    && mv nextflow /usr/local/bin/

# Install Docker CLI (not daemon)
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VER}.tgz | tar xzv \
    && mv docker/* /usr/local/bin/ \
    && chmod +x /usr/local/bin/docker

COPY install_repo.sh /opt/

ENV SOURCE_GITHUB_REPOSITORY nitin-ebi/eva-sub-cli
ENV SOURCE_GITHUB_REF remove-non-vcf-file
ENV SOURCE_GITHUB_SHA $SOURCE_GITHUB_SHA

# Run the installation of the repository
RUN ./install_repo.sh

CMD tail -f /dev/null