# 📦 Configuration MinIO pour Stockage Vidéo

MinIO est un stockage objet S3-compatible, self-hosted. Il remplace AWS S3 pour stocker les vidéos, images et audios générés par le pipeline marketing IA.

## 🎯 Pourquoi MinIO ?

- ✅ **Self-hosted** : Données sur ton VPS, pas de coûts cloud externe
- ✅ **Compatible S3** : Utilise boto3, aucun changement de code
- ✅ **Gratuit** : Open-source, pas de limite
- ✅ **Interface Web** : Console pour visualiser/gérer les fichiers
- ✅ **Performant** : Idéal pour vidéos volumineuses

## 🚀 Déploiement

### 1. Configuration déjà ajoutée

Le service MinIO est déjà configuré dans `docker-compose.prod.yml` :

```yaml
services:
  minio:
    image: minio/minio:latest
    container_name: latigue_minio
    ports:
      - "9000:9000"  # API S3
      - "9001:9001"  # Console Web
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin123
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
```

### 2. Variables d'environnement

Ajouter dans `.env.production` :

```bash
# === MinIO (Stockage S3-compatible) ===
MINIO_ENDPOINT=http://minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changeme_production_password
MINIO_BUCKET_VIDEOS=marketing-videos

# Django doit utiliser MinIO au lieu de AWS S3
AWS_S3_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=changeme_production_password
```

**⚠️ IMPORTANT : Change le mot de passe en production !**

### 3. Démarrer MinIO

```bash
cd /opt/app/latigue
docker compose -f docker-compose.prod.yml up -d minio
```

### 4. Accéder à la Console Web

URL : `http://159.195.104.193:9001`

**Login :**
- Username : `minioadmin` (ou valeur de `MINIO_ROOT_USER`)
- Password : `minioadmin123` (ou valeur de `MINIO_ROOT_PASSWORD`)

**Actions dans la console :**
- Créer le bucket `marketing-videos` (fait automatiquement par le code Python)
- Visualiser les fichiers uploadés
- Configurer les policies (public read pour les vidéos)
- Monitorer l'espace disque

### 5. Sécurité (si exposé publiquement)

Si tu veux accéder à MinIO depuis l'extérieur du VPS :

**Option 1 : Nginx reverse proxy (recommandé)**
```nginx
# /etc/nginx/sites-available/minio.bolibana.net
server {
    listen 80;
    server_name minio.bolibana.net;

    location / {
        proxy_pass http://localhost:9001;  # Console
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# API S3
server {
    listen 80;
    server_name s3.bolibana.net;

    location / {
        proxy_pass http://localhost:9000;  # API S3
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Ensuite SSL avec certbot :
```bash
certbot --nginx -d minio.bolibana.net -d s3.bolibana.net
```

**Option 2 : Firewall (limiter accès)**
```bash
# Bloquer accès externe, autoriser uniquement localhost
ufw deny 9000
ufw deny 9001
```

## 🧪 Test de connexion

### Via Python (Django shell)

```bash
docker exec -it latigue_web python manage.py shell
```

```python
from marketing.storage import get_storage

# Tester connexion
storage = get_storage()
print(f"✅ Connecté : {storage.endpoint}")
print(f"✅ Bucket : {storage.bucket_videos}")

# Lister fichiers
files = storage.list_files()
print(f"📁 Fichiers : {len(files)}")
```

### Via CLI boto3

```python
import boto3
from botocore.client import Config

s3 = boto3.client(
    's3',
    endpoint_url='http://159.195.104.193:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin123',
    config=Config(signature_version='s3v4')
)

# Lister buckets
response = s3.list_buckets()
print("Buckets:", [b['Name'] for b in response['Buckets']])
```

## 📊 Structure de stockage

Les fichiers sont organisés ainsi :

```
marketing-videos/
├── videos/
│   ├── 1/                        # VideoProject ID 1
│   │   ├── images/
│   │   │   ├── img_0_20260215_070000.png
│   │   │   ├── img_1_20260215_070001.png
│   │   │   └── ...
│   │   ├── audio_20260215_070100.mp3
│   │   └── final_20260215_070200.mp4
│   ├── 2/
│   │   ├── ...
│   └── ...
```

**Avantages :**
- Organisé par projet vidéo
- Timestamps pour versionning
- Facile de nettoyer un projet (supprimer dossier)

## 🔧 Usage dans le code

### Upload une vidéo

```python
from marketing.storage import upload_video

url = upload_video('/tmp/final.mp4', video_id=1)
print(f"✅ Vidéo uploadée : {url}")
# → http://minio:9000/marketing-videos/videos/1/final_20260215_070200.mp4
```

### Upload des images

```python
from marketing.storage import upload_image

for i, img_path in enumerate(image_paths):
    url = upload_image(img_path, video_id=1, index=i)
    print(f"✅ Image {i} : {url}")
```

### Upload un audio

```python
from marketing.storage import upload_audio

url = upload_audio('/tmp/voiceover.mp3', video_id=1)
print(f"✅ Audio : {url}")
```

### Instance globale

```python
from marketing.storage import get_storage

storage = get_storage()

# Upload custom
storage.upload_file('/tmp/test.txt', 'folder/test.txt')

# Liste fichiers
files = storage.list_files(prefix='videos/1/')

# Supprimer
storage.delete_file('videos/1/old.mp4')

# URL publique
url = storage.get_url('videos/1/final.mp4')
```

## 🗂️ Migration depuis AWS S3 (optionnel)

Si tu as des fichiers sur AWS S3 et veux les migrer :

```bash
# Installer MinIO Client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# Configurer aliases
mc alias set myminio http://localhost:9000 minioadmin minioadmin123
mc alias set myaws https://s3.amazonaws.com AWS_KEY AWS_SECRET

# Copier bucket entier
mc mirror myaws/personalporfolio myminio/marketing-videos
```

## 📈 Monitoring & Maintenance

### Espace disque utilisé

```bash
# Taille du volume Docker
docker volume inspect latigue_minio_data

# Espace dans le container
docker exec latigue_minio du -sh /data
```

### Backup

```bash
# Backup du volume
docker run --rm \
  -v latigue_minio_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/minio_backup_$(date +%Y%m%d).tar.gz /data

# Restaurer
docker run --rm \
  -v latigue_minio_data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd / && tar xzf /backup/minio_backup_20260215.tar.gz"
```

### Nettoyer vieux fichiers

```python
from marketing.storage import get_storage
from datetime import datetime, timedelta

storage = get_storage()

# Supprimer fichiers > 30 jours
cutoff = datetime.now() - timedelta(days=30)
files = storage.list_files()

for file in files:
    # Parser timestamp du nom
    # Supprimer si ancien
    pass
```

## 🔗 URLs accessibles

**Depuis le container Django :**
- API S3 : `http://minio:9000`
- Console : `http://minio:9001`

**Depuis le host (VPS) :**
- API S3 : `http://localhost:9000`
- Console : `http://localhost:9001`

**Depuis l'extérieur (si configuré) :**
- API S3 : `https://s3.bolibana.net`
- Console : `https://minio.bolibana.net`

## ⚡ Performance

**Tips pour optimiser :**
- Vidéos : Compresser avec H.264 (codec compatible web)
- Images : PNG → WebP (50% moins lourd)
- Multipart upload pour fichiers >5MB (boto3 le fait automatiquement)
- Configurer lifecycle policies pour archivage auto

## 🆘 Troubleshooting

### "Connection refused" depuis Django
```bash
# Vérifier que MinIO tourne
docker ps | grep minio

# Vérifier les logs
docker logs latigue_minio

# Vérifier le réseau Docker
docker network inspect latigue_app_network
```

### "AccessDenied" lors de l'upload
```python
# Vérifier credentials
import os
print(os.getenv('MINIO_ROOT_USER'))
print(os.getenv('MINIO_ROOT_PASSWORD'))
```

### Bucket n'existe pas
```python
# Le créer manuellement
from marketing.storage import get_storage
storage = get_storage()
# Le bucket est créé automatiquement au premier appel
```

---

*Dernière mise à jour : 2026-02-15*
