FROM maven:3.9.11-eclipse-temurin-21 AS build
WORKDIR /build
COPY pom.xml ./
COPY src ./src
RUN mvn -B -ntp -DskipTests package

FROM eclipse-temurin:21-jre-jammy
RUN groupadd --gid 10001 adc && useradd --uid 10001 --gid adc --create-home adc
WORKDIR /app
COPY --from=build --chown=adc:adc /build/target/adc-nexus.jar ./adc-nexus.jar
USER adc
ENV APP_ENV=PRODUCTION SEED_DATA=false DEMO_MODE=false TZ=Asia/Shanghai PORT=10000 BIND_ADDRESS=0.0.0.0 DATA_DIR=/tmp/adc-nexus
EXPOSE 10000
ENTRYPOINT ["java", "-Xms64m", "-Xmx320m", "-XX:MaxMetaspaceSize=96m", "-Dfile.encoding=UTF-8", "-Duser.timezone=Asia/Shanghai", "-jar", "adc-nexus.jar"]
