FROM tomcat:9.0-jdk11

RUN apt update  \
    && apt install -y git maven

COPY maven-settings.xml /root

WORKDIR /usr/local/software

# make manager app available
RUN cp -avT /usr/local/tomcat/webapps.dist/manager /usr/local/tomcat/webapps/manager

# deploy contig alias
RUN git clone https://github.com/EBIvariation/contig-alias.git
RUN mvn package -s /root/maven-settings.xml -f contig-alias/pom.xml -P docker -DskipTests
RUN cp contig-alias/target/contig-alias-*.war.original /usr/local/tomcat/webapps/contig-alias.war

EXPOSE 8080

CMD ["catalina.sh", "run"]


