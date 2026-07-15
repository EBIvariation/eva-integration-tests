FROM eclipse-temurin:11-jdk

ARG TOMCAT_VERSION=9.0.120

RUN apt-get update \
    && apt-get install -y --no-install-recommends git maven curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://archive.apache.org/dist/tomcat/tomcat-9/v${TOMCAT_VERSION}/bin/apache-tomcat-${TOMCAT_VERSION}.tar.gz" -o /tmp/tomcat.tar.gz \
    && mkdir -p /usr/local/tomcat \
    && tar xzf /tmp/tomcat.tar.gz -C /usr/local/tomcat --strip-components=1 \
    && rm /tmp/tomcat.tar.gz

COPY maven-settings.xml /root

WORKDIR /usr/local/software

# deploy contig alias
RUN git clone https://github.com/EBIvariation/contig-alias.git
RUN mvn package -s /root/maven-settings.xml -f contig-alias/pom.xml -P docker -DskipTests
RUN cp contig-alias/target/contig-alias-*.war.original /usr/local/tomcat/webapps/contig-alias.war

EXPOSE 8080

CMD ["/usr/local/tomcat/bin/catalina.sh", "run"]
