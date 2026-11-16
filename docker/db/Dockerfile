FROM mariadb:11.4
COPY sources/db/articles.sql /docker-entrypoint-initdb.d/01-articles.sql
HEALTHCHECK --interval=10s --timeout=5s --start-period=40s --retries=10 \
    CMD healthcheck.sh --connect --innodb_initialized
