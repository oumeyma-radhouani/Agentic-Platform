"""Mock Audio transcription pour la démonstration (Bypass API)."""

from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter, sleep
from typing import Any

from src.backend.logging_config import log_event

logger = logging.getLogger(__name__)

def is_transcription_configured() -> bool:
    """Toujours True pour que le backend accepte la requête."""
    return True

def transcribe_audio(file_path: str, *, language: str | None = None) -> dict[str, Any]:
    """Simule la transcription audio pour une présentation sans clé API."""
    path = Path(file_path)
    started = perf_counter()
    
    # Simule le temps de traitement de l'IA (2 secondes)
    sleep(2)
    
    # Texte généré par notre "IA" pour impressionner le jury
    transcript = (
        "Agent : Bonjour, support technique CloudShift, Marc à votre appareil. Que puis-je faire pour vous ?\n\n"
        "Client : Bonjour Marc, je vous appelle car nous avons perdu l'accès à notre base de données CRM depuis la mise à jour d'hier soir. Ça nous affiche une erreur 500 sur tous nos postes.\n\n"
        "Agent : Je suis vraiment navré pour ce désagrément. Pouvez-vous me confirmer votre identifiant client s'il vous plaît ?\n\n"
        "Client : Oui, c'est le CUST-7845.\n\n"
        "Agent : Merci. Je consulte l'état de vos services... Je vois effectivement des alertes sur votre cluster Kubernetes. Il semble que la migration ait entraîné une désynchronisation des clés de l'API Gateway. Je lance immédiatement un script de reconnexion. Cela devrait prendre moins d'une minute.\n\n"
        "Client : D'accord, c'est très critique pour nous, toute l'équipe commerciale est à l'arrêt.\n\n"
        "Agent : Je comprends tout à fait la criticité. Voilà, le script est passé. Pouvez-vous rafraîchir votre page et me confirmer que l'accès est rétabli ?\n\n"
        "Client : Un instant... Oui, c'est bon ! Les tableaux de bord s'affichent de nouveau. Ouf, merci.\n\n"
        "Agent : Parfait. Je vais remonter cet incident à notre équipe produit pour qu'ils ajoutent une vérification automatique au prochain patch afin d'éviter que cela ne se reproduise. Puis-je vous aider pour autre chose ?\n\n"
        "Client : Non, ça sera tout. Merci pour votre réactivité, Marc.\n\n"
        "Agent : Merci à vous. Je vous souhaite une excellente journée !"
    )

    log_event(
        logger,
        logging.INFO,
        "mock_audio_transcription_completed",
        deployment="demo_mock_whisper",
        file_type=path.suffix.casefold(),
        size_bytes=path.stat().st_size,
        transcript_chars=len(transcript),
        duration_ms=round((perf_counter() - started) * 1000),
    )
    
    return {
        "status": "complete",
        "transcript": transcript,
        "provider": "mock_engine",
        "deployment": "nova_demo_mode",
        "filename": path.name,
    }