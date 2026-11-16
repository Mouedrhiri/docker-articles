<?php
declare(strict_types=1);
require __DIR__ . '/db-config.php';
startSession();
header('X-Content-Type-Options: nosniff');
header("Content-Security-Policy: default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'");
header('Cache-Control: no-store');
$error = null; $articles = [];
try { $articles = database()->query('SELECT * FROM articles ORDER BY id DESC')->fetchAll(); }
catch (Throwable $e) { error_log($e->getMessage()); http_response_code(503); $error = 'La base de donnees est temporairement indisponible.'; }
?>
<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Articles - Projet Docker Ynov</title><link rel="stylesheet" href="style.css"></head>
<body><header><div class="container"><span class="badge">YNOV / PROJET DOCKER</span><h1>Le journal des articles</h1><p>Une application PHP et MariaDB, orchestree avec Docker Compose.</p></div></header>
<main class="container grid"><section class="panel"><h2>Nouvel article</h2><p class="muted">Partagez une idee avec votre equipe.</p>
<?php if (isset($_GET['created'])): ?><p class="success" role="status">Article enregistre.</p><?php endif; ?>
<?php if ($error): ?><p class="error" role="alert"><?= escape($error) ?></p><?php endif; ?>
<form action="validation.php" method="post"><input type="hidden" name="csrf" value="<?= escape($_SESSION['csrf']) ?>">
<label for="title">Titre</label><input id="title" name="title" maxlength="100" required placeholder="Le titre de votre article">
<label for="author">Auteur</label><input id="author" name="author" maxlength="100" required placeholder="Votre nom">
<label for="content">Contenu</label><textarea id="content" name="content" rows="7" maxlength="10000" required placeholder="Votre texte..."></textarea><button type="submit">Publier l'article</button></form></section>
<section><div class="list-heading"><h2>Dernieres publications</h2><span><?= count($articles) ?> article(s)</span></div>
<?php if (!$articles && !$error): ?><div class="panel"><h3>Le journal commence ici.</h3><p>Publiez votre premier article depuis le formulaire.</p></div><?php endif; ?>
<?php foreach ($articles as $article): ?><article class="panel article"><p class="muted"><?= escape($article['date']) ?></p><h3><?= escape($article['title']) ?></h3><p class="content"><?= nl2br(escape($article['content'])) ?></p><footer>Par <?= escape($article['author']) ?></footer></article><?php endforeach; ?>
</section></main><footer class="container bottom">Projet de conteneurisation / PHP 8.2 / Apache / MariaDB</footer></body></html>
