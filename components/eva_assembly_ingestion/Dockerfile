FROM ubuntu:22.04

ARG SOURCE_GITHUB_REPOSITORY
ARG SOURCE_GITHUB_REF
ARG SOURCE_GITHUB_SHA

ENV NXF_VER=25.10.4


WORKDIR /opt

# install utility libs
RUN apt update  \
    && apt -qq install -y tar zip unzip curl wget samtools bcftools tabix bedtools minimap2 rsync git build-essential

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

# Install Maven
RUN apt update && apt -qq install -y maven

# install Python
RUN apt update && apt -qq install -y python3.10 python3-pip python3.10-dev python3.10-venv \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip

# Install nextflow
RUN curl -fsSL "https://github.com/nextflow-io/nextflow/releases/download/v${NXF_VER}/nextflow" -o /usr/local/bin/nextflow \
    && chmod +x /usr/local/bin/nextflow \
    && nextflow -version

# Install eva-submission
# TODO: revert after testing
RUN git clone --single-branch --branch java-21 https://github.com/EBIvariation/eva-submission.git eva-submission && cd eva-submission && python -m pip -q install . && cd ..

# Install variant-remapping (needs a virtual environment)
RUN git clone https://github.com/EBIvariation/variant-remapping.git variant-remapping \
    && cd variant-remapping \
    && python -m venv python \
    && python/bin/pip install -U pip \
    && python/bin/pip install -qr requirements.txt \
    && cd ..

# Copy the config files
RUN mkdir -p /root/.nextflow
COPY eva_assembly_ingestion/nextflow.config /root/.nextflow/config
COPY eva_assembly_ingestion/assembly_config.yml /root/.assembly_config.yml
COPY eva_assembly_ingestion/assembly_config.yml /root/.submission_config.yml
COPY maven-settings.xml /root/maven-settings.xml
COPY eva_assembly_ingestion/install_repo.sh /opt/

WORKDIR /usr/local/software

# Install eva-accession
RUN git clone --single-branch https://github.com/EBIvariation/eva-accession.git
RUN mvn package -s /root/maven-settings.xml -f eva-accession/pom.xml -DskipTests -P docker
RUN cp eva-accession/eva-accession-clustering/target/eva-accession-clustering-*-exec.jar /usr/local/software/eva-accession-clustering.jar
RUN cp eva-accession/eva-remapping-get-source/target/eva-remapping-get-source-*-exec.jar /usr/local/software/eva-remapping-get-source.jar
RUN cp eva-accession/eva-remapping-ingest/target/eva-remapping-ingest-*-exec.jar /usr/local/software/eva-remapping-ingest.jar

WORKDIR /opt
ENV SOURCE_GITHUB_REPOSITORY=$SOURCE_GITHUB_REPOSITORY
ENV SOURCE_GITHUB_REF=$SOURCE_GITHUB_REF
ENV SOURCE_GITHUB_SHA=$SOURCE_GITHUB_SHA

# Run the installation of the repository
RUN ./install_repo.sh

CMD tail -f /dev/null
