"""
VoiceAgent — Génère l'audio voix-off via ElevenLabs.

Workflow:
1. Récupère le texte voiceover du script
2. Envoie à ElevenLabs TTS
3. Sauvegarde le .wav/.mp3
4. Met à jour le job avec le chemin audio
"""

import os
import requests
from django.conf import settings
from .base import BaseAgent, AgentResult


class VoiceAgent(BaseAgent):
    name = "VoiceAgent"
    
    # Voix par défaut ElevenLabs
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    DEFAULT_MODEL = "eleven_multilingual_v2"
    
    def can_run(self, job) -> bool:
        return job.status == 'script_ready'
    
    def execute(self, job) -> AgentResult:
        """Génère l'audio voix-off pour le script du job."""
        
        api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
        if not api_key:
            return AgentResult(
                success=False,
                agent_name=self.name,
                message="ELEVENLABS_API_KEY non configurée",
                errors=["missing_api_key"]
            )
        
        # Extraire le texte voiceover
        voiceover_text = self._extract_voiceover(job)
        if not voiceover_text:
            return AgentResult(
                success=False,
                agent_name=self.name,
                message="Pas de texte voiceover dans le script",
                errors=["no_voiceover_text"]
            )
        
        voice_id = job.get_config('voice_id', self.DEFAULT_VOICE_ID)
        model_id = job.get_config('tts_model', self.DEFAULT_MODEL)
        
        try:
            # Appel ElevenLabs TTS
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": voiceover_text,
                    "model_id": model_id,
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75,
                        "style": 0.5,
                        "use_speaker_boost": True
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            
            # Sauvegarder l'audio
            output_dir = os.path.join(
                getattr(settings, 'MEDIA_ROOT', '/tmp'),
                'marketing', 'audio'
            )
            os.makedirs(output_dir, exist_ok=True)
            
            audio_path = os.path.join(output_dir, f"job_{job.id}_voiceover.mp3")
            with open(audio_path, 'wb') as f:
                f.write(response.content)
            
            # Mettre à jour le job
            job.config = {**job.config, 'audio_path': audio_path}
            job.status = 'assets_ready'
            job.save(update_fields=['config', 'status'])
            
            # Estimer coût (~$0.30/1000 chars pour Multilingual v2)
            cost = len(voiceover_text) * 0.0003
            
            return AgentResult(
                success=True,
                agent_name=self.name,
                message=f"Audio généré: {len(voiceover_text)} chars → {audio_path}",
                data={
                    "audio_path": audio_path,
                    "text_length": len(voiceover_text),
                    "voice_id": voice_id,
                },
                cost_usd=cost
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                agent_name=self.name,
                message=f"ElevenLabs error: {e}",
                errors=[str(e)]
            )
    
    def _extract_voiceover(self, job) -> str:
        """Extrait le texte voiceover du script."""
        import json
        
        script = job.script_text
        
        # Essayer de parser comme JSON
        try:
            data = json.loads(script)
            if 'voiceover_text' in data:
                return data['voiceover_text']
            # Assembler les sections
            parts = []
            for section in ['hook', 'problem', 'framework', 'example', 'cta']:
                if section in data:
                    text = data[section].get('text', data[section]) if isinstance(data[section], dict) else data[section]
                    parts.append(str(text))
            return " ".join(parts)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Script texte brut — extraire les parties après les labels
        lines = []
        for line in script.split('\n'):
            line = line.strip()
            if ':' in line and any(k in line.upper() for k in ['HOOK', 'PROBLEM', 'SOLUTION', 'PROOF', 'CTA', 'MICRO']):
                # Prendre la partie après le dernier ':'
                text = line.split(':', 1)[-1].strip()
                lines.append(text)
            elif line and not line.startswith('['):
                lines.append(line)
        
        return " ".join(lines) if lines else script
