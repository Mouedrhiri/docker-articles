"""Initialise la configuration sans remplacer les secrets existants."""
from pathlib import Path
import secrets
import shutil

root = Path(__file__).resolve().parents[1]
if not (root / '.env').exists():
    shutil.copyfile(root / '.env.example', root / '.env')
(root / 'secrets').mkdir(exist_ok=True)
for name in ('db_password', 'db_root_password'):
    path = root / 'secrets' / (name + '.txt')
    if not path.exists():
        path.write_text(secrets.token_urlsafe(32), encoding='utf-8')
        # Lecture requise pour www-data dans le conteneur. Proteger le dossier hote.
        path.chmod(0o644)
print('Configuration prete. Lancer : docker compose up -d --build --wait')
