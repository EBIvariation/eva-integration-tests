FROM tomcat:9.0-jdk11

RUN apt update  \
    && apt install -y git maven

ADD mocked_web_services /usr/local/software/mocked_web_services

# make manager app available
COPY tomcat-users.xml /usr/local/tomcat/conf/
RUN cp -avT /usr/local/tomcat/webapps.dist/manager /usr/local/tomcat/webapps/manager \
 && sed -i 's|<Valve className="org.apache.catalina.valves.RemoteAddrValve".*|<!-- Removed RemoteAddrValve for all IP access -->|' /usr/local/tomcat/webapps/manager/META-INF/context.xml

WORKDIR /usr/local/software

# build and deploy mocked web-services
RUN mvn package -f mocked_web_services/pom.xml
RUN cp mocked_web_services/target/mocked_web_services-*.war.original /usr/local/tomcat/webapps/mocked_web_services.war

EXPOSE 8080

CMD ["catalina.sh", "run"]


