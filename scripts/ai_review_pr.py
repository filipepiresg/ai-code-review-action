"""
🤖 AI Code Review Script
========================

Este script realiza análise automática de código usando IA (OpenAI GPT ou Anthropic Claude).
Ele analisa arquivos modificados em Pull Requests e publica feedback automaticamente.

Funcionalidades:
- Suporte a múltiplas linguagens de programação
- Análise de segurança e vulnerabilidades
- Detecção de más práticas e sugestões de melhoria
- Sistema de ignore configurável (regex e arquivo)
- Limite configurável de arquivos analisados
- Chunking automático para arquivos grandes

Autor: Filipe Pires
Versão: 1.0.0
"""

import hashlib
import json
import os
import pathspec
import re
import sys
import textwrap

# ===============================
# 🔧 CONFIGURAÇÕES INICIAIS
# ===============================
# Carrega variáveis de ambiente necessárias para execução
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")      # Chave da API OpenAI
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")      # Chave da API Anthropic Claude
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5")     # Modelo de IA a ser usado

# Configurações do GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")          # Token para interação com GitHub API
REPO = os.getenv("GITHUB_REPOSITORY")             # Repositório no formato owner/repo
PR_NUMBER = os.getenv("GITHUB_PR_NUMBER")         # Número do Pull Request

# Configurações de análise
ANALYZE_LIMIT = int(os.getenv("ANALYZE_LIMIT", "10"))  # Máximo de arquivos a analisar
IGNORE_FILE_CONTENT = os.getenv("IGNORE_FILE_CONTENT", "")     # Padrões regex para ignorar
IGNORE_FILE_PATH = os.getenv("IGNORE_FILE_PATH") or  ".ai-review-ignore"   # Caminho do arquivo de ignore

# Extensões de arquivos suportadas para análise
SUPPORTED_EXTENSIONS = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cs", ".php",
    ".rb", ".go", ".swift", ".kt", ".rs"
)

# Diretório base do cache persistente
CACHE_DIR = os.path.join(os.getenv("GITHUB_WORKSPACE", "."), "ai_review_cache")
IGNORE_CACHE_PATH = os.path.join(CACHE_DIR, "ignore_rules.json")
os.makedirs(CACHE_DIR, exist_ok=True)

# ===============================
# ⚙️ FUNÇÕES AUXILIARES
# ===============================

def log(msg):
    """
    Exibe mensagens de log com prefixo identificador.
    
    Args:
        msg (str): Mensagem a ser exibida
    """
    print(f"[AI-Review] {msg}")

def shorten_multiline(text, width, placeholder=' [...]'):
    """
    Encurta um texto de múltiplas linhas para que o texto total caiba em 'width',
    preservando as quebras de linha existentes.

    Args:
        text (str): O texto de entrada.
        width (int): O número máximo de caracteres que o texto de saída pode ter.
        placeholder (str): O espaço reservado para indicar que o texto foi encurtado.

    Returns:
        str: O texto encurtado.
    """
    if not isinstance(text, str):
        raise TypeError("O argumento 'text' deve ser uma string.")

    if len(text) <= width:
        return text

    # Trata as quebras de linha existentes
    lines = text.splitlines()
    output = []
    current_length = 0

    # Adiciona a primeira linha (ou parte dela) até o limite
    # e continua com as demais linhas se houver espaço
    for line in lines:
        if current_length + len(line) <= width - len(placeholder):
            output.append(line)
            current_length += len(line) + 1  # +1 para a quebra de linha
        else:
            remaining_width = width - current_length - len(placeholder)
            if remaining_width > 0:
                output.append(line[:remaining_width])
            # Adiciona o espaço reservado e interrompe
            output.append(placeholder)
            break
    
    return "\n".join(output)
    
def get_file_hash(content: str):
    """Gera hash único de um arquivo (SHA-256)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_ignore_cache():
    if os.path.exists(IGNORE_CACHE_PATH):
        with open(IGNORE_CACHE_PATH, "r") as f:
            return json.load(f)
    return None

def save_ignore_cache(data):
    with open(IGNORE_CACHE_PATH, "w") as f:
        json.dump(data, f)

def load_cache(file_hash: str):
    """Carrega resultado de cache se existir."""
    path = os.path.join(CACHE_DIR, f"{file_hash}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_cache(file_hash: str, data: dict):
    """Salva resultado da análise em cache."""
    path = os.path.join(CACHE_DIR, f"{file_hash}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_ignore_patterns():
    """
    Carrega padrões de ignore de um arquivo (formato .gitignore).
    
    Returns:
        list: Lista de padrões glob para ignorar arquivos
    """
    patterns = []
    workspace = os.getenv("GITHUB_WORKSPACE", ".")  # Diretório raiz do repositório
    if IGNORE_FILE_PATH:
        ignore_path = os.path.join(workspace, IGNORE_FILE_PATH)
        if os.path.exists(ignore_path):
            log(f"📄 Carregando padrões de ignore: {ignore_path}")
            with open(ignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    patterns.append(line)
        else:
            log(f"⚠️ Arquivo de ignore não encontrado: {ignore_path}")
    separator_comma_space = ", "
    log(f"  └── Arquivo regex ignoradas: {separator_comma_space.join(patterns)}")
    return patterns

def compile_regex_patterns():
    """
    Compila padrões regex passados via variável de ambiente.
    
    Returns:
        list: Lista de objetos regex compilados para ignorar arquivos
    """
    regex_list = []
    if IGNORE_FILE_CONTENT.strip():
        for line in IGNORE_FILE_CONTENT.strip().splitlines():
            pattern = line.strip()
            if not pattern:
                continue
            try:
                regex_list.append(re.compile(pattern))
            except re.error as e:
                log(f"⚠️ Regex inválida ignorada: {pattern} ({e})")
    separator_comma_space = ", "
    log(f"  └── Regex ignoradas: {separator_comma_space.join(regex_list)}")
    return regex_list

def should_ignore(filename, ignore_globs, ignore_regex):
    """
    Verifica se um arquivo deve ser ignorado baseado nos padrões configurados.
    
    Args:
        filename (str): Caminho do arquivo a verificar
        ignore_globs (list): Lista de padrões glob para ignorar
        ignore_regex (list): Lista de regex compiladas para ignorar
        
    Returns:
        bool: True se o arquivo deve ser ignorado, False caso contrário
    """
    # Cria o objeto pathspec
    spec_globs = pathspec.PathSpec.from_lines("gitwildmatch", ignore_globs)
    spec_regex = pathspec.PathSpec.from_lines("gitwildmatch", ignore_regex)
    if spec_globs.match_file(filename) or spec_regex.match_file(filename):
        return True
    return False

def get_pull_request():
    """
    Obtém o objeto Pull Request do GitHub.
    
    Returns:
        github.PullRequest.PullRequest: Objeto do PR para análise
    """
    from github import Auth, Github

    auth = Auth.Token(GITHUB_TOKEN)
    gh = Github(auth=auth)
    repo = gh.get_repo(REPO)
    return repo.get_pull(int(PR_NUMBER))

def get_file_content(filename, repo):
    """
    Obtém o conteúdo de um arquivo do repositório.
    
    Args:
        filename (str): Caminho do arquivo
        repo: Objeto do repositório GitHub
        
    Returns:
        str: Conteúdo do arquivo em UTF-8, ou string vazia em caso de erro
    """
    try:
        return repo.get_contents(filename).decoded_content.decode("utf-8")
    except Exception:
        return ""

def chunk_code(content, max_chars=8000):
    """
    Divide código em blocos menores para evitar limite de tokens das APIs.
    
    Args:
        content (str): Conteúdo do código a ser dividido
        max_chars (int): Número máximo de caracteres por chunk
        
    Returns:
        list: Lista de strings contendo chunks do código
    """
    lines = content.splitlines()
    chunks, current, size = [], [], 0
    for line in lines:
        size += len(line)
        current.append(line)
        if size >= max_chars:
            chunks.append("\n".join(current))
            current, size = [], 0
    if current:
        chunks.append("\n".join(current))
    return chunks

# ===============================
# 🤖 CLIENTE DE IA DINÂMICO
# ===============================

def call_openai(prompt, code_chunk):
    """
    Chama a API da OpenAI para análise de código.
    
    Args:
        prompt (str): Prompt de análise para o modelo
        code_chunk (str): Bloco de código a ser analisado
        
    Returns:
        str: Resposta do modelo OpenAI com análise do código
    """
    import openai
    openai.api_key = OPENAI_API_KEY
    response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "Você é um engenheiro de software e segurança."},
            {"role": "user", "content": f"{prompt}\n\n{code_chunk}"}
        ],
        temperature=0.3,  # Baixa temperatura para respostas mais consistentes
    )
    return response.choices[0].message.content.strip()

def call_claude(prompt, code_chunk):
    """
    Chama a API da Anthropic Claude para análise de código.
    
    Args:
        prompt (str): Prompt de análise para o modelo
        code_chunk (str): Bloco de código a ser analisado
        
    Returns:
        str: Resposta do modelo Claude com análise do código
    """
    from anthropic import Anthropic
    client = Anthropic(api_key=CLAUDE_API_KEY)
    response = client.messages.create(
        model=MODEL_NAME if MODEL_NAME.startswith("claude") else "claude-3-sonnet-20240229",
        max_tokens=2000,  # Limite de tokens para resposta
        messages=[
            {"role": "user", "content": f"{prompt}\n\n{code_chunk}"}
        ]
    )
    return response.content[0].text.strip()

def analyze_code(filename, content):
    file_hash = get_file_hash(content)
    cached = load_cache(file_hash)
    if cached:
        log(f"  └── ⚡ Arquivo cacheado")
        return cached["analysis"]

    """
    Analisa código usando IA (OpenAI ou Claude) com foco em segurança e boas práticas.
    
    Esta função divide o código em chunks para evitar limites de tokens e analisa
    cada parte separadamente, focando em:
    - Vulnerabilidades de segurança (SQLi, XSS, etc.)
    - Violações de boas práticas
    - Sugestões de melhoria
    - Observações gerais sobre qualidade
    
    Args:
        filename (str): Nome do arquivo sendo analisado
        content (str): Conteúdo do código a ser analisado
        
    Returns:
        str: Relatório de análise formatado em Markdown
    """
    prompt = f"""
Você é um especialista em análise de código e segurança. Analise o arquivo `{filename}` e responda em português, de forma organizada, com foco em:

1. **Problemas de segurança ou vulnerabilidades** (injeção, XSS, SQLi, credenciais, etc.);
2. **Boas práticas violadas** (complexidade, performance, organização);
3. **Sugestões de melhoria** (clareza, manutenção, eficiência);
4. **Observações gerais** (coerência, padrões, etc.).

Use o formato:

### 📄 {filename}
**Vulnerabilidades**
- ...
**Melhorias sugeridas**
- ...
**Boas práticas**
- ...
**Resumo final**
- ...
"""
    try:
        chunks = chunk_code(content)
        report = ""
        log(f"  └── 🧠 Arquivo sem cache")
        for chunk in chunks:
            if OPENAI_API_KEY:
                report += call_openai(prompt, chunk) + "\n\n"
            elif CLAUDE_API_KEY:
                report += call_claude(prompt, chunk) + "\n\n"
            else:
                raise ValueError("Nenhuma chave de LLM foi fornecida (openap_api_key ou claudeai_api_key).")
                
        save_cache(file_hash, {"filename": filename, "analysis": report})
        return report
    except Exception as e:
        log(f"⚠️ Erro ao analisar {filename}: {str(e)}")
        return None

def post_comment(pr, body):
    """
    Publica comentário no Pull Request com o relatório de análise.
    
    Args:
        pr: Objeto do Pull Request do GitHub
        body (str): Conteúdo do comentário a ser publicado
    """
    try:
        pr.create_issue_comment(body)
        log("💬 Comentário publicado no PR com sucesso.")
    except Exception as e:
        log(f"⚠️ Falha ao comentar no PR: {str(e)}")

# ===============================
# 🚀 EXECUÇÃO PRINCIPAL
# ===============================

if __name__ == "__main__":
    """
    Função principal que executa o processo completo de análise de código.
    
    Fluxo de execução:
    1. Validação de variáveis de ambiente
    2. Carregamento de padrões de ignore
    3. Obtenção do Pull Request
    4. Filtragem de arquivos modificados
    5. Análise de cada arquivo com IA
    6. Publicação do relatório no PR
    """
    
    # ===============================================
    # 🔍 DEBUG E VALIDAÇÃO INICIAL
    # ===============================================
    print("======== DEBUG VARS: ========")
    for var in ["GITHUB_REPOSITORY", "GITHUB_PR_NUMBER", "OPENAI_API_KEY","OPENAI_MODEL", "CLAUDE_API_KEY", "ANALYZE_LIMIT", "IGNORE_FILE_CONTENT", "IGNORE_FILE_PATH"]:
        print(f" - {var}={os.getenv(var)}")
    print("=============================")

    # Validação de variáveis obrigatórias do GitHub
    if not all([GITHUB_TOKEN, PR_NUMBER, REPO]):
        log("❌ Variáveis de ambiente faltando. Abortando.")
        sys.exit(1)

    # Validação de pelo menos uma chave de LLM
    if not any([OPENAI_API_KEY, CLAUDE_API_KEY]):
        log("❌ Nenhuma chave de LLM informada. Use openai_api_key ou claudeai_api_key.")
        sys.exit(1)

    # ===============================================
    # 📋 CARREGAMENTO DE CONFIGURAÇÕES
    # ===============================================
    ignore_globs = load_ignore_patterns()      # Padrões glob do arquivo
    ignore_regex = compile_regex_patterns()   # Padrões regex da variável

    # ===============================================
    # 🔍 ANÁLISE DO PULL REQUEST
    # ===============================================
    pr = get_pull_request()
    log(f"🔍 Analisando PR #{PR_NUMBER}: {pr.title}")

    # ===============================================
    # 📁 FILTRAGEM DE ARQUIVOS MODIFICADOS
    # ===============================================
    changed_files = []
    for f in pr.get_files():
        # Limite de arquivos a analisar
        if len(changed_files) >= ANALYZE_LIMIT:
            break
            
        # Verifica se é uma extensão suportada
        if not f.filename.endswith(SUPPORTED_EXTENSIONS):
            continue
            
        # Verifica se deve ser ignorado
        if should_ignore(f.filename, ignore_globs, ignore_regex):
            log(f"🚫 Ignorado: {f.filename}")
            continue
            
        # Obtém conteúdo do arquivo
        content = get_file_content(f.filename, pr.base.repo)

        # Verifica se esse contéudo já foi cacheado
        file_hash = get_file_hash(content)
        cached = load_cache(file_hash)
        if cached is not None:
            log(f"🚫 Arquivo já avaliado: {f.filename}")
            continue

        changed_files.append((f.filename, content))

    # ===============================================
    # ✅ VALIDAÇÃO FINAL
    # ===============================================
    if not changed_files:
        log("⚠️ Nenhum arquivo elegível encontrado após filtros.")
        sys.exit(0)

    log(f"📦 {len(changed_files)} arquivos serão analisados usando {'OpenAI' if OPENAI_API_KEY else 'Claude'}.")

    # ===============================================
    # 🤖 ANÁLISE E GERAÇÃO DO RELATÓRIO
    # ===============================================
    full_report = ""
    for filename, content in changed_files:
        log(f"🔍 Analisando: {filename}")
        analysis = analyze_code(filename, content)
        if cached or analysis is None:
            continue
        full_report += f"## 📄 {filename}\n" + analysis + "\n---\n"

    # ===============================================
    # 💬 PUBLICAÇÃO DO RELATÓRIO
    # ===============================================
    # Trunca o relatório se exceder limite do GitHub (65.536 caracteres)
    if full_report:
        full_report = "# 🤖 Revisão automática com LLM\n\n" + full_report
        summary = shorten_multiline(full_report, 60000, placeholder="\n\n... [comentário truncado]")
        post_comment(pr, summary)
    else:
        log("⚠️ Nenhum report foi criado.")
