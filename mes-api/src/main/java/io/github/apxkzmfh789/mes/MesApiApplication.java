package io.github.apxkzmfh789.mes;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class MesApiApplication {

	public static void main(String[] args) {
		SpringApplication.run(MesApiApplication.class, args);
	}

}
