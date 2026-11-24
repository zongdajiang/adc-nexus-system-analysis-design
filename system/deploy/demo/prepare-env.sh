#!/bin/sh
set -eu
cd "$(dirname "$0")"

domain=${1:-}
case "$domain" in
    ""|.*|*.|*..*|*[!A-Za-z0-9.-]*)
        printf '%s\n' 'Usage: sh prepare-env.sh demo.example.com' >&2
        exit 2 ;;
    *[A-Za-z]*.*|*.*[A-Za-z]*) ;;
    *)
        printf '%s\n' 'Use a DNS hostname for the HTTPS endpoint.' >&2
        exit 2 ;;
esac
if [ -e .env ]; then
    printf '%s\n' 'Existing .env kept. It contains the credentials for the configured instance.' >&2
    exit 1
fi

postgres_password=$(openssl rand -hex 24)
application_password=$(openssl rand -hex 24)
owner_password=$(openssl rand -hex 24)
umask 077
set -C
{
    printf 'ADC_DOMAIN=%s\n' "$domain"
    printf 'ADC_POSTGRES_PASSWORD=%s\n' "$postgres_password"
    printf 'ADC_DB_PASSWORD=%s\n' "$application_password"
    printf 'ADC_ADMIN_PASSWORD=%s\n' "$owner_password"
} > .env
printf '%s\n' 'Created private .env (mode 600).'
