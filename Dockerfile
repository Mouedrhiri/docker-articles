FROM php:8.2-apache AS extensions
RUN docker-php-ext-install -j"$(nproc)" mysqli pdo_mysql

FROM php:8.2-apache AS runtime
COPY --from=extensions /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=extensions /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini" \
    && sed -i 's/Listen 80/Listen 8080/' /etc/apache2/ports.conf \
    && sed -i 's/:80>/:8080>/' /etc/apache2/sites-available/000-default.conf \
    && printf 'ServerName localhost\nServerTokens Prod\nServerSignature Off\n' > /etc/apache2/conf-available/security.conf \
    && printf 'expose_php=Off\nsession.save_path=/tmp\nsession.cookie_httponly=1\nsession.cookie_samesite=Lax\n' > /usr/local/etc/php/conf.d/security.ini \
    && chown -R www-data:www-data /var/run/apache2 /var/lock/apache2
WORKDIR /var/www/html
COPY --chown=root:root sources/app/ ./
USER www-data
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl --fail --silent --show-error http://127.0.0.1:8080/health.php
CMD ["apache2-foreground"]
