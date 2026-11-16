<?php
declare(strict_types=1);
require __DIR__ . '/db-config.php';
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { header('Allow: POST'); http_response_code(405); exit('Methode non autorisee.'); }
startSession();
if (!is_string($_POST['csrf'] ?? null) || !hash_equals($_SESSION['csrf'], $_POST['csrf'])) { http_response_code(403); exit('Formulaire expire. Revenez a l accueil.'); }
$values = [];
foreach (['title' => 100, 'author' => 100, 'content' => 10000] as $field => $limit) {
    $value = $_POST[$field] ?? null;
    if (!is_string($value) || trim($value) === '' || preg_match('//u', $value) !== 1 || preg_match_all('/./us', $value) > $limit) { http_response_code(422); exit('Champs obligatoires. Titre et auteur : 100 caracteres ; contenu : 10000.'); }
    $values[$field] = trim($value);
}
try {
    $statement = database()->prepare('INSERT INTO articles (title, author, content) VALUES (:title, :author, :content)');
    $statement->execute($values);
    header('Location: /index.php?created=1', true, 303); exit;
} catch (Throwable $e) { error_log($e->getMessage()); http_response_code(503); exit('Enregistrement indisponible.'); }
