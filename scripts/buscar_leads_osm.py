#!/usr/bin/env python3
"""
Sourcing de leads via OpenStreetMap (Overpass API) — alternativa GRÁTIS
ao Google Places. Sem chave, sem billing, sem cartão.

Busca negócios por categoria dentro de uma cidade e grava no formato que o
qualificar_leads.py consome. O OSM diz se o negócio tem site cadastrado —
e quem não tem é exatamente o lead quente.

Uso:
    python buscar_leads_osm.py --cidade "Taubaté" --categorias cafe,padaria,restaurante
    python buscar_leads_osm.py --cidade "Taubaté" --buscas dados/buscas-osm.csv
    python buscar_leads_osm.py --cidade "Taubaté" --area-id 298561 --categorias cafe

Cobertura do OSM é menor que a do Google, mas é de graça e ilimitada —
ótima pra primeira garimpada. O que faltar de site, o qualificador confere.

Sem dependências externas: usa só a biblioteca padrão do Python 3.
"""

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

OVERPASS = "https://overpass-api.de/api/interpreter"
COLS = ["nome", "tipo", "setor", "cidade", "telefone", "email", "site",
        "nota", "avaliacoes", "instagram", "linkedin"]

# categoria amigável -> (tags OSM, rótulo do setor, tipo padrão)
CATEGORIAS = {
    "cafe": ([("amenity", "cafe")], "Cafeteria", "b2c"),
    "cafeteria": ([("amenity", "cafe")], "Cafeteria", "b2c"),
    "restaurante": ([("amenity", "restaurant")], "Restaurante", "b2c"),
    "lanchonete": ([("amenity", "fast_food")], "Lanchonete", "b2c"),
    "bar": ([("amenity", "bar"), ("amenity", "pub")], "Bar", "b2c"),
    "padaria": ([("shop", "bakery")], "Padaria", "b2c"),
    "mercado": ([("shop", "supermarket"), ("shop", "convenience")], "Mercado", "b2c"),
    "pet": ([("shop", "pet")], "Pet shop", "b2c"),
    "petshop": ([("shop", "pet")], "Pet shop", "b2c"),
    "veterinaria": ([("amenity", "veterinary")], "Veterinária", "b2c"),
    "salao": ([("shop", "hairdresser"), ("shop", "beauty")], "Salão de beleza", "b2c"),
    "barbearia": ([("shop", "hairdresser")], "Barbearia", "b2c"),
    "academia": ([("leisure", "fitness_centre")], "Academia", "b2c"),
    "clinica": ([("amenity", "clinic"), ("healthcare", "clinic")], "Clínica", "b2c"),
    "odontologia": ([("amenity", "dentist"), ("healthcare", "dentist")], "Odontologia", "b2c"),
    "dentista": ([("amenity", "dentist")], "Odontologia", "b2c"),
    "farmacia": ([("amenity", "pharmacy")], "Farmácia", "b2c"),
    "oficina": ([("shop", "car_repair")], "Oficina", "b2c"),
    "autopecas": ([("shop", "car_parts")], "Autopeças", "b2b"),
    "hotel": ([("tourism", "hotel")], "Hotel", "b2c"),
    # B2B no OSM é fraco — pra isso, prefira o filtrar_cnpj.py
    "advocacia": ([("office", "lawyer")], "Advocacia", "b2b"),
    "contabilidade": ([("office", "accountant")], "Contabilidade", "b2b"),
    "imobiliaria": ([("office", "estate_agent")], "Imobiliária", "b2b"),
}


def montar_selecionados(categorias, buscas_csv, tipo_padrao):
    """Retorna lista de (tag_k, tag_v, setor, tipo)."""
    sel = []
    pares = []  # (categoria, tipo_override)
    if buscas_csv:
        with open(buscas_csv, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                row = {(k or "").strip().lower(): (v or "").strip()
                       for k, v in row.items()}
                if row.get("categoria"):
                    pares.append((row["categoria"].lower(), row.get("tipo", "")))
    else:
        pares = [(c.strip().lower(), "") for c in categorias.split(",") if c.strip()]

    for cat, tipo_ov in pares:
        if cat not in CATEGORIAS:
            print(f"  ! categoria desconhecida: '{cat}' (ignorada). "
                  f"Conhecidas: {', '.join(sorted(CATEGORIAS))}")
            continue
        tags, setor, tipo_def = CATEGORIAS[cat]
        tipo = tipo_ov or tipo_def or tipo_padrao
        for k, v in tags:
            sel.append((k, v, setor, tipo))
    return sel


def montar_query(sel, cidade, area_id):
    if area_id:
        area = f"area({3600000000 + int(area_id)})->.a;"
    else:
        cid = cidade.replace('"', '\\"')
        area = f'area["name"="{cid}"]["admin_level"="8"]->.a;'
    corpo = "\n".join(f'  nwr["{k}"="{v}"](area.a);' for k, v, _, _ in sel)
    return f"[out:json][timeout:90];\n{area}\n(\n{corpo}\n);\nout center tags;"


def parse_elementos(data, cidade, sel):
    """Converte resposta Overpass -> linhas no formato do qualificador."""
    setor_por_tag = {(k, v): (setor, tipo) for k, v, setor, tipo in sel}
    vistos, linhas = set(), []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        nome = tags.get("name", "").strip()
        if not nome:
            continue
        chave = (el.get("type"), el.get("id"))
        if chave in vistos:
            continue
        vistos.add(chave)
        # casa o elemento com a categoria pedida
        setor, tipo = "", "b2c"
        for (k, v), (s, t) in setor_por_tag.items():
            if tags.get(k) == v:
                setor, tipo = s, t
                break
        site = tags.get("website") or tags.get("contact:website") or ""
        tel = tags.get("phone") or tags.get("contact:phone") or ""
        email = tags.get("email") or tags.get("contact:email") or ""
        insta = tags.get("contact:instagram") or ""
        cidade_el = tags.get("addr:city") or cidade
        linhas.append({
            "nome": nome, "tipo": tipo, "setor": setor, "cidade": cidade_el,
            "telefone": tel, "email": email, "site": site,
            "nota": "", "avaliacoes": "", "instagram": insta, "linkedin": "",
        })
    return linhas


def consultar(query):
    dados = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        OVERPASS, data=dados,
        headers={"User-Agent": "MazyOS-OSM-Sourcing/1.0"})
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as e:
            if tentativa == 2:
                raise
            print(f"  ... Overpass ocupado ({e}); tentando de novo em 5s")
            time.sleep(5)


def main():
    ap = argparse.ArgumentParser(description="Sourcing de leads via OpenStreetMap")
    ap.add_argument("--cidade", required=True, help='ex: "Taubaté"')
    ap.add_argument("--categorias", default="", help="ex: cafe,padaria,restaurante")
    ap.add_argument("--buscas", help="CSV com colunas categoria,tipo")
    ap.add_argument("--tipo", default="b2c", help="tipo padrão (b2c/b2b)")
    ap.add_argument("--area-id", default="", help="id de relação OSM (precisão)")
    ap.add_argument("--saida", default="dados/prospects.csv")
    ap.add_argument("--append", action="store_true")
    args = ap.parse_args()

    sel = montar_selecionados(args.categorias, args.buscas, args.tipo)
    if not sel:
        sys.exit("Nenhuma categoria válida. Use --categorias ou --buscas.")

    query = montar_query(sel, args.cidade, args.area_id)
    print(f"Consultando OpenStreetMap: {args.cidade} "
          f"({len({s[2] for s in sel})} categorias)...")
    data = consultar(query)
    linhas = parse_elementos(data, args.cidade, sel)

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    modo = "a" if (args.append and saida.exists()) else "w"
    with open(saida, modo, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if modo == "w":
            w.writeheader()
        w.writerows(linhas)

    sem_site = sum(1 for l in linhas if not l["site"])
    print(f"\n{len(linhas)} leads gravados em {saida} "
          f"({sem_site} sem site = oportunidade).")
    print("Próximo passo: python scripts/qualificar_leads.py " + str(saida))


if __name__ == "__main__":
    main()
