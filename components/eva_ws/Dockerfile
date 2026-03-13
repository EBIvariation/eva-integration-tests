FROM tomcat:9.0-jdk11

RUN apt update && apt -qq install -y git maven

COPY maven-settings.xml /root

WORKDIR /usr/local/software

# deploy eva-ws (count_stats only for now)
RUN git clone https://github.com/EBIvariation/eva-ws.git
RUN mvn package -s /root/maven-settings.xml -f eva-ws/pom.xml -P docker -DskipTests
RUN cp eva-ws/count-stats/target/count-stats-*.war /usr/local/tomcat/webapps/count_stats.war

EXPOSE 8080

CMD ["catalina.sh", "run"]
