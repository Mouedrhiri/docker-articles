"""Génération du rapport : python scripts/make_report.py (reportlab requis)."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Table, TableStyle

root = Path(__file__).resolve().parents[1]
out = root / 'docs'
out.mkdir(exist_ok=True)
styles = getSampleStyleSheet()
styles['BodyText'].leading = 14
styles['BodyText'].spaceAfter = 9
story = []
def title(text): story.append(Paragraph(escape(text), styles['Heading1']))
def sub(text): story.append(Paragraph(escape(text), styles['Heading2']))
def p(text): story.append(Paragraph(escape(text), styles['BodyText']))
def page(): story.append(PageBreak())

title("Conteneurisation d'une application Web multi-tiers")
p('Projet M2 — Docker / Ynov — 16 novembre 2026')
p("Dans ce projet, j'ai conteneurisé l'application Articles avec PHP 8.2, Apache et MariaDB 11.4. Mon objectif était de séparer l'application de sa base de données, de conserver les articles entre les redémarrages et de préparer une chaîne de construction, de test et de publication des images.")
sub('1. Analyse et architecture')
p("J'ai commencé par analyser les sources PHP et le script SQL fournis. L'application permet de publier et de consulter des articles. La connexion initiale utilisait localhost et des identifiants fixes. J'ai remplacé cette configuration par des paramètres d'environnement et des secrets fichiers. Depuis le conteneur Web, j'utilise le nom DNS db pour joindre MariaDB.")
p("J'ai retenu deux services : web pour Apache, l'interface et le traitement PHP ; db pour MariaDB. Ce découpage conserve la structure de l'application fournie tout en isolant les données du serveur Web.")
data = [['Navigateur : http://localhost:8080'], ['HTTP : port hôte 8080 vers port conteneur 8080'], ['web : Apache + PHP 8.2 / www-data (UID 33)'], ['Réseau bridge app-network / PDO vers db:3306'], ['db : MariaDB 11.4 / base articles / compte articles_app'], ['Volume persistant db-data : /var/lib/mysql']]
t = Table(data, colWidths=[16*cm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#edf5f2')),('BOX',(0,0),(-1,-1),1,colors.HexColor('#236a60')),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
story.append(t)
p("J'ai publié uniquement le port Web sur 127.0.0.1. La base ne possède aucun port publié sur l'hôte. Les deux services communiquent sur le bridge personnalisé app-network et les secrets sont montés sous /run/secrets.")
page()

title('Construction et orchestration')
sub('2. Mon Dockerfile Web')
p("J'utilise FROM php:8.2-apache AS extensions pour disposer de la base officielle et compiler mysqli et pdo_mysql avec RUN docker-php-ext-install. Une seconde étape FROM, nommée runtime, récupère les modules et leurs fichiers d'activation avec COPY --from. Cette séparation évite de recopier les résidus de compilation, même si l'image de base conserve certains outils.")
p("Dans RUN, j'active php.ini-production, je masque les versions PHP et Apache et je configure les sessions. Je fais écouter Apache sur 8080 : ce port permet l'exécution sans root sans ajouter de capacité réseau privilégiée. Je conserve ainsi l'accès demandé sur localhost:8080.")
p("WORKDIR fixe /var/www/html. COPY copie seulement les sources applicatives avec root comme propriétaire. USER www-data lance Apache sans root. EXPOSE documente le port 8080. CMD apache2-foreground garde le serveur au premier plan. HEALTHCHECK utilise curl pour vérifier une route HTTP qui effectue aussi une requête SQL.")
p("Je n'installe aucun paquet apt supplémentaire. Je limite le contexte de construction aux sources utiles avec .dockerignore, ce qui exclut notamment les secrets, les archives, les rapports et l'historique Git.")
sub('3. Mon Dockerfile MariaDB')
p("J'utilise FROM mariadb:11.4 et COPY pour placer articles.sql dans /docker-entrypoint-initdb.d. L'entrypoint officiel crée la base et le compte applicatif à partir des paramètres MARIADB_DATABASE et MARIADB_USER. Le script initialise ensuite la table articles au premier démarrage sur un volume vide. Le HEALTHCHECK utilise healthcheck.sh --connect --innodb_initialized.")
p("Je conserve l'entrypoint officiel : il prépare les permissions du volume puis lance le serveur MariaDB sous son utilisateur dédié. Je ne force donc pas un USER qui empêcherait cette préparation.")
sub('4. Mon fichier Docker Compose')
p("Dans services, je déclare web et db, leurs contextes build et leurs noms image. environment transmet les paramètres de connexion et les chemins des secrets. secrets autorise chaque service à lire les fichiers nécessaires. ports publie uniquement le Web et depends_on avec service_healthy attend que la base soit prête.")
p("J'ai ajouté les healthchecks dans Compose pour leur utilisation avec Podman comme avec Docker. restart: unless-stopped gère les redémarrages, networks définit le bridge et volumes déclare db-data pour conserver les données en dehors des conteneurs.")
page()

title('Sécurité, réseau et persistance')
sub('5. Mes choix de sécurité')
p("J'exécute le Web avec www-data, read_only: true, cap_drop: ALL et no-new-privileges. Les fichiers temporaires PHP et Apache sont placés dans un tmpfs sous /tmp. Son mode 1777 correspond au fonctionnement habituel d'un répertoire temporaire avec sticky bit. Je n'applique aucun chmod 777 au code ni aux données : il permettrait à tous les utilisateurs de les modifier.")
p("J'ai prévu scripts/setup.py pour générer deux mots de passe aléatoires sans remplacer les secrets existants. Ces fichiers sont exclus de Git, du contexte Docker et du ZIP. Compose les monte en lecture seule. Ils ne sont pas chiffrés au repos : je dois donc aussi protéger l'accès au dossier hôte. Le compte applicatif est distinct de root et limité à sa base.")
p("J'ai conservé les requêtes préparées PDO et ajouté utf8mb4, la validation des types et des longueurs, les jetons CSRF et l'échappement HTML. Les erreurs détaillées sont envoyées dans les logs. Les cookies de session utilisent HttpOnly et SameSite. Pour un déploiement sur Internet, je prévoirais également HTTPS et les contrôles d'accès adaptés.")
sub('6. Communication entre les services')
p("Le service web résout db grâce au DNS du réseau Compose. Le healthcheck vérifie le parcours HTTP, PHP puis SQL. Pour un contrôle réseau isolé, je peux vérifier la résolution avec getent hosts db et ouvrir une connexion TCP sur db:3306. Je n'utilise pas curl http://db:3306 car MySQL ne parle pas HTTP.")
sub('7. Vérification de la persistance')
p("J'ai ajouté un article portant un marqueur unique, exécuté docker compose down puis recréé les conteneurs. Le test a retrouvé le même article : le volume db-data conserve donc les données. Je réserve down -v à une réinitialisation volontaire, car cette commande supprime le volume.")
p("Les paramètres d'initialisation MariaDB ne sont appliqués que sur un volume vide. Pour changer le mot de passe d'un compte déjà créé, je dois effectuer une rotation SQL coordonnée ; modifier seulement le fichier secret ne suffit pas.")
page()

title('Optimisation et analyse de vulnérabilités')
sub('8. Mesure des images')
p("J'ai relevé les tailles locales non compressées sur linux/amd64 avec podman image inspect : 509 332 368 octets pour php:8.2-apache, 509 645 356 octets pour l'image Web initialement testée et 340 532 266 octets pour l'image MariaDB initialement testée. Le surcoût Web mesuré est de 312 988 octets, soit environ 0,06 %.")
p("Cette mesure compare la base PHP à mon image applicative ; elle ne représente pas un avant/après d'une ancienne image monolithique, puisqu'aucune image de ce type n'était fournie. Mon optimisation porte sur le contexte de construction, l'isolation de la compilation et l'absence de dépendances supplémentaires inutiles. Pour rendre une livraison strictement reproductible, je figerais également les digests des bases après vérification.")
sub('9. Analyse Trivy')
summary_file = out / 'trivy-summary.json'
if summary_file.exists():
    summary = json.loads(summary_file.read_text(encoding='utf-8'))
    p("J'ai exécuté Trivy sur les deux images publiées sur Docker Hub. J'ai utilisé le scanner de vulnérabilités avec le filtre HIGH,CRITICAL. Les rapports JSON complets sont inclus dans docs/trivy-web.json et docs/trivy-db.json.")
    for name, result in summary.items():
        p(f"Image {name} : {result['high']} vulnérabilité(s) HIGH et {result['critical']} CRITICAL détectée(s), dont {result['fixable_critical']} critique(s) disposant d'une version corrigée. Résultat du seuil utilisé en CI (aucune critique corrigeable) : {result['gate']}.")
    p("Ces résultats correspondent aux images et à la base de vulnérabilités utilisées au moment du scan. Je prévois de reconstruire les images avec les correctifs disponibles puis de relancer l'analyse avant une nouvelle livraison. La réussite technique du scan ne signifie pas automatiquement l'absence de vulnérabilité.")
else:
    p("J'ai prévu l'analyse des images avec Trivy dans le pipeline. Le résultat local est à compléter à partir des rapports de scan avant de conclure sur les vulnérabilités détectées.")
p("Dans le workflow, j'ai configuré un blocage sur les vulnérabilités CRITICAL disposant d'un correctif. Les vulnérabilités sans correctif restent à examiner ; ce seuil ne remplace donc pas la lecture du rapport complet.")
page()

title('CI/CD, publication et bilan')
sub('10. Mon pipeline GitHub Actions')
p("J'ai préparé un workflow déclenché sur push main/master, pull_request ou lancement manuel. Il construit les deux images, vérifie la syntaxe PHP, démarre la stack, exécute les tests HTTP et contrôle la persistance après recréation des conteneurs. Il lance ensuite Trivy sur les deux images. Les logs sont affichés et les ressources de test sont nettoyées même en cas d'échec.")
p("J'ai séparé la publication dans un job dépendant du succès des tests. Ce job n'est pas lancé sur une pull request. Il utilise DOCKERHUB_USERNAME et DOCKERHUB_TOKEN dans les secrets GitHub, puis publie latest et le SHA complet du commit. La création du dépôt GitHub distant, la configuration de ces secrets et une première exécution distante restent à effectuer.")
sub('11. Publication Docker Hub')
p("J'ai publié les deux images sur mon compte mouedrhi492 : mouedrhi492/ynov-articles-web et mouedrhi492/ynov-articles-db. Les tags disponibles sont latest et 8d39914b870aee697761d49b1a947eefedbd5786. J'ai vérifié leur accessibilité publique ; les digests sont enregistrés dans docs/publication.json. Cette publication a été réalisée manuellement avec Podman.")
sub('12. Bilan des vérifications')
p("J'ai validé la construction des deux images, la configuration Compose et la syntaxe des quatre fichiers PHP. Les tests HTTP passent pour la santé, la lecture, la création, les champs obligatoires, la longueur, le refus des méthodes non autorisées, le CSRF et l'échappement XSS. J'ai également contrôlé l'utilisateur www-data et la conservation de l'article après recréation des conteneurs.")
p("Pour ma démonstration, je présente l'architecture, je lance la stack, je publie un article puis je recrée les conteneurs pour montrer la persistance. Je termine avec les protections Docker, le résultat Trivy et la structure du pipeline. Les commandes de reproduction sont regroupées dans README.md.")
sub('Références officielles')
for url in ['https://hub.docker.com/_/php','https://hub.docker.com/_/mariadb','https://docs.docker.com/compose/how-tos/use-secrets/','https://docs.docker.com/compose/']:
    p(url)
def footer(canvas, doc):
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2*cm, 1.25*cm, 'Projet Docker Ynov — Rapport technique')
    canvas.drawRightString(19*cm, 1.25*cm, str(doc.page))
SimpleDocTemplate(str(out / 'Rapport-technique.pdf'), rightMargin=2*cm, leftMargin=2*cm, topMargin=1.7*cm, bottomMargin=1.8*cm).build(story, onFirstPage=footer, onLaterPages=footer)
print('Rapport créé : docs/Rapport-technique.pdf')
