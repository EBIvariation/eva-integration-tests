FROM tomcat:9.0-jdk11

RUN apt update && apt -qq install -y git maven

COPY maven-settings.xml /root

# make manager app available
COPY tomcat-users.xml /usr/local/tomcat/conf/
RUN cp -avT /usr/local/tomcat/webapps.dist/manager /usr/local/tomcat/webapps/manager \
 && sed -i 's|<Valve className="org.apache.catalina.valves.RemoteAddrValve".*|<!-- Removed RemoteAddrValve for all IP access -->|' /usr/local/tomcat/webapps/manager/META-INF/context.xml

WORKDIR /usr/local/software

# deploy eva-submission-ws
RUN git clone https://github.com/EBIvariation/eva-submission-ws.git
RUN mvn package -s /root/maven-settings.xml -f eva-submission-ws/pom.xml -P docker -DskipTests
RUN cp eva-submission-ws/target/eva-submission-ws-*.war.original /usr/local/tomcat/webapps/eva#webservices#submission-ws.war

EXPOSE 8080

CMD ["catalina.sh", "run"]


