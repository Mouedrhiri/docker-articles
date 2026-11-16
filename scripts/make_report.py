"""Regeneration optionnelle : pip install reportlab ; python scripts/make_report.py."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

root = Path(__file__).resolve().parents[1]
out = root / 'docs'
out.mkdir(exist_ok=True)
styles = getSampleStyleSheet()
styles['BodyText'].spaceAfter = 10
styles['BodyText'].leading = 15
story = []
def title(text): story.append(Paragraph(escape(text), styles['Heading1']))
def sub(text): story.append(Paragraph(escape(text), styles['Heading2']))
def p(text): story.append(Paragraph(escape(text), styles['BodyText']))
def page(): story.append(PageBreak())

title('Conteneurisation d une application Web multi-tiers')
p('Projet M2 - Docker / Ynov - 16 novembre 2026')
p('Application Articles : PHP 8.2, Apache et MariaDB 11.4. Rapport technique accompagne du code source, des Dockerfiles, de Docker Compose, des tests HTTP et du pipeline GitHub Actions.')
sub('1. Analyse et architecture')
p('Les sources initiales comportent un formulaire, une liste d articles et un traitement PHP par requete preparee. La connexion utilisait localhost et des identifiants fixes ; le SQL creait un utilisateur limite a localhost. Dans des conteneurs distincts, localhost designe chaque conteneur : le Web doit joindre le nom de service db. La gestion du compte SQL est deleguee a l entrypoint MariaDB officiel.')
data = [[Paragraph('<b>Navigateur</b><br/>http://localhost:8080', styles['BodyText'])], ['HTTP via port publie 8080 -> 8080'], [Paragraph('<b>web : Apache / PHP 8.2</b><br/>Utilisateur www-data (UID 33)<br/>Formulaire + traitement backend PHP', styles['BodyText'])], ['PDO / TCP 3306 / DNS : db'], [Paragraph('<b>db : MariaDB 11.4</b><br/>Base articles / compte articles_app', styles['BodyText'])], ['Volume nomme db-data : /var/lib/mysql']]
t = Table(data, colWidths=[16*cm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#edf5f2')),('BOX',(0,0),(-1,-1),1,colors.HexColor('#236a60')),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)])); story.append(t)
p('Le bridge personnalise app-network relie web et db. Seul le port Web est publie, sur 127.0.0.1. La base n expose aucun port sur l hote. Les secrets sont montes en fichiers dans /run/secrets. Aucun service d administration optionnel n est ajoute.')
page()
title('Construction et orchestration')
sub('2. Dockerfile Web : justification des instructions')
for text in [
'FROM php:8.2-apache AS extensions : base officielle avec serveur Apache et environnement de compilation PHP. RUN docker-php-ext-install compile mysqli et pdo_mysql.',
'FROM php:8.2-apache AS runtime puis COPY --from : conserve les extensions compilees et leur activation sans les residus de compilation. La base commune conserve toutefois ses outils : ce choix ne permet pas de pretendre a une forte reduction de taille.',
'RUN : active php.ini-production, masque la version PHP et la signature Apache, configure les sessions et change l ecoute vers 8080. Aucun paquet apt additionnel ni cache supplementaire n est ajoute.',
'WORKDIR fixe /var/www/html ; COPY limite le contenu aux sources applicatives, proprietaire root, lisibles par www-data. Le code applicatif ne peut pas se modifier lui-meme.',
'USER www-data execute Apache sans root. EXPOSE 8080 documente le port interne ; CMD apache2-foreground garde le processus principal au premier plan. HEALTHCHECK interroge une route qui execute une requete SQL : il verifie le chemin HTTP + PHP + schema SQL.'
]: p(text)
sub('3. Dockerfile base de donnees')
p('FROM mariadb:11.4 selectionne la branche officielle. COPY place articles.sql dans /docker-entrypoint-initdb.d. Le script initialise la table dans MARIADB_DATABASE au premier demarrage. HEALTHCHECK utilise healthcheck.sh --connect --innodb_initialized fourni par l image. Le serveur MariaDB abandonne les privileges root apres preparation du volume par l entrypoint ; aucun USER force ne vient casser cette initialisation.')
sub('4. Sections Docker Compose')
p('services definit web et db avec build et image pour construction et publication. environment transmet les parametres non secrets et les chemins des fichiers secrets. secrets autorise explicitement les services a lire les fichiers necessaires. ports publie uniquement le Web. depends_on/service_healthy attend une base prete. healthcheck controle les deux services, y compris avec les builds OCI Podman. restart: unless-stopped assure la relance en cas d arret inattendu. networks cree le bridge personnalise. volumes conserve les donnees hors des couches ephemeres.')
p('Le port interne 8080 est un ecart volontaire au port 80 suggere dans le sujet : il permet une execution non-root sans capacite reseau privilegiee, tout en conservant l URL demandee localhost:8080.')
page()
title('Securite, reseau et optimisation')
sub('5. Mesures de securite')
p('Le Web utilise read_only: true, cap_drop: ALL et no-new-privileges. Un tmpfs /tmp fournit les fichiers temporaires PHP et les repertoires Apache configures sous /tmp/apache2. Son mode 1777 est le mode temporaire standard avec sticky bit : les utilisateurs ne peuvent pas supprimer les fichiers des autres. Aucun chmod 777 n est applique au code ou aux donnees.')
p('Les mots de passe sont generes aleatoirement par scripts/setup.py, preserves entre lancements et exclus de Git, du contexte Docker et du ZIP. Compose les monte en lecture seule. Les fichiers locaux ne sont pas chiffres au repos : leur protection depend aussi des permissions du dossier hote. Le compte applicatif est distinct de root et limite a sa base.')
p('L application utilise des requetes preparees PDO, utf8mb4, une validation serveur des types et longueurs, des jetons CSRF et un echappement HTML systematique. Les erreurs techniques vont dans les logs ; les utilisateurs recoivent des erreurs generiques. Les cookies sont HttpOnly/SameSite. Une mise en production exposant Internet doit ajouter HTTPS et les politiques d acces adaptees.')
sub('6. Communication et persistance')
p('Le DNS Compose resout db depuis web. Le controle TCP utilise fsockopen(db, 3306) ; le healthcheck PDO confirme une vraie operation SQL. curl http://db:3306 n est pas pertinent car MySQL ne parle pas HTTP. Le bridge limite la communication au reseau rejoint, sans constituer a lui seul un pare-feu applicatif entre les deux services.')
p('docker compose down retire les conteneurs et le reseau, mais conserve db-data. Le test de persistance cree un article marque, recree les conteneurs et retrouve exactement ce marqueur. down -v est reserve a une reinitialisation volontaire car il detruit les donnees. Les variables d initialisation ne modifient pas un compte SQL deja present dans le volume.')
sub('7. Mesure des images')
p('Mesures locales linux/amd64 avec podman image inspect, tailles non compressees : base php:8.2-apache = 509 332 368 octets ; Web final = 509 645 356 octets ; DB finale = 340 532 266 octets. Le surcout Web est de 312 988 octets, environ 0,06 %. Cette comparaison base/final n est pas une mesure avant/apres d une application monolithique : aucune telle image initiale n etait fournie. Aucun gain fictif n est annonce.')
p('Le multi-stage isole la compilation ; .dockerignore restreint le contexte aux sources utiles. Les tags recoivent des correctifs, mais restent mutables : figer les digests apres scan serait necessaire pour un deploiement strictement reproductible. Le pipeline Trivy bloque les critiques corrigeables ; un scan complet reste requis pour les vulnerabilites sans correctif.')
page()
title('Automatisation, validation et demonstration')
sub('8. Pipeline CI/CD et publication')
p('Le workflow GitHub Actions se declenche sur push main/master, pull_request ou lancement manuel. Il genere la configuration, valide Compose, construit les deux images, controle php -l, demarre les services, execute les tests HTTP puis recree les conteneurs pour prouver la persistance. Trivy analyse ensuite les images Web et DB. Les logs sont collectes et les ressources CI nettoyees meme en cas d echec.')
p('La publication depend du succes du job de test et ne se produit pas pour une PR. docker/login-action utilise les secrets GitHub DOCKERHUB_USERNAME et DOCKERHUB_TOKEN. docker/build-push-action publie les deux images avec latest et le SHA complet du commit. Creer les deux depots publics sur le compte personnel avant execution. Les deux images ont ete publiees manuellement sur Docker Hub sous mouedrhi492 avec les tags latest et 8d39914b870aee697761d49b1a947eefedbd5786. Leur accessibilite publique et leurs digests sont verifies dans docs/publication.json. Le depot GitHub distant et une execution distante du workflow restent a realiser.')
sub('9. Validation locale')
validation = out / 'validation.txt'
p(validation.read_text(encoding='utf-8') if validation.exists() else 'Voir docs/validation.txt pour les verifications reellement executees et leurs limites.')
sub('10. Demonstration et reprise')
p('1. Executer python scripts/setup.py puis docker compose up -d --build --wait. 2. Montrer docker compose ps et le site localhost:8080. 3. Ajouter un article et le retrouver. 4. Executer down puis up -d --wait et constater la persistance. 5. Presenter le reseau, le volume, USER www-data, les secrets et le workflow. README.md contient les commandes exactes et les procedures de scan et publication.')
sub('References officielles')
for url in ['https://hub.docker.com/_/php','https://hub.docker.com/_/mariadb','https://docs.docker.com/compose/how-tos/use-secrets/','https://docs.docker.com/compose/']:
    p(url)

def footer(canvas, doc):
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2*cm, 1.25*cm, 'Projet Docker Ynov - Rapport technique')
    canvas.drawRightString(19*cm, 1.25*cm, str(doc.page))
SimpleDocTemplate(str(out / 'Rapport-technique.pdf'), rightMargin=2*cm, leftMargin=2*cm, topMargin=1.8*cm, bottomMargin=2*cm).build(story, onFirstPage=footer, onLaterPages=footer)
print('Rapport cree : docs/Rapport-technique.pdf')
