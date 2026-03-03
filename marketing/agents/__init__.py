"""
Agents de production vidéo autonome.
Pipeline inspiré de l'architecture Matt Ganzak (11 agents).

Architecture:
    IdeaIntakeAgent     → Récupère idées, crée VideoJobs
    ScriptWriterAgent   → Génère scripts format court
    VoiceAgent          → Génère audio voix-off (ElevenLabs)
    AvatarVideoAgent    → Génère vidéo avatar (HeyGen) OU vidéo IA (MiniMax/Luma)
    CaptionAgent        → Ajoute sous-titres
    QAAgent             → Contrôle qualité automatique
    PublisherAgent      → Publication multi-plateforme
    AnalyticsAgent      → Suivi performance hebdomadaire

Chaque agent est un service indépendant appelable par:
- Management command Django
- Cron OpenClaw
- Interface web
"""

from .base import BaseAgent, AgentResult
from .idea_intake import IdeaIntakeAgent
from .script_writer import ScriptWriterAgent
from .voice_agent import VoiceAgent
from .video_agent import VideoAgent
from .qa_agent import QAAgent

__all__ = [
    'BaseAgent',
    'AgentResult', 
    'IdeaIntakeAgent',
    'ScriptWriterAgent',
    'VoiceAgent',
    'VideoAgent',
    'QAAgent',
]
