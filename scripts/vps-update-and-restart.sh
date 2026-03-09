#!/bin/bash
# Mise à jour du code sur le VPS et redémarrage des conteneurs
# À lancer sur le VPS après modification du code.
# Le code est développé directement sur le VPS : on push sur Git puis on rebuild.
#
# Usage (depuis la racine du repo sur le VPS) :
#   ./scripts/vps-update-and-restart.sh
#   ./scripts/vps-update-and-restart.sh --no-push   # ne pas faire git push, seulement rebuild + restart
#   ./scripts/vps-update-and-restart.sh -m "message" # message de commit personnalisé
#
set -e
cd "$(dirname "$0")/.."
COMPOSE_FILE="docker-compose.yml"

DO_PUSH=true
COMMIT_MSG="mise à jour depuis le VPS"
for arg in "$@"; do
  if [ "$arg" = "--no-push" ]; then
    DO_PUSH=false
  fi
done
# Récupérer le message de commit personnalisé (-m "message")
while [[ $# -gt 0 ]]; do
  case "$1" in
    -m) COMMIT_MSG="$2"; shift 2 ;;
    *) shift ;;
  esac
done

echo "=========================================="
echo "Latigue - Mise à jour VPS"
echo "=========================================="

if [ "$DO_PUSH" = true ] && [ -d .git ]; then
  echo "📤 Sauvegarde du code sur Git..."
  git add -A
  git diff --cached --quiet && echo "  Rien à committer." || {
    git commit -m "$COMMIT_MSG"
    git push origin main
    echo "  ✅ Code pushé sur origin/main."
  }
fi

echo "🔨 Rebuild de l'image web..."
docker compose -f "$COMPOSE_FILE" build --no-cache web

echo "🔄 Redémarrage du conteneur web..."
docker compose -f "$COMPOSE_FILE" up -d --force-recreate web

echo ""
echo "🧹 Nettoyage (sans toucher aux volumes ni aux conteneurs en cours)..."
docker image prune -f
docker builder prune -f
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Mise à jour terminée. Le site utilise le nouveau code."
echo "   Vérifier les logs si besoin: docker compose -f $COMPOSE_FILE logs -f web"
