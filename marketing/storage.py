"""
Helper pour gérer le stockage MinIO (compatible S3)
"""
import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class MinIOStorage:
    """Client MinIO pour upload/download de fichiers"""
    
    def __init__(self):
        """Initialise le client S3 compatible MinIO"""
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
        self.access_key = os.getenv('MINIO_ROOT_USER', 'minioadmin')
        self.secret_key = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin123')
        self.bucket_videos = os.getenv('MINIO_BUCKET_VIDEOS', 'marketing-videos')
        
        # Client boto3 configuré pour MinIO
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'  # MinIO ignore la région, mais boto3 la requiert
        )
        
        # Créer le bucket s'il n'existe pas
        self._ensure_bucket_exists(self.bucket_videos)
    
    def _ensure_bucket_exists(self, bucket_name: str):
        """Crée le bucket s'il n'existe pas"""
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError:
            # Bucket n'existe pas, le créer
            try:
                self.client.create_bucket(Bucket=bucket_name)
                print(f"✅ Bucket créé : {bucket_name}")
                
                # Rendre le bucket public (lecture seule)
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                        }
                    ]
                }
                import json
                self.client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(bucket_policy)
                )
                print(f"✅ Bucket policy appliquée : {bucket_name} (public read)")
            except Exception as e:
                print(f"⚠️ Impossible de créer le bucket {bucket_name}: {e}")
    
    def upload_file(self, file_path: str, object_name: str = None, bucket: str = None) -> str:
        """
        Upload un fichier vers MinIO
        
        Args:
            file_path: Chemin local du fichier
            object_name: Nom de l'objet dans MinIO (optionnel, utilise le nom du fichier)
            bucket: Nom du bucket (optionnel, utilise bucket_videos par défaut)
        
        Returns:
            URL publique du fichier
        """
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        if bucket is None:
            bucket = self.bucket_videos
        
        try:
            self.client.upload_file(file_path, bucket, object_name)
            url = f"{self.endpoint}/{bucket}/{object_name}"
            print(f"✅ Fichier uploadé : {url}")
            return url
        except Exception as e:
            print(f"❌ Erreur upload : {e}")
            raise
    
    def upload_bytes(self, data: bytes, object_name: str, content_type: str = None, bucket: str = None) -> str:
        """
        Upload des bytes vers MinIO
        
        Args:
            data: Données binaires
            object_name: Nom de l'objet dans MinIO
            content_type: Type MIME (ex: 'video/mp4', 'image/png')
            bucket: Nom du bucket (optionnel)
        
        Returns:
            URL publique du fichier
        """
        if bucket is None:
            bucket = self.bucket_videos
        
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        try:
            from io import BytesIO
            self.client.upload_fileobj(
                BytesIO(data),
                bucket,
                object_name,
                ExtraArgs=extra_args
            )
            url = f"{self.endpoint}/{bucket}/{object_name}"
            print(f"✅ Bytes uploadés : {url}")
            return url
        except Exception as e:
            print(f"❌ Erreur upload bytes : {e}")
            raise
    
    def download_file(self, object_name: str, file_path: str, bucket: str = None):
        """
        Télécharge un fichier depuis MinIO
        
        Args:
            object_name: Nom de l'objet dans MinIO
            file_path: Chemin local de destination
            bucket: Nom du bucket (optionnel)
        """
        if bucket is None:
            bucket = self.bucket_videos
        
        try:
            self.client.download_file(bucket, object_name, file_path)
            print(f"✅ Fichier téléchargé : {file_path}")
        except Exception as e:
            print(f"❌ Erreur download : {e}")
            raise
    
    def delete_file(self, object_name: str, bucket: str = None):
        """
        Supprime un fichier de MinIO
        
        Args:
            object_name: Nom de l'objet dans MinIO
            bucket: Nom du bucket (optionnel)
        """
        if bucket is None:
            bucket = self.bucket_videos
        
        try:
            self.client.delete_object(Bucket=bucket, Key=object_name)
            print(f"✅ Fichier supprimé : {object_name}")
        except Exception as e:
            print(f"❌ Erreur suppression : {e}")
            raise
    
    def list_files(self, prefix: str = '', bucket: str = None) -> list:
        """
        Liste les fichiers dans un bucket
        
        Args:
            prefix: Préfixe de filtrage (ex: 'videos/2024/')
            bucket: Nom du bucket (optionnel)
        
        Returns:
            Liste de noms d'objets
        """
        if bucket is None:
            bucket = self.bucket_videos
        
        try:
            response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except Exception as e:
            print(f"❌ Erreur listage : {e}")
            return []
    
    def get_url(self, object_name: str, bucket: str = None) -> str:
        """
        Retourne l'URL publique d'un fichier
        
        Args:
            object_name: Nom de l'objet dans MinIO
            bucket: Nom du bucket (optionnel)
        
        Returns:
            URL publique
        """
        if bucket is None:
            bucket = self.bucket_videos
        
        return f"{self.endpoint}/{bucket}/{object_name}"


# Instance globale (singleton)
_storage = None

def get_storage() -> MinIOStorage:
    """Retourne l'instance globale de MinIOStorage"""
    global _storage
    if _storage is None:
        _storage = MinIOStorage()
    return _storage


# Fonctions helpers pour usage rapide
def upload_video(file_path: str, video_id: int) -> str:
    """
    Upload une vidéo avec nom standardisé
    
    Args:
        file_path: Chemin local de la vidéo
        video_id: ID du VideoProject
    
    Returns:
        URL publique
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    object_name = f"videos/{video_id}/final_{timestamp}.mp4"
    return get_storage().upload_file(file_path, object_name)


def upload_image(file_path: str, video_id: int, index: int) -> str:
    """
    Upload une image avec nom standardisé
    
    Args:
        file_path: Chemin local de l'image
        video_id: ID du VideoProject
        index: Index de l'image (0, 1, 2...)
    
    Returns:
        URL publique
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    object_name = f"videos/{video_id}/images/img_{index}_{timestamp}.png"
    return get_storage().upload_file(file_path, object_name)


def upload_audio(file_path: str, video_id: int) -> str:
    """
    Upload un fichier audio avec nom standardisé
    
    Args:
        file_path: Chemin local de l'audio
        video_id: ID du VideoProject
    
    Returns:
        URL publique
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    object_name = f"videos/{video_id}/audio_{timestamp}.mp3"
    return get_storage().upload_file(file_path, object_name)


if __name__ == '__main__':
    # Test rapide
    storage = get_storage()
    print(f"✅ MinIO connecté : {storage.endpoint}")
    print(f"✅ Bucket vidéos : {storage.bucket_videos}")
    
    # Lister les fichiers
    files = storage.list_files()
    print(f"📁 Fichiers dans le bucket : {len(files)}")
    for f in files[:10]:  # Premiers 10
        print(f"  - {f}")
