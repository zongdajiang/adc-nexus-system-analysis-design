#!/bin/sh
set -eu
: "${ADC_DB_PASSWORD:?missing app database password}"

psql --username "$POSTGRES_USER" --dbname postgres --no-psqlrc --set ON_ERROR_STOP=1 <<'SQL'
\getenv app_password ADC_DB_PASSWORD
CREATE ROLE adc_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'app_password';
CREATE DATABASE adc_demo OWNER adc_app;
REVOKE CONNECT ON DATABASE adc_demo FROM PUBLIC;
SQL
