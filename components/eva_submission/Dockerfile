FROM python:3.10

ENV vcf_validator_version=0.9.4
ENV NXF_VER=23.10.0


WORKDIR /opt


# install utility libs
RUN apt update  \
    && apt -qq install -y curl wget samtools bcftools tabix bedtools minimap2 rsync

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


# Install eva-sub-cli
RUN git clone https://github.com/EBIvariation/eva-sub-cli.git

RUN mkdir -p /opt/ftp/private/eva-box-01/upload/username

# Copy the config files
COPY eva_submission/submission_config.yml /root/.submission_config.yml
COPY maven-settings.xml /root/maven-settings.xml
COPY eva_submission/install_repo.sh /opt/

CMD ["./install_repo.sh"]