import os
import sys
import openai
from github import Github
import textwrap

# ===============================
# 🔧 CONFIGURAÇÕES INICIAIS
# ===============================
REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("GITHUB_PR_NUMBER")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
ANALYZE_LIMIT = int(os.getenv("ANALYZE_LIMIT", "10"))

openai.api_key = OPENAI_API_KEY

# ===============================
# ⚙️ FUNÇÕES AUXILIARES
# ===============================
def log(msg):
    print(f"[AI-Review] {msg}")

def get_pull_request():
    """Obtém o PR e os arquivos alterados"""
    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(REPO)
    pr = repo.get_pull(int(PR_NUMBER))
    return pr

def get_changed_files(pr):
    """Retorna até N arquivos alterados e seu conteúdo"""
    changed_files = []
    for i, f in enumerate(pr.get_files()):
        if i >= ANALYZE_LIMIT:
            break
        if f.filename.endswith(('.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.kt', '.swift', '.go', '.rs')):
            changed_files.append({
                "filename": f.filename,
                "patch": f.patch or "",
                "contents": get_file_content(f.filename, pr.base.repo)
            })
    return changed_files

def get_file_content(filename, repo):
    """Busca o conteúdo completo do arquivo na branch base"""
    try:
        file_content = repo.get_contents(filename).decoded_content.decode('utf-8')
        return file_content
    except Exception:
        return ""

def chunk_code(content, max_chars=8000):
    """Divide código em blocos menores para evitar limite de tokens"""
    lines = content.splitlines()
    chunk, chunks = [], []
    size = 0
    for line in lines:
        size += len(line)
        chunk.append(line)
        if size >= max_chars:
            chunks.append("\n".join(chunk))
            chunk, size = [], 0
    if chunk:
        chunks.append("\n".join(chunk))
    return chunks

def analyze_code_with_ai(filename, content):
    """Envia o código para análise do GPT-5"""
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
        f
