<?php
declare(strict_types=1);
function database(): PDO {
    $password = @file_get_contents(getenv('DB_PASSWORD_FILE') ?: '/run/secrets/db_password');
    if ($password === false || trim($password) === '') throw new RuntimeException('Secret absent.');
    return new PDO(sprintf('mysql:host=%s;dbname=%s;charset=utf8mb4', getenv('DB_HOST') ?: 'db', getenv('DB_NAME') ?: 'articles'), getenv('DB_USER') ?: 'articles_app', trim($password), [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC, PDO::ATTR_EMULATE_PREPARES => false]);
}
function escape(string $value): string { return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function startSession(): void {
    session_start(['cookie_httponly' => true, 'cookie_samesite' => 'Lax']);
    if (!isset($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32));
}
