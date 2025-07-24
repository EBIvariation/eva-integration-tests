FROM python:3.10

ENV vcf_validator_version=0.9.4
ENV NXF_VER=22.10.6

ARG REPO_URL=https://github.com/apriltuesday/eva-submission.git
ARG REPO_REF=7d535fe

WORKDIR /opt


# install utility libs
RUN apt update  \
    && apt install -y curl wget samtools bcftools tabix bedtools minimap2 rsync

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

RUN git clone ${REPO_URL} eva-submission && cd eva-submission && git checkout ${REPO_REF}

RUN cd eva-submission && python -m pip install .

# Install eva-sub-cli
RUN git clone https://github.com/apriltuesday/eva-sub-cli.git eva-sub-cli && cd eva-sub-cli && git checkout 5de8f00 && python -m pip install . && cd ..

RUN mkdir -p /opt/ftp/private/eva-box-01/upload/username

# Copy the config files
COPY eva_submission/submission_config.yml /root/.submission_config.yml
COPY maven-settings.xml /root/maven-settings.xml
