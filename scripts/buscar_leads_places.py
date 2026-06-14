#!/usr/bin/env python3
"""
Sourcing de leads via Google Places — Etapa 2 (B2C local + B2B).

Busca empresas no Google Maps por consulta ("cafeteria em Taubaté",
"contabilidade em Taubaté", "distribuidora em São José dos Campos") e
despeja no CSV no formato que o qualificar_leads.py consome — já trazendo
se a empresa tem site, telefone, nota e nº de avaliações.

Pré-requisito:
    - Conta no Google Cloud com a "Places API" ativada (free tier ~US$200/mês)
    - Chave de API na variável de ambiente GOOGLE_MAPS_API_KEY
      (ou passar com --key)

Uso:
    export GOOGLE_MAPS_API_KEY="sua_chave"
    # plano de busca num CSV (colunas: consulta, tipo, setor)
    python buscar_leads_places.py --buscas dados/buscas-exemplo.csv
    # ou uma busca avulsa
    python buscar_leads_places.py "cafeteria em Taubaté" --tipo b2c --setor Cafeteria

Saída:
    dados/prospects.csv  (use --saida pra mudar; --append pra acrescentar)
    -> depois é só rodar: python scripts/qualificar_leads.py dados/prospects.csv

Sem dependências externas: usa só a biblioteca padrão do Python 3.
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

TEXT_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"
DETAIL_FIELDS = "name,website,formatted_phone_number,rating,user_ratings_total,formatted_address"
COLS = ["nome", "tipo", "setor", "cidade", "telefone", "site",
        "nota", "avaliacoes", "instagram", "linkedin"]


def get_json(url, params):
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(url + "?" + qs,
                                 headers={"User-Agent": "MazyOS-Sourcing/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def cidade_da_consulta(consulta, endereco=""):
    if " em " in consulta.lower():
        return consulta[consulta.lower().rindex(" em ") + 4:].strip()
    # fallback: penúltimo campo do endereço formatado
    partes = [p.strip() for p in endereco.split(",") if p.strip()]
    return partes[-2] if len(partes) >= 2 else ""


def buscar(consulta, key, max_paginas):
    """Text Search paginado -> lista de place_ids (até 20 por página)."""
    ids, params = [], {"query": consulta, "key": key,
                       "language": "pt-BR", "region": "br"}
    for pagina in range(max_paginas):
        data = get_json(TEXT_SEARCH, params)
        status = data.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            print(f"  ! API: {status} — {data.get('error_message','')}")
            break
        for res in data.get("results", []):
            ids.append(res["place_id"])
        token = data.get("next_page_token")
        if not token:
            break
        time.sleep(2)  # token leva ~2s pra ficar válido
        params = {"pagetoken": token, "key": key}
    return ids


def detalhes(place_id, key):
    data = get_json(DETAILS, {"place_id": place_id, "fields": DETAIL_FIELDS,
                             "key": key, "language": "pt-BR"})
    if data.get("status") != "OK":
        return None
    return data.get("result", {})


def carregar_plano(args):
    """Retorna lista de (consulta, tipo, setor)."""
    if args.buscas:
        plano = []
        with open(args.buscas, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                row = {(k or "").strip().lower(): (v or "").strip()
                       for k, v in row.items()}
                if row.get("consulta"):
                    plano.append((row["consulta"],
                                  row.get("tipo", "b2c") or "b2c",
                                  row.get("setor", "")))
        return plano
    if args.consulta:
        return [(args.consulta, args.tipo, args.setor)]
    sys.exit("Informe --buscas <arquivo.csv> ou uma consulta avulsa.")


def main():
    ap = argparse.ArgumentParser(description="Sourcing de leads via Google Places")
    ap.add_argument("consulta", nargs="?", help='ex: "cafeteria em Taubaté"')
    ap.add_argument("--buscas", help="CSV com colunas consulta,tipo,setor")
    ap.add_argument("--tipo", default="b2c", help="b2c ou b2b (consulta avulsa)")
    ap.add_argument("--setor", default="", help="rótulo do setor (consulta avulsa)")
    ap.add_argument("--saida", default="dados/prospects.csv")
    ap.add_argument("--append", action="store_true", help="acrescenta ao CSV")
    ap.add_argument("--paginas", type=int, default=3, help="páginas/busca (máx 3)")
    ap.add_argument("--key", default=os.environ.get("GOOGLE_MAPS_API_KEY", ""))
    args = ap.parse_args()

    if not args.key:
        sys.exit("Defina GOOGLE_MAPS_API_KEY (ou use --key). "
                 "Crie a chave no Google Cloud com a Places API ativada.")

    plano = carregar_plano(args)
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)

    vistos, linhas = set(), []
    for consulta, tipo, setor in plano:
        print(f"Buscando: {consulta}  ({tipo})")
        ids = buscar(consulta, args.key, max(1, min(args.paginas, 3)))
        print(f"  {len(ids)} resultados; puxando detalhes...")
        for pid in ids:
            if pid in vistos:
                continue
            vistos.add(pid)
            d = detalhes(pid, args.key)
            if not d:
                continue
            linhas.append({
                "nome": d.get("name", ""),
                "tipo": tipo,
                "setor": setor or consulta.split(" em ")[0],
                "cidade": cidade_da_consulta(consulta,
                                             d.get("formatted_address", "")),
                "telefone": d.get("formatted_phone_number", ""),
                "site": d.get("website", ""),
                "nota": d.get("rating", ""),
                "avaliacoes": d.get("user_ratings_total", ""),
                "instagram": "", "linkedin": "",
            })

    modo = "a" if (args.append and saida.exists()) else "w"
    with open(saida, modo, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if modo == "w":
            w.writeheader()
        w.writerows(linhas)

    com_site = sum(1 for l in linhas if l["site"])
    print(f"\n{len(linhas)} leads gravados em {saida} "
          f"({len(linhas)-com_site} sem site = oportunidade).")
    print("Próximo passo: python scripts/qualificar_leads.py " + str(saida))


if __name__ == "__main__":
    main()
