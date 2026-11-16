<?php
declare(strict_types=1);
require __DIR__ . '/db-config.php';
header('Content-Type: text/plain; charset=utf-8');
try { database()->query('SELECT id FROM articles LIMIT 1'); echo 'OK'; }
catch (Throwable $e) { error_log($e->getMessage()); http_response_code(503); echo 'UNAVAILABLE'; }
