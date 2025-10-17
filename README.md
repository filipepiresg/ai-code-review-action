# 🤖 AI Code Review Action

Esta GitHub Action realiza uma **revisão automática de código** usando **GPT-5**.  
Quando acionada em um **Pull Request**, ela:

- Analisa apenas os arquivos modificados;
- Detecta vulnerabilidades e más práticas;
- Sugere melhorias linha a linha;
- Comenta automaticamente o resultado no PR.

---

## 🚀 Como usar

### 1. Adicione a Action ao seu workflow

No repositório que deseja usar a análise, crie o arquivo:
`.github/workflows/ai-review.yml`

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Executar revisão com IA
        uses: org/ai-code-review-action@v1
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          analyze_limit: 8
          model: gpt-5
```
