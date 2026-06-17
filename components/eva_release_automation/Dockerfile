FROM ubuntu:22.04

ARG SOURCE_GITHUB_REPOSITORY=EBIvariation/eva-release-automation
ARG SOURCE_GITHUB_REF=main
ARG SOURCE_GITHUB_SHA

ENV NXF_VER=25.10.4
ENV VCF_VALIDATOR_VERSION=0.9.4
ENV CONTIG_NAME_CONVERTER_VERSION=0.0.2

# install utility libs, python and java
RUN apt update
RUN apt-get install -y curl wget maven git bcftools

# install Python
RUN apt update && apt -qq install -y python3.10 python3-pip python3.10-dev \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip

# Install JAVA 21
RUN apt update && apt -qq install -y wget apt-transport-https gnupg \
    && wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor -o /usr/share/keyrings/adoptium.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb bookworm main" > /etc/apt/sources.list.d/adoptium.list \
    && apt update && apt -qq install -y temurin-21-jdk \
    && ARCH=$(dpkg --print-architecture) \
    && update-alternatives --install /usr/bin/java java /usr/lib/jvm/temurin-21-jdk-${ARCH}/bin/java 1 \
    && update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/temurin-21-jdk-${ARCH}/bin/javac 1 \
    && update-alternatives --set java /usr/lib/jvm/temurin-21-jdk-${ARCH}/bin/java \
    && update-alternatives --set javac /usr/lib/jvm/temurin-21-jdk-${ARCH}/bin/javac \
    && ln -sf /usr/lib/jvm/temurin-21-jdk-${ARCH} /usr/lib/jvm/temurin-21-jdk

ENV JAVA_HOME=/usr/lib/jvm/temurin-21-jdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# install nextflow
RUN curl -fsSL "https://github.com/nextflow-io/nextflow/releases/download/v${NXF_VER}/nextflow" -o /usr/local/bin/nextflow \
    && chmod +x /usr/local/bin/nextflow \
    && nextflow -version

RUN mkdir /usr/local/software/

# install vcf_validator
RUN curl -LJo /usr/local/bin/vcf_validator https://github.com/EBIvariation/vcf-validator/releases/download/v${VCF_VALIDATOR_VERSION}/vcf_validator_linux \
    && chmod 755 /usr/local/bin/vcf_validator

# install vcf_assembly_checker
RUN curl -LJo /usr/local/bin/vcf_assembly_checker https://github.com/EBIvariation/vcf-validator/releases/download/v${VCF_VALIDATOR_VERSION}/vcf_assembly_checker_linux \
    && chmod 755 /usr/local/bin/vcf_assembly_checker

# Install contig_name_converter
RUN pip install -q "git+https://github.com/EBIvariation/contig_name_converter.git@${CONTIG_NAME_CONVERTER_VERSION}"

COPY maven-settings.xml /root/maven.xml
COPY eva_release_automation/release_config.yml /root/.release_config.yml
COPY eva_release_automation/nextflow.config /root/.nextflow/config
COPY eva_release_automation/install_repo.sh /opt/

# Setup release pipeline
WORKDIR /usr/local/software
RUN git clone --single-branch https://github.com/EBIvariation/eva-accession.git
RUN mvn package -s /root/maven.xml -f eva-accession/pom.xml -DskipTests -P docker
RUN cp eva-accession/eva-accession-release/target/eva-accession-release-*-exec.jar /usr/local/software/eva-accession-release.jar

WORKDIR /opt
# Install eva-release-automation
RUN ./install_repo.sh

CMD tail -f /dev/null