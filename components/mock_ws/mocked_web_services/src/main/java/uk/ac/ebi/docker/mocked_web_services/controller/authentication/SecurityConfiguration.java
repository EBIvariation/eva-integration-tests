package uk.ac.ebi.docker.mocked_web_services.controller.authentication;

import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.context.annotation.Bean;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfiguration {
    public static final String REALM = "EBI-DOCKER-REALM";
    private static final String ROLE_ADMIN = "ADMIN";
    private final CustomBasicAuthenticationEntryPoint customBasicAuthenticationEntryPoint;
    private String USERNAME_ADMIN = "mocked_web_services_user";
    private String PASSWORD_ADMIN = "mocked_web_services_pass";

    public SecurityConfiguration(CustomBasicAuthenticationEntryPoint customBasicAuthenticationEntryPoint) {
        this.customBasicAuthenticationEntryPoint = customBasicAuthenticationEntryPoint;
    }

    @Bean
    public UserDetailsService userDetailsService() {
        return new InMemoryUserDetailsManager(
            User.withUsername(USERNAME_ADMIN)
                .password("{noop}" + PASSWORD_ADMIN)
                .roles(ROLE_ADMIN)
                .build()
        );
    }

     @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    // CSRF disabled intentionally — stateless REST API uses Basic Auth with no session cookies, so CSRF is not applicable
        http.csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth.anyRequest().permitAll())
            .httpBasic(basic -> basic.realmName(REALM).authenticationEntryPoint(customBasicAuthenticationEntryPoint))
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS));
        return http.build();
    }
}
