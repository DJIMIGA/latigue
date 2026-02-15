"""
Générateur d'images avec DALL-E 3 (OpenAI)
"""
import os
import requests
from io import BytesIO
from PIL import Image
from openai import OpenAI


class ImageGenerator:
    """Génère des images avec DALL-E 3"""
    
    def __init__(self):
        """Initialise le client OpenAI"""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "dall-e-3"
        self.default_size = "1024x1792"  # Format vertical pour Reels/TikTok (9:16)
        self.default_quality = "standard"  # "standard" ou "hd" (2x plus cher)
        self.default_style = "vivid"  # "vivid" ou "natural"
    
    def generate(
        self,
        prompt: str,
        size: str = None,
        quality: str = None,
        style: str = None
    ) -> dict:
        """
        Génère une image avec DALL-E 3
        
        Args:
            prompt: Description de l'image
            size: "1024x1024", "1024x1792" (portrait), "1792x1024" (paysage)
            quality: "standard" ou "hd"
            style: "vivid" (vibrant) ou "natural" (naturel)
        
        Returns:
            {
                'url': str,           # URL temporaire de l'image
                'revised_prompt': str # Prompt amélioré par DALL-E
            }
        """
        size = size or self.default_size
        quality = quality or self.default_quality
        style = style or self.default_style
        
        try:
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=1
            )
            
            image_data = response.data[0]
            
            return {
                'url': image_data.url,
                'revised_prompt': image_data.revised_prompt
            }
        
        except Exception as e:
            print(f"❌ Erreur génération image : {e}")
            raise
    
    def generate_multiple(
        self,
        prompts: list,
        size: str = None,
        quality: str = None,
        style: str = None
    ) -> list:
        """
        Génère plusieurs images à partir d'une liste de prompts
        
        Args:
            prompts: Liste de descriptions
            size, quality, style: Paramètres DALL-E
        
        Returns:
            Liste de dicts {'url': ..., 'revised_prompt': ...}
        """
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"🎨 Génération image {i+1}/{len(prompts)}...")
            try:
                result = self.generate(prompt, size, quality, style)
                results.append(result)
            except Exception as e:
                print(f"⚠️ Erreur image {i+1}: {e}")
                # Continuer avec les autres
                results.append({
                    'url': None,
                    'revised_prompt': None,
                    'error': str(e)
                })
        
        return results
    
    def download_image(self, url: str) -> bytes:
        """
        Télécharge une image depuis une URL
        
        Args:
            url: URL de l'image (générée par DALL-E)
        
        Returns:
            Bytes de l'image (PNG)
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"❌ Erreur téléchargement image : {e}")
            raise
    
    def save_image(self, url: str, file_path: str):
        """
        Télécharge et sauvegarde une image localement
        
        Args:
            url: URL de l'image
            file_path: Chemin de sauvegarde local
        """
        image_bytes = self.download_image(url)
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        print(f"✅ Image sauvegardée : {file_path}")
    
    def resize_for_video(self, image_bytes: bytes, target_size: tuple = (1080, 1920)) -> bytes:
        """
        Redimensionne une image au format vidéo (9:16)
        
        Args:
            image_bytes: Image source en bytes
            target_size: (width, height) - défaut 1080x1920 (9:16)
        
        Returns:
            Image redimensionnée en bytes (PNG)
        """
        try:
            # Charger l'image
            img = Image.open(BytesIO(image_bytes))
            
            # Redimensionner en gardant le ratio
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # Créer un fond noir au format cible
            background = Image.new('RGB', target_size, (0, 0, 0))
            
            # Centrer l'image redimensionnée sur le fond
            offset_x = (target_size[0] - img.width) // 2
            offset_y = (target_size[1] - img.height) // 2
            background.paste(img, (offset_x, offset_y))
            
            # Convertir en bytes
            output = BytesIO()
            background.save(output, format='PNG')
            return output.getvalue()
        
        except Exception as e:
            print(f"❌ Erreur redimensionnement : {e}")
            raise


# Fonctions helpers pour usage rapide
def generate_image(prompt: str, size: str = "1024x1792", quality: str = "standard") -> dict:
    """
    Fonction rapide pour générer une image
    
    Args:
        prompt: Description de l'image
        size: "1024x1024", "1024x1792" (portrait), "1792x1024" (paysage)
        quality: "standard" ou "hd"
    
    Returns:
        {'url': ..., 'revised_prompt': ...}
    
    Usage:
        from marketing.ai.image_generator import generate_image
        result = generate_image("A vibrant illustration of Python code")
        print(result['url'])
    """
    generator = ImageGenerator()
    return generator.generate(prompt, size=size, quality=quality)


def generate_images_for_script(script_data: dict) -> list:
    """
    Génère toutes les images pour un script vidéo
    
    Args:
        script_data: Dict du script (contient 'image_prompts')
    
    Returns:
        Liste de dicts {'url': ..., 'revised_prompt': ...}
    
    Usage:
        from marketing.ai import generate_script
        from marketing.ai.image_generator import generate_images_for_script
        
        script = generate_script('tips', 'Python tips')
        images = generate_images_for_script(script)
        print(f"✅ {len(images)} images générées")
    """
    prompts = script_data.get('image_prompts', [])
    
    if not prompts:
        raise ValueError("Le script ne contient pas de 'image_prompts'")
    
    generator = ImageGenerator()
    return generator.generate_multiple(prompts)


def download_and_save_images(image_results: list, output_dir: str, video_id: int) -> list:
    """
    Télécharge et sauvegarde plusieurs images localement
    
    Args:
        image_results: Liste de dicts {'url': ..., 'revised_prompt': ...}
        output_dir: Dossier de sauvegarde
        video_id: ID du projet vidéo
    
    Returns:
        Liste de chemins locaux des images sauvegardées
    
    Usage:
        from marketing.ai.image_generator import generate_images_for_script, download_and_save_images
        
        images = generate_images_for_script(script)
        paths = download_and_save_images(images, '/tmp/video_1', video_id=1)
        print(f"Images : {paths}")
    """
    import os
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    
    generator = ImageGenerator()
    saved_paths = []
    
    for i, result in enumerate(image_results):
        if result.get('url'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"img_{i}_{timestamp}.png"
            file_path = os.path.join(output_dir, filename)
            
            try:
                generator.save_image(result['url'], file_path)
                saved_paths.append(file_path)
            except Exception as e:
                print(f"⚠️ Impossible de sauvegarder image {i}: {e}")
        else:
            print(f"⚠️ Image {i} n'a pas d'URL (erreur lors de la génération)")
    
    return saved_paths


if __name__ == '__main__':
    # Test rapide
    generator = ImageGenerator()
    
    # Générer une image test
    result = generator.generate(
        "A modern, vibrant illustration of Python code with colorful syntax highlighting, digital art style",
        size="1024x1792",
        quality="standard"
    )
    
    print(f"✅ Image générée : {result['url']}")
    print(f"📝 Prompt amélioré : {result['revised_prompt']}")
    
    # Télécharger et sauvegarder
    # generator.save_image(result['url'], '/tmp/test_image.png')
