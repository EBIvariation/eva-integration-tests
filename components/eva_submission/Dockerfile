FROM ubuntu:22.04

ARG SOURCE_GITHUB_REPOSITORY
ARG SOURCE_GITHUB_REF
ARG SOURCE_GITHUB_SHA

ENV vcf_validator_version=0.9.4
ENV NXF_VER=21.10.5
ENV MONGOSH_VERSION=2.7.0


WORKDIR /opt

# install utility libs
RUN apt update  \
    && apt -qq install -y tar zip unzip curl wget samtools bcftools tabix bedtools minimap2 rsync git build-essential

# Install JAVA 8 and Node
RUN apt update && apt -qq install -y openjdk-8-jdk nodejs npm \
    && ARCH=$(dpkg --print-architecture) \
    && update-alternatives --install /usr/bin/java java /usr/lib/jvm/java-8-openjdk-${ARCH}/bin/java 1 \
    && update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-8-openjdk-${ARCH}/bin/javac 1 \
    && update-alternatives --set java /usr/lib/jvm/java-8-openjdk-${ARCH}/bin/java \
    && update-alternatives --set javac /usr/lib/jvm/java-8-openjdk-${ARCH}/bin/javac \
    && ln -sf /usr/lib/jvm/java-8-openjdk-${ARCH} /usr/lib/jvm/java-8-openjdk

ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk
ENV PATH="$JAVA_HOME/bin:$PATH"

# Install Maven
RUN apt update && apt -qq install -y maven

# install Python
RUN apt update && apt -qq install -y python3.10 python3-pip python3.10-dev \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip

# install mongosh
RUN apt update && apt install -y xz-utils ca-certificates && rm -rf /var/lib/apt/lists/* && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "aarch64" ]; then export MONGOSH_ARCH=linux-arm64; else export MONGOSH_ARCH=linux-x64; fi && \
    curl -L https://downloads.mongodb.com/compass/mongosh-${MONGOSH_VERSION}-${MONGOSH_ARCH}.tgz | tar -xz -C /usr/local/ && \
    mv /usr/local/mongosh-${MONGOSH_VERSION}-${MONGOSH_ARCH}/bin/mongosh /usr/local/bin/ && \
    rm -rf /usr/local/mongosh-${MONGOSH_VERSION}-${MONGOSH_ARCH}

# Install VCF validator
RUN curl -LJo /usr/local/bin/vcf_validator  https://github.com/EBIvariation/vcf-validator/releases/download/v${vcf_validator_version}/vcf_validator_linux \
    && curl -LJo /usr/local/bin/vcf_assembly_checker  https://github.com/EBIvariation/vcf-validator/releases/download/v${vcf_validator_version}/vcf_assembly_checker_linux \
    && chmod 755 /usr/local/bin/vcf_assembly_checker /usr/local/bin/vcf_validator

# Install biovalidator and make it executable
RUN pip3 install gyp-next \
    && git clone https://github.com/elixir-europe/biovalidator.git  \
    && cd biovalidator  \
    && npm install \
    && npm link

# Install nextflow
RUN curl -L "https://github.com/nextflow-io/nextflow/releases/download/v${NXF_VER}/nextflow-${NXF_VER}-all" | bash \
    && mv nextflow /usr/local/bin/


# Install eva-sub-cli
RUN git clone https://github.com/EBIvariation/eva-sub-cli.git eva-sub-cli && cd eva-sub-cli && python -m pip -q install . && cd ..

RUN mkdir -p /opt/ftp/private/eva-box-01/upload/username

# Copy the config files
RUN mkdir -p /root/.nextflow
COPY eva_submission/nextflow.config /root/.nextflow/config
COPY eva_submission/submission_config.yml /root/.submission_config.yml
COPY maven-settings.xml /root/maven-settings.xml
COPY eva_submission/install_repo.sh /opt/
COPY mongo_db/mongo_admin_prod_pass /root/.mongo_admin_prod_pass

ENV SOURCE_GITHUB_REPOSITORY $SOURCE_GITHUB_REPOSITORY
ENV SOURCE_GITHUB_REF $SOURCE_GITHUB_REF
ENV SOURCE_GITHUB_SHA $SOURCE_GITHUB_SHA

# Run the installation of the repository
RUN ./install_repo.sh


WORKDIR /usr/local/software

# setup eva-accession
RUN git clone --single-branch https://github.com/EBIvariation/eva-accession.git
RUN mvn package -s /root/maven-settings.xml -f eva-accession/pom.xml -DskipTests -P docker
RUN cp eva-accession/eva-accession-pipeline/target/eva-accession-pipeline-*-exec.jar /usr/local/software/eva-accession-pipeline.jar
RUN cp eva-accession/eva-accession-clustering/target/eva-accession-clustering-*-exec.jar /usr/local/software/eva-accession-clustering.jar
RUN cp eva-accession/eva-remapping-get-source/target/eva-remapping-get-source-*-exec.jar /usr/local/software/eva-remapping-get-source.jar
RUN cp eva-accession/eva-remapping-ingest/target/eva-remapping-ingest-*-exec.jar /usr/local/software/eva-remapping-ingest.jar

# setup eva-pipeline
RUN git clone --single-branch https://github.com/EBIvariation/eva-pipeline.git
RUN mvn package -s /root/maven-settings.xml -f eva-pipeline/pom.xml -DskipTests -P docker
RUN cp eva-pipeline/target/eva-pipeline-*-exec.jar /usr/local/software/eva-pipeline.jar

# install VEP
WORKDIR /usr/local/software/vep

# install dependencies for vep
RUN apt update && apt install -y libdbi-perl libdbd-mysql-perl libbz2-dev liblzma-dev libxml-libxml-perl libcurl4-openssl-dev libmodule-build-perl zlib1g-dev
# install htslib
RUN wget https://github.com/samtools/htslib/releases/download/1.14/htslib-1.14.tar.bz2 -P /usr/bin
RUN tar -vxjf /usr/bin/htslib-1.14.tar.bz2 -C /usr/bin
RUN make -C /usr/bin/htslib-1.14/

ENV HTSLIB_DIR=/usr/bin/htslib-1.14
ENV PATH="${PATH}:${HTSLIB_DIR}"
ENV PERL_MM_USE_DEFAULT=1

# install vep
RUN git clone https://github.com/Ensembl/ensembl-vep.git
RUN cd ensembl-vep && perl INSTALL.pl

WORKDIR /opt

CMD tail -f /dev/null
