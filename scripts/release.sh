#!/usr/bin/env bash
set -e

# ========================================
# 🔖 Script de Release para GitHub Actions
# ========================================
# 
# Este script automatiza o processo de criação de releases para GitHub Actions.
# Ele cria tags semânticas e mantém aliases para facilitar o uso da action.
#
# Funcionalidades:
# - Validação de formato de versão semântica
# - Criação de tags exatas (ex: v1.2.3)
# - Atualização de aliases major (ex: v1)
# - Opção de atualizar alias latest
# - Sincronização com repositório remoto
#
# Autor: Filipe Pires
# Versão: 1.0.0
#
# Uso:
#   ./scripts/release.sh v1.2.0          # Cria release v1.2.0 e atualiza v1
#   ./scripts/release.sh v1.2.0 true      # Também atualiza alias 'latest'
# ========================================

# ===============================================
# 📋 PARÂMETROS E VALIDAÇÃO
# ===============================================

VERSION=$1        # Versão no formato vX.Y.Z (ex: v1.2.3)
ISLATEST=$2       # Se deve atualizar alias 'latest' (true/false)

# Validação de parâmetros obrigatórios
if [ -z "$VERSION" ]; then
  echo "❌ Erro: informe a versão. Exemplo:"
  echo "   ./scripts/release.sh v1.0.0"
  echo "   ./scripts/release.sh v1.0.0 true"
  exit 1
fi

# Validação de formato semântico (vX.Y.Z)
if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "❌ Versão inválida. Use o formato semântico:"
  echo "   Exemplos válidos: v1.0.0, v2.1.3, v10.5.2"
  echo "   Formato: v[MAJOR].[MINOR].[PATCH]"
  exit 1
fi

# Extrai versão major para criar alias (ex: v1.2.3 -> v1)
MAJOR_TAG=$(echo "$VERSION" | cut -d'.' -f1)

echo "📦 Criando release $VERSION e atualizando alias $MAJOR_TAG..."

# ===============================================
# 🔄 PREPARAÇÃO DO REPOSITÓRIO
# ===============================================

# Garante que está na branch main e sincronizado
echo "🔄 Sincronizando com repositório remoto..."
git checkout main
git pull origin main

# ===============================================
# 💾 COMMIT DE RELEASE (OPCIONAL)
# ===============================================

# Pergunta se deseja criar um commit de release
read -p "Deseja criar um commit de 'Release $VERSION'? (s/n) " yn
if [[ "$yn" == "s" ]]; then
  echo "💾 Criando commit de release..."
  git add .
  git commit -m "🔖 Release $VERSION"
fi

# ===============================================
# 🏷️ CRIAÇÃO DE TAGS
# ===============================================

echo "🏷️ Criando tag exata: $VERSION"
# Cria tag anotada com mensagem de release
git tag -a "$VERSION" -m "Release $VERSION"
git push origin "$VERSION"

echo "🏷️ Atualizando alias major: $MAJOR_TAG"
# Atualiza alias major (ex: v1) para apontar para a nova versão
git tag -f "$MAJOR_TAG"
git push origin "$MAJOR_TAG" --force

# ===============================================
# 🌟 ALIAS LATEST (OPCIONAL)
# ===============================================

if [ -n "$ISLATEST" ]; then
  echo "🌟 Atualizando alias latest..."
  # Atualiza alias latest para apontar para a nova versão
  git tag -f latest
  git push origin latest --force
fi

# ===============================================
# ✅ RESUMO DA RELEASE
# ===============================================

echo ""
echo "✅ Release criada com sucesso!"
echo "   📌 Tag exata: $VERSION"
echo "   🔗 Alias atualizado: $MAJOR_TAG"
if [ -n "$ISLATEST" ]; then
  echo "   ⭐ Alias atualizado: latest"
fi
echo ""
echo "👉 Agora pode usar:"
echo "   uses: filipepiresg/ai-code-review-action@$MAJOR_TAG"
if [ -n "$ISLATEST" ]; then
  echo "   uses: filipepiresg/ai-code-review-action@latest"
fi
echo ""
echo "📚 Documentação: https://github.com/filipepiresg/ai-code-review-action"
