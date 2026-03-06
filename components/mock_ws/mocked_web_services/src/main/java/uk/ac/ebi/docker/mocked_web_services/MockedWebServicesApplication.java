package uk.ac.ebi.docker.mocked_web_services;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.servlet.support.SpringBootServletInitializer;

@SpringBootApplication
public class MockedWebServicesApplication extends SpringBootServletInitializer {

    public static void main(String[] args) {
        SpringApplication.run(MockedWebServicesApplication.class, args);
    }

    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder application) {
        return application.sources(MockedWebServicesApplication.class);
    }

}
