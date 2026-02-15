"""
Générateur de voix-off avec ElevenLabs TTS
"""
import os
from elevenlabs import generate, set_api_key, voices, Voice


class TTSGenerator:
    """Génère des voix-off réalistes avec ElevenLabs"""
    
    def __init__(self):
        """Initialise le client ElevenLabs"""
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY non configurée")
        
        set_api_key(api_key)
        
        # Voix par défaut (multilingue, supporte français)
        self.default_voice = "Adam"  # Voix masculine, claire
        # Alternatives: "Bella" (féminine), "Antoni" (masculine profonde)
        
        self.default_model = "eleven_multilingual_v2"  # Supporte français
    
    def generate(
        self,
        text: str,
        voice: str = None,
        model: str = None
    ) -> bytes:
        """
        Génère un audio à partir de texte
        
        Args:
            text: Texte à convertir en voix
            voice: Nom de la voix ElevenLabs (défaut: "Adam")
            model: Modèle TTS (défaut: "eleven_multilingual_v2")
        
        Returns:
            Audio en bytes (MP3)
        """
        voice = voice or self.default_voice
        model = model or self.default_model
        
        try:
            audio_bytes = generate(
                text=text,
                voice=voice,
                model=model
            )
            
            print(f"✅ Audio généré : {len(text)} caractères")
            return audio_bytes
        
        except Exception as e:
            print(f"❌ Erreur génération audio : {e}")
            raise
    
    def save_audio(
        self,
        text: str,
        file_path: str,
        voice: str = None,
        model: str = None
    ):
        """
        Génère et sauvegarde un audio localement
        
        Args:
            text: Texte à convertir
            file_path: Chemin de sauvegarde (ex: '/tmp/voiceover.mp3')
            voice: Nom de la voix
            model: Modèle TTS
        """
        audio_bytes = self.generate(text, voice, model)
        
        with open(file_path, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"✅ Audio sauvegardé : {file_path}")
    
    def list_voices(self) -> list:
        """
        Liste toutes les voix disponibles
        
        Returns:
            Liste de dicts {'name': ..., 'voice_id': ..., 'labels': ...}
        """
        try:
            all_voices = voices()
            
            voice_list = []
            for voice in all_voices:
                voice_list.append({
                    'name': voice.name,
                    'voice_id': voice.voice_id,
                    'labels': voice.labels if hasattr(voice, 'labels') else {}
                })
            
            return voice_list
        
        except Exception as e:
            print(f"❌ Erreur listage voix : {e}")
            return []
    
    def get_voice_by_name(self, name: str) -> Voice:
        """
        Récupère une voix par son nom
        
        Args:
            name: Nom de la voix (ex: "Adam", "Bella")
        
        Returns:
            Objet Voice ElevenLabs
        """
        try:
            all_voices = voices()
            for voice in all_voices:
                if voice.name.lower() == name.lower():
                    return voice
            
            raise ValueError(f"Voix '{name}' non trouvée")
        
        except Exception as e:
            print(f"❌ Erreur recherche voix : {e}")
            raise
    
    def estimate_cost(self, text: str, plan: str = "free") -> dict:
        """
        Estime le coût de génération
        
        Args:
            text: Texte à convertir
            plan: "free" (10k chars/mois) ou "starter" (30k chars/mois)
        
        Returns:
            {
                'chars': int,
                'cost_usd': float,
                'remaining_free': int  # Si plan gratuit
            }
        """
        char_count = len(text)
        
        if plan == "free":
            # Plan gratuit : 10,000 chars/mois
            return {
                'chars': char_count,
                'cost_usd': 0.0,
                'remaining_free': max(0, 10000 - char_count)
            }
        
        elif plan == "starter":
            # Plan starter : $5/mois pour 30,000 chars
            cost_per_char = 5.0 / 30000
            return {
                'chars': char_count,
                'cost_usd': char_count * cost_per_char,
                'monthly_limit': 30000
            }
        
        else:
            return {'chars': char_count}


# Fonctions helpers pour usage rapide
def generate_voiceover(text: str, voice: str = "Adam") -> bytes:
    """
    Fonction rapide pour générer une voix-off
    
    Args:
        text: Texte à convertir
        voice: Nom de la voix (défaut: "Adam")
    
    Returns:
        Audio en bytes (MP3)
    
    Usage:
        from marketing.ai.tts_generator import generate_voiceover
        audio = generate_voiceover("Bonjour, voici mon script vidéo...")
        with open('voiceover.mp3', 'wb') as f:
            f.write(audio)
    """
    generator = TTSGenerator()
    return generator.generate(text, voice=voice)


def generate_voiceover_from_script(script_data: dict, output_path: str, voice: str = "Adam"):
    """
    Génère la voix-off complète d'un script vidéo
    
    Args:
        script_data: Dict du script (contient 'voiceover')
        output_path: Chemin de sauvegarde (ex: '/tmp/voiceover.mp3')
        voice: Nom de la voix
    
    Usage:
        from marketing.ai import generate_script
        from marketing.ai.tts_generator import generate_voiceover_from_script
        
        script = generate_script('tips', 'Python tips')
        generate_voiceover_from_script(script, '/tmp/voiceover.mp3')
    """
    voiceover_text = script_data.get('voiceover')
    
    if not voiceover_text:
        raise ValueError("Le script ne contient pas de 'voiceover'")
    
    generator = TTSGenerator()
    generator.save_audio(voiceover_text, output_path, voice=voice)
    
    print(f"✅ Voix-off générée : {output_path}")


def list_available_voices() -> list:
    """
    Liste toutes les voix disponibles
    
    Returns:
        Liste de noms de voix
    
    Usage:
        from marketing.ai.tts_generator import list_available_voices
        voices = list_available_voices()
        print(f"Voix disponibles : {', '.join(voices)}")
    """
    generator = TTSGenerator()
    voice_list = generator.list_voices()
    return [v['name'] for v in voice_list]


if __name__ == '__main__':
    # Test rapide
    generator = TTSGenerator()
    
    # Texte de test en français
    test_text = """
    Bonjour ! Aujourd'hui, je vais te montrer une astuce Python incroyable.
    Les list comprehensions permettent d'écrire du code plus concis et élégant.
    N'oublie pas de suivre pour plus de tips Python !
    """
    
    # Lister les voix disponibles
    print("🎤 Voix disponibles :")
    voices = generator.list_voices()
    for v in voices[:5]:  # Premiers 5
        print(f"  - {v['name']} (ID: {v['voice_id']})")
    
    # Estimer le coût
    cost_info = generator.estimate_cost(test_text)
    print(f"\n💰 Coût estimé : {cost_info['chars']} caractères")
    if 'remaining_free' in cost_info:
        print(f"   Reste (plan gratuit) : {cost_info['remaining_free']} chars")
    
    # Générer audio test
    # audio = generator.generate(test_text, voice="Adam")
    # with open('/tmp/test_voiceover.mp3', 'wb') as f:
    #     f.write(audio)
    # print("✅ Audio test sauvegardé : /tmp/test_voiceover.mp3")
