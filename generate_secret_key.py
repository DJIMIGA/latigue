#!/usr/bin/env python3
"""
Script pour générer une nouvelle SECRET_KEY Django sécurisée
Usage: python generate_secret_key.py
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print("\n" + "="*70)
    print("🔐 NOUVELLE DJANGO SECRET_KEY GÉNÉRÉE")
    print("="*70)
    print(f"\n{secret_key}\n")
    print("="*70)
    print("⚠️  IMPORTANT: Copiez cette clé dans votre fichier .env.production")
    print("⚠️  Ne partagez JAMAIS cette clé publiquement!")
    print("="*70 + "\n")
