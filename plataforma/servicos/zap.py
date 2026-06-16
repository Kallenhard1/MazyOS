"""Links wa.me (click-to-chat) — abre o WhatsApp com a mensagem pré-preenchida.
Normaliza telefone BR: tira não-dígitos, remove o 0 de tronco e garante o DDI 55.
"""
import re
import urllib.parse


def numero(telefone):
    """Telefone bruto -> só dígitos no formato 55DDDNUMERO (ou '' se inválido)."""
    primeiro = re.split(r"[;/]", telefone or "")[0]
    d = re.sub(r"\D", "", primeiro).lstrip("0")
    if not d:
        return ""
    if d.startswith("55") and len(d) >= 12:
        return d
    if len(d) in (10, 11):  # DDD + número, sem DDI
        return "55" + d
    return d if d.startswith("55") else "55" + d


def link(telefone, mensagem=""):
    """URL wa.me com a mensagem pré-preenchida. '' se o telefone não der número."""
    n = numero(telefone)
    if not n:
        return ""
    url = f"https://wa.me/{n}"
    return url + ("?text=" + urllib.parse.quote(mensagem) if mensagem else "")
