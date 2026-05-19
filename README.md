# Avis API

API FastAPI pour la collecte et le traitement des avis.

## Installation locale

1. Créer un environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Installer les dépendances

```bash
pip install -r requirements.txt
```

3. Copier le fichier d'exemple

```bash
cp .env.example .env
```

4. Lancer le serveur

```bash
python3 main.py
```

> Important : exécutez toujours la commande depuis la racine du dépôt (`avis-api`), pas depuis le dossier `app/`.

## Variables d'environnement

- `APP_ENV`: `development` ou `production`
- `DATABASE_URL`: URL de connexion à la base de données SQL.
  - En production, cette variable doit être définie pour utiliser MySQL, PostgreSQL, ou autre base SQL.
  - Si elle n'est pas définie, l'application utilisera par défaut SQLite locale (`sqlite:///./avis.db`).
  - Exemples :
    - SQLite local : `sqlite:///./avis.db`
    - PostgreSQL : `postgresql+psycopg[binary]://user:password@host:5432/dbname`
    - MySQL : `mysql+pymysql://user:password@host:3306/dbname`
- `CORS_ORIGINS`: liste d'origines autorisées pour CORS, séparées par des virgules

## Docker

Build et démarrage :

```bash
docker build -t avis-api .
docker run -d -p 8000:8000 --name avis-api avis-api
```

### Utilisation avec Docker Compose

Un `docker-compose.yml` est fourni pour démarrer l'API, MySQL et PHPMyAdmin ensemble :

```bash
docker compose up -d --build
```

Accès :
- API : `http://localhost:8000`
- PHPMyAdmin : `http://localhost:8080`

### Configuration MySQL

Pour utiliser MySQL avec Docker Compose, remplacez dans `.env` :

```env
APP_ENV=development
DATABASE_URL=mysql+pymysql://avis_user:avis_password@db:3306/avis_db
```

> En production, vous pouvez utiliser Docker directement sur le serveur et définir `DATABASE_URL` via des variables d'environnement ou un fichier `.env` sécurisé.

### PhpMyAdmin

`phpmyadmin` est utile pour le développement et l'administration interne, mais il n'est pas recommandé de l'exposer publiquement en production.

> Pour production sans phpMyAdmin : commentez ou supprimez la section `phpmyadmin` du `docker-compose.yml`.

## Structure

- `app/main.py` : point d'entrée FastAPI
- `app/database.py` : configuration SQLAlchemy
- `app/models.py` : schémas Pydantic et enums
- `app/config.py` : configuration d'environnement et CORS

## Notes

- `.gitignore` ignore le venv, les fichiers temporaires, les fichiers `.env` et les bases SQLite locales
- `app/__init__.py` permet d'importer le package `app` proprement
