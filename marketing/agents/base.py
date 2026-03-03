"""
Classe de base pour tous les agents du pipeline vidéo.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger('marketing.agents')


@dataclass
class AgentResult:
    """Résultat d'une exécution d'agent."""
    success: bool
    agent_name: str
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0
    cost_usd: float = 0
    
    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.agent_name}: {self.message}"


class BaseAgent:
    """
    Agent de base pour le pipeline de production vidéo.
    
    Chaque agent:
    - Prend un VideoProductionJob en entrée
    - Effectue sa tâche
    - Met à jour le job
    - Retourne un AgentResult
    """
    
    name: str = "BaseAgent"
    
    def __init__(self, **config):
        self.config = config
        self.logger = logging.getLogger(f'marketing.agents.{self.name}')
    
    def run(self, job) -> AgentResult:
        """
        Exécute l'agent sur un job.
        
        Args:
            job: VideoProductionJob instance
        
        Returns:
            AgentResult
        """
        start = datetime.now()
        self.logger.info(f"[{self.name}] Starting on job #{job.id}: {job.title}")
        
        try:
            result = self.execute(job)
            result.duration_seconds = (datetime.now() - start).total_seconds()
            
            if result.success:
                self.logger.info(f"[{self.name}] ✅ Completed: {result.message}")
            else:
                self.logger.warning(f"[{self.name}] ❌ Failed: {result.message}")
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.logger.error(f"[{self.name}] 💥 Exception: {e}", exc_info=True)
            
            return AgentResult(
                success=False,
                agent_name=self.name,
                message=f"Exception: {str(e)}",
                errors=[str(e)],
                duration_seconds=duration
            )
    
    def execute(self, job) -> AgentResult:
        """
        Logique métier de l'agent. À implémenter dans chaque sous-classe.
        """
        raise NotImplementedError(f"{self.name}.execute() not implemented")
    
    def can_run(self, job) -> bool:
        """
        Vérifie si l'agent peut s'exécuter sur ce job.
        Vérifie les pré-conditions (statut, dépendances).
        """
        return True
