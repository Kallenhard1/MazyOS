#!/usr/bin/env python3
"""
Sourcing B2B em escala — filtra os dados abertos de CNPJ da Receita Federal.

A Receita publica o cadastro completo de empresas do Brasil como CSVs
públicos e gratuitos. Este script filtra por setor (CNAE) + UF (+ município)
+ situação ativa e despeja no formato que o qualificar_leads.py consome.

Onde baixar os dados (gratuito):
    https://dadosabertos.rfb.gov.br/CNPJ/
    Baixe e descompacte numa pasta:
      - Estabelecimentos*  (endereço, CNAE, telefone, situação)
      - Empresas*          (razão social, porte)   [pro nome da empresa]
      - Municipios         (código -> nome)         [opcional, p/ cidade]

Layout (CSV ';' separado, latin-1, SEM cabeçalho) — colunas usadas:
    Estabelecimentos: 0 cnpj_basico, 4 nome_fantasia, 5 situacao(02=ativa),
        11 cnae_principal, 19 uf, 20 municipio(cod), 21 ddd1, 22 tel1,
        27 email
    Empresas: 0 cnpj_basico, 1 razao_social, 5 porte
    Municipios: 0 codigo, 1 nome

Uso:
    python filtrar_cnpj.py --dir ./cnpj --cnae 6920,6201 --uf SP \\
        --municipio "TAUBATE,SAO JOSE DOS CAMPOS" --limite 500
    # depois: python scripts/qualificar_leads.py dados/prospects.csv

Obs.: CNPJ não tem o site da empresa — todas saem com 'site' vazio. O
qualificador vai marcá-las como "sem_site"; rode primeiro o
buscar_leads_places (ou complete os sites) se quiser refinar antes.

Sem dependências externas: usa só a biblioteca padrão do Python 3.
"""

import argparse
import csv
import glob
import sys
from pathlib import Path

COLS = ["nome", "tipo", "setor", "cidade", "telefone", "site",
        "nota", "avaliacoes", "instagram", "linkedin"]
PORTE = {"01": "Microempresa", "03": "Pequeno porte", "05": "Demais"}


def achar(dir_, *padroes):
    for p in padroes:
        achados = glob.glob(str(Path(dir_) / p))
        if achados:
            return sorted(achados)
    return []


def ler_csv_rf(caminho):
    """Itera linhas de um CSV da Receita (latin-1, ';', sem header)."""
    with open(caminho, encoding="latin-1", newline="") as f:
        for row in csv.reader(f, delimiter=";", quotechar='"'):
            yield row


def carregar_municipios(arquivos):
    mapa = {}
    for arq in arquivos:
        for row in ler_csv_rf(arq):
            if len(row) >= 2:
                mapa[row[0].strip()] = row[1].strip()
    return mapa


def main():
    ap = argparse.ArgumentParser(description="Filtra dados abertos de CNPJ (B2B)")
    ap.add_argument("--dir", default="cnpj", help="pasta com os CSVs da Receita")
    ap.add_argument("--cnae", default="", help="prefixos CNAE, ex: 6920,6201")
    ap.add_argument("--uf", default="", help="UFs, ex: SP,MG")
    ap.add_argument("--municipio", default="",
                    help="nomes (com municipios.csv) ou códigos, separados por vírgula")
    ap.add_argument("--situacao", default="02", help="02=ativa (padrão)")
    ap.add_argument("--limite", type=int, default=0, help="máx. de leads (0=todos)")
    ap.add_argument("--saida", default="dados/prospects.csv")
    ap.add_argument("--tipo", default="b2b")
    args = ap.parse_args()

    cnaes = tuple(c.strip() for c in args.cnae.split(",") if c.strip())
    ufs = {u.strip().upper() for u in args.uf.split(",") if u.strip()}
    munis = {m.strip().upper() for m in args.municipio.split(",") if m.strip()}

    estab = achar(args.dir, "*ESTABELE*", "*Estabele*", "*estabele*")
    empres = achar(args.dir, "*EMPRESA*", "*Empresa*", "*empresa*")
    municf = achar(args.dir, "*MUNIC*", "*Munic*", "*munic*")
    if not estab:
        sys.exit(f"Nenhum arquivo de Estabelecimentos em '{args.dir}'. "
                 "Baixe de https://dadosabertos.rfb.gov.br/CNPJ/")

    mapa_muni = carregar_municipios(municf) if municf else {}
    # se filtrou por nome de município, traduz nome -> código
    cods_muni = set()
    if munis:
        nome2cod = {v.upper(): k for k, v in mapa_muni.items()}
        for m in munis:
            cods_muni.add(nome2cod.get(m, m))  # aceita código direto também

    # ---- Passo 1: filtra estabelecimentos ----
    print("Passo 1/2: filtrando estabelecimentos...")
    matches, basicos = [], set()
    for arq in estab:
        for row in ler_csv_rf(arq):
            if len(row) < 28:
                continue
            if args.situacao and row[5].strip() != args.situacao:
                continue
            if cnaes and not row[11].strip().startswith(cnaes):
                continue
            if ufs and row[19].strip().upper() not in ufs:
                continue
            if cods_muni and row[20].strip() not in cods_muni:
                continue
            ddd, tel = row[21].strip(), row[22].strip()
            telefone = f"({ddd}) {tel}" if ddd and tel else tel
            cod_mun = row[20].strip()
            matches.append({
                "cnpj_basico": row[0].strip(),
                "nome_fantasia": row[4].strip(),
                "setor": "CNAE " + row[11].strip(),
                "cidade": mapa_muni.get(cod_mun, cod_mun),
                "uf": row[19].strip().upper(),
                "telefone": telefone,
                "email": row[27].strip(),
            })
            basicos.add(row[0].strip())
            if args.limite and len(matches) >= args.limite:
                break
        if args.limite and len(matches) >= args.limite:
            break
    print(f"  {len(matches)} estabelecimentos batem nos filtros.")

    # ---- Passo 2: razão social via Empresas (só pros que bateram) ----
    razao = {}
    if empres:
        print("Passo 2/2: buscando razão social...")
        for arq in empres:
            for row in ler_csv_rf(arq):
                if len(row) >= 2 and row[0].strip() in basicos:
                    razao[row[0].strip()] = (row[1].strip(),
                                             PORTE.get(row[5].strip(), "")
                                             if len(row) > 5 else "")
    else:
        print("Passo 2/2: sem arquivo Empresas — usando nome fantasia.")

    # ---- Escreve no formato do qualificador ----
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for m in matches:
            nome = razao.get(m["cnpj_basico"], ("", ""))[0] or m["nome_fantasia"]
            if not nome:
                nome = "CNPJ " + m["cnpj_basico"]
            w.writerow({
                "nome": nome, "tipo": args.tipo, "setor": m["setor"],
                "cidade": f"{m['cidade']}/{m['uf']}" if m["cidade"] else m["uf"],
                "telefone": m["telefone"], "site": "",
                "nota": "", "avaliacoes": "",
                "instagram": "", "linkedin": "",
            })
    print(f"\n{len(matches)} leads B2B gravados em {saida}.")
    print("Próximo passo: python scripts/qualificar_leads.py " + str(saida))


if __name__ == "__main__":
    main()
