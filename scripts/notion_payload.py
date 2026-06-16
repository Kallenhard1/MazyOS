#!/usr/bin/env python3
"""Gera o payload de páginas pro Notion (create-pages) a partir do pipeline.csv,
pulando leads que já existem no board. Saída: JSON em saidas/notion-payload.json.

Uso: python scripts/notion_payload.py "Nome Já Existe" "Outro Nome" ...
"""
import csv, json, sys
from pathlib import Path

ja_existem = {n.strip().lower() for n in sys.argv[1:]}

pages = []
with open("crm/pipeline.csv", newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        nome = (r.get("nome") or "").strip()
        if not nome or nome.lower() in ja_existem:
            continue
        props = {"Empresa": nome}
        if r.get("status"):    props["Status"] = r["status"].strip()
        if r.get("tipo"):      props["Tipo"] = r["tipo"].strip()
        if r.get("setor"):     props["Setor"] = r["setor"].strip()
        if r.get("cidade"):    props["Cidade"] = r["cidade"].strip()
        if r.get("telefone"):  props["Telefone"] = r["telefone"].strip()
        if r.get("email"):     props["Email"] = r["email"].strip()
        if r.get("site"):      props["Site"] = r["site"].strip()
        if r.get("score"):
            try: props["Score"] = float(r["score"])
            except ValueError: pass
        if r.get("proximo_followup"):
            props["date:Follow-up:start"] = r["proximo_followup"].strip()
        if r.get("canal"):     props["Canal"] = r["canal"].strip()
        if r.get("notas"):     props["Notas"] = r["notas"].strip()
        pages.append({"properties": props})

out = Path("saidas/notion-payload.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{len(pages)} páginas novas -> {out}")
