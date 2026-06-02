"""Analisa os assuntos classificados como DESCONHECIDO para identificar
padroes que escaparam dos tokens atuais.
"""
import sys, re
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_conn

with get_conn() as conn:
    rows = conn.execute("""
        SELECT codigo_amostra, assunto_original FROM amostras
        WHERE processo='DESCONHECIDO'
        ORDER BY data_recebimento_email DESC
    """).fetchall()

print(f"Total DESCONHECIDOS: {len(rows)}")
print()

# Extrai a parte do assunto APOS o codigo PM/EC/AB
regex_codigo = re.compile(r"\b(PM|EC|AB|PR)\d+\b")

palavras_chave = Counter()
exemplos_por_padrao = {}

for r in rows:
    subj = r["assunto_original"] or ""
    m = regex_codigo.search(subj)
    if not m:
        continue
    apos = subj[m.end():].strip(" -:")
    # Pega 2-3 primeiras palavras como "padrao"
    palavras = re.split(r"[\s,/\-]+", apos)
    palavras = [p.strip(".,;:") for p in palavras if p.strip(".,;:")]
    if not palavras:
        continue
    chave = " ".join(palavras[:3]).upper()[:40]
    palavras_chave[chave] += 1
    if chave not in exemplos_por_padrao:
        exemplos_por_padrao[chave] = subj

print(f"=== Top 30 padroes nao reconhecidos ===")
print()
for padrao, n in palavras_chave.most_common(30):
    exemplo = exemplos_por_padrao.get(padrao, "")[:80]
    print(f"  [{n:>3}x] {padrao!r:50s} ex: {exemplo}")
