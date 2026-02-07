FROM eclipse-temurin:21-jre

WORKDIR /work

COPY freerouting-2.1.0.jar /freerouting.jar

ENTRYPOINT ["java", "-jar", "/freerouting.jar"]
