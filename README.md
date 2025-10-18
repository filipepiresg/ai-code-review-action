# 🤖 AI Code Review Action

[![GitHub release](https://img.shields.io/github/v/release/filipepiresg/ai-code-review-action)](https://github.com/filipepiresg/ai-code-review-action/releases)
[![GitHub license](https://img.shields.io/github/license/filipepiresg/ai-code-review-action)](https://github.com/filipepiresg/ai-code-review-action/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/filipepiresg/ai-code-review-action)](https://github.com/filipepiresg/ai-code-review-action/stargazers)

Esta GitHub Action realiza uma **revisão automática de código** usando **IA avançada** (OpenAI GPT-4/5 ou Anthropic Claude 3.x).  
Quando acionada em um **Pull Request**, ela:

- 🔍 Analisa apenas os arquivos modificados
- 🛡️ Detecta vulnerabilidades de segurança (SQLi, XSS, etc.)
- 📋 Identifica violações de boas práticas
- 💡 Sugere melhorias específicas e acionáveis
- 💬 Comenta automaticamente o resultado no PR
- 🚫 Suporte a padrões de ignore configuráveis
- 📊 Limite configurável de arquivos analisados

---

## ✨ Funcionalidades

### 🔒 Análise de Segurança

- Detecção de vulnerabilidades comuns (SQL Injection, XSS, etc.)
- Identificação de credenciais expostas
- Análise de práticas inseguras de autenticação
- Verificação de validação de entrada

### 📝 Qualidade de Código

- Detecção de código duplicado
- Análise de complexidade ciclomática
- Identificação de anti-patterns
- Sugestões de refatoração

### 🎯 Linguagens Suportadas

- **Python** (.py)
- **JavaScript/TypeScript** (.js, .ts, .jsx, .tsx)
- **Java** (.java)
- **C#** (.cs)
- **PHP** (.php)
- **Ruby** (.rb)
- **Go** (.go)
- **Swift** (.swift)
- **Kotlin** (.kt)
- **Rust** (.rs)

### ⚙️ Configurações Avançadas

- Suporte a múltiplos modelos de IA
- Sistema de ignore flexível (regex + arquivo)
- Chunking automático para arquivos grandes
- Limite configurável de arquivos analisados

---

## 🚀 Como usar

### 1. Configure as chaves de API

No seu repositório, vá em **Settings > Secrets and variables > Actions** e adicione:

- `OPENAI_API_KEY`: Sua chave da API OpenAI (formato: `sk-...`)
- `CLAUDEAI_API_KEY`: Sua chave da API Anthropic Claude (formato: `sk-ant-...`)

> **Nota**: Você precisa de pelo menos uma das duas chaves. Se ambas estiverem configuradas, a OpenAI será usada por padrão.

### 2. Adicione a Action ao seu workflow

Crie o arquivo `.github/workflows/ai-review.yml`:

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
        uses: filipepiresg/ai-code-review-action@v1
        with:
          # Chaves de API (pelo menos uma obrigatória)
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          claudeai_api_key: ${{ secrets.CLAUDEAI_API_KEY }}

          # Configurações do GitHub
          github_token: ${{ secrets.GITHUB_TOKEN }}
          repository: ${{ github.repository }}
          pr_number: ${{ github.event.pull_request.number }}

          # Configurações de análise
          analyze_limit: 8
          model: gpt-5

          # Padrões de ignore (opcional)
          ignore_file_content: |
            ^src/__tests__/
            ^node_modules/
            \.{test,spec}.{j,t}s?(x)$
            \.json$
            \.lock$

          # Arquivo de ignore (opcional)
          ignore_file_path: ".ai-review-ignore"
```

---

## ⚙️ Parâmetros de Configuração

### 🔑 Chaves de API

| Parâmetro          | Obrigatório | Descrição                     | Exemplo                           |
| ------------------ | ----------- | ----------------------------- | --------------------------------- |
| `openai_api_key`   | Não\*       | Chave da API OpenAI           | `${{ secrets.OPENAI_API_KEY }}`   |
| `claudeai_api_key` | Não\*       | Chave da API Anthropic Claude | `${{ secrets.CLAUDEAI_API_KEY }}` |

> \*Pelo menos uma das duas chaves é obrigatória.

### 🔧 Configurações do GitHub

| Parâmetro      | Obrigatório | Descrição                           | Exemplo                                   |
| -------------- | ----------- | ----------------------------------- | ----------------------------------------- |
| `github_token` | ✅          | Token do GitHub para comentar no PR | `${{ secrets.GITHUB_TOKEN }}`             |
| `repository`   | ✅          | Nome do repositório                 | `${{ github.repository }}`                |
| `pr_number`    | ✅          | Número do Pull Request              | `${{ github.event.pull_request.number }}` |

### 📊 Configurações de Análise

| Parâmetro       | Padrão  | Descrição                            |
| --------------- | ------- | ------------------------------------ |
| `analyze_limit` | `10`    | Número máximo de arquivos a analisar |
| `model`         | `gpt-5` | Modelo de IA a ser usado             |

**Modelos suportados:**

- **OpenAI**: `gpt-4`, `gpt-4-turbo`, `gpt-5`
- **Claude**: `claude-3-sonnet-20240229`, `claude-3-opus-20240229`

### 🚫 Configurações de Ignore

| Parâmetro             | Descrição                    | Exemplo             |
| --------------------- | ---------------------------- | ------------------- |
| `ignore_file_content` | Padrões regex (um por linha) | `^src/__tests__/`   |
| `ignore_file_path`    | Caminho do arquivo de ignore | `.ai-review-ignore` |

---

## 📁 Arquivo de Ignore

Crie um arquivo `.ai-review-ignore` na raiz do seu projeto para ignorar arquivos específicos:

```gitignore
# Arquivos de teste
**/*.test.js
**/*.spec.js
**/__tests__/

# Dependências
node_modules/
vendor/

# Arquivos de configuração
*.json
*.lock
*.log

# Arquivos temporários
*.tmp
*.cache
```

---

## 🎯 Exemplos de Uso

### Configuração Básica

```yaml
- uses: filipepiresg/ai-code-review-action@v1
  with:
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    repository: ${{ github.repository }}
    pr_number: ${{ github.event.pull_request.number }}
```

### Configuração Avançada

```yaml
- uses: filipepiresg/ai-code-review-action@v1
  with:
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    claudeai_api_key: ${{ secrets.CLAUDEAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    repository: ${{ github.repository }}
    pr_number: ${{ github.event.pull_request.number }}
    analyze_limit: 15
    model: gpt-4-turbo
    ignore_file_path: |
      ^src/__tests__/
      ^docs/
      \.md$
    ignore_file_path: ".ai-review-ignore"
```

### Usando Apenas Claude

```yaml
- uses: filipepiresg/ai-code-review-action@v1
  with:
    claudeai_api_key: ${{ secrets.CLAUDEAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    repository: ${{ github.repository }}
    pr_number: ${{ github.event.pull_request.number }}
    model: claude-3-opus-20240229
```

---

## 📊 Exemplo de Saída

A Action gera comentários estruturados no PR com análises detalhadas:

```markdown
# 🤖 Revisão automática com LLM

## 📄 src/auth/login.py

### Vulnerabilidades

- ⚠️ **SQL Injection**: Query na linha 45 usa concatenação direta
- 🔐 **Credenciais**: Senha sendo logada em texto plano (linha 23)

### Melhorias sugeridas

- ✅ Use prepared statements para queries SQL
- ✅ Implemente hash de senhas com bcrypt
- ✅ Adicione rate limiting para tentativas de login

### Boas práticas

- 📝 Código bem estruturado e legível
- 🧪 Falta cobertura de testes para casos de erro
- 📚 Documentação de funções poderia ser mais detalhada

### Resumo final

- 🔴 2 vulnerabilidades críticas encontradas
- 🟡 3 melhorias recomendadas
- ✅ Estrutura geral do código está boa
```

---

## 🔧 Desenvolvimento

### Estrutura do Projeto

```
ai-code-review-action/
├── action.yml              # Configuração da GitHub Action
├── scripts/
│   ├── ai_review_pr.py     # Script principal de análise
│   └── release.sh          # Script de release automatizado
└── README.md               # Documentação
```

### Scripts Disponíveis

#### `scripts/ai_review_pr.py`

Script principal que realiza a análise de código usando IA.

**Funcionalidades:**

- Carregamento de configurações via variáveis de ambiente
- Filtragem de arquivos baseada em extensões e padrões de ignore
- Chunking automático para arquivos grandes
- Análise com OpenAI ou Claude
- Publicação de comentários no PR

#### `scripts/release.sh`

Script para automatizar releases da GitHub Action.

**Uso:**

```bash
# Release básica
./scripts/release.sh v1.2.0

# Release com alias latest
./scripts/release.sh v1.2.0 true
```

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🙏 Agradecimentos

- [OpenAI](https://openai.com/) pela API GPT
- [Anthropic](https://www.anthropic.com/) pela API Claude
- [PyGithub](https://pygithub.readthedocs.io/) pela integração com GitHub
- Comunidade open source por inspiração e feedback

---

## 📞 Suporte

- 🐛 **Bugs**: [Abra uma issue](https://github.com/filipepiresg/ai-code-review-action/issues)
- 💡 **Sugestões**: [Discussions](https://github.com/filipepiresg/ai-code-review-action/discussions)
- 📧 **Contato**: [@filipepiresg](https://github.com/filipepiresg)

---

<div align="center">
  <p>Feito com ❤️ por <a href="https://github.com/filipepiresg">Filipe Pires</a></p>
  <p>⭐ Se este projeto te ajudou, considere dar uma estrela!</p>
</div>
