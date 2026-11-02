#!/usr/bin/env python3
"""Gera public/matematica/ a partir de conteudo/.

Sem dependências: só a biblioteca padrão do Python.

    python ferramentas/gerar.py

Organização de conteudo/:
    index.md                     capa (/matematica/)
    NN-slug/index.md             abertura de um estudo (/matematica/slug/)
    NN-slug/NN-parte.md          partes do estudo, em ordem (/matematica/slug/parte/)

O título de cada página é o primeiro "# " do arquivo. Os números NN só dão a ordem
e não entram no endereço.
"""
import html
import re
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTEUDO = RAIZ / "conteudo"
SAIDA = RAIZ / "public" / "matematica"
BASE = "/matematica/"
FIXOS = {"fontes", "estilo.css", "favicon.svg"}  # ficam em public/matematica/ e não são gerados


# ---------------------------------------------------------------- Markdown mínimo

def inline(t):
    t = html.escape(t, quote=False)
    codigos = []

    def guardar(m):
        codigos.append("<code>" + m.group(1) + "</code>")
        return "\x00%d\x00" % (len(codigos) - 1)

    t = re.sub(r"`([^`]+)`", guardar, t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: '<a href="%s">%s</a>' % (
        html.escape(m.group(2), quote=True), m.group(1)), t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<![\w])_(?!\s)(.+?)(?<!\s)_(?![\w])", r"<em>\1</em>", t)
    t = re.sub(r"\x00(\d+)\x00", lambda m: codigos[int(m.group(1))], t)
    return t


def ancora(texto, usadas):
    base = re.sub(r"<[^>]+>", "", texto).lower()
    for a, b in (("áàâãä", "a"), ("éèêë", "e"), ("íìîï", "i"), ("óòôõö", "o"), ("úùûü", "u"), ("ç", "c")):
        for c in a:
            base = base.replace(c, b)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "secao"
    a, n = base, 2
    while a in usadas:
        a, n = "%s-%d" % (base, n), n + 1
    usadas.add(a)
    return a


def celulas(linha):
    linha = linha.strip()
    if linha.startswith("|"):
        linha = linha[1:]
    if linha.endswith("|"):
        linha = linha[:-1]
    return [c.strip() for c in linha.split("|")]


def lista(linhas):
    """Listas com um nível de aninhamento (dois ou mais espaços)."""
    saida, pilha = [], []
    for ln in linhas:
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", ln)
        if not m:  # continuação do item anterior
            saida[-1] = saida[-1][:-5] + " " + inline(ln.strip()) + "</li>"
            continue
        nivel = 1 if len(m.group(1)) >= 2 else 0
        tag = "ol" if m.group(2)[0].isdigit() else "ul"
        while len(pilha) > nivel + 1:
            saida.append("</%s>" % pilha.pop())
            saida.append("</li>")
        if len(pilha) < nivel + 1:
            if pilha and saida and saida[-1].endswith("</li>"):
                saida[-1] = saida[-1][:-5]
            saida.append("<%s>" % tag)
            pilha.append(tag)
        saida.append("<li>" + inline(m.group(3)) + "</li>")
    while pilha:
        t = pilha.pop()
        saida.append("</%s>" % t)
        if pilha:
            saida.append("</li>")
    return "\n".join(saida)


def markdown(texto):
    linhas = texto.split("\n")
    saida, i, usadas, titulos = [], 0, set(), []
    eh_item = re.compile(r"^\s*([-*]|\d+\.)\s+")
    while i < len(linhas):
        ln = linhas[i]
        if not ln.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            n, t = len(m.group(1)), inline(m.group(2))
            if n == 1:
                saida.append("<h1>%s</h1>" % t)
            else:
                a = ancora(t, usadas)
                if n == 2:
                    titulos.append((a, t))
                saida.append('<h%d id="%s">%s</h%d>' % (n, a, t, n))
            i += 1
        elif re.match(r"^(-{3,}|\*{3,})\s*$", ln):
            saida.append("<hr>")
            i += 1
        elif ln.startswith(">"):
            bloco = []
            while i < len(linhas) and linhas[i].startswith(">"):
                bloco.append(linhas[i][1:].lstrip())
                i += 1
            saida.append("<blockquote>%s</blockquote>" % markdown("\n".join(bloco))[0])
        elif ln.lstrip().startswith("|") and i + 1 < len(linhas) and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", linhas[i + 1]):
            cab = celulas(ln)
            i += 2
            corpo = []
            while i < len(linhas) and linhas[i].lstrip().startswith("|"):
                corpo.append(celulas(linhas[i]))
                i += 1
            t = ['<div class="tabela"><table><thead><tr>']
            t += ["<th>%s</th>" % inline(c) for c in cab]
            t.append("</tr></thead><tbody>")
            for r in corpo:
                t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            saida.append("".join(t))
        elif eh_item.match(ln):
            bloco = []
            while i < len(linhas) and linhas[i].strip() and (eh_item.match(linhas[i]) or linhas[i].startswith("  ")):
                bloco.append(linhas[i])
                i += 1
            # um item pode continuar depois de uma linha em branco, se vier recuado
            saida.append(lista(bloco))
        else:
            bloco = []
            while i < len(linhas) and linhas[i].strip() and not re.match(r"^(#{1,4}\s|>|\s*\||\s*([-*]|\d+\.)\s)", linhas[i]):
                bloco.append(linhas[i].strip())
                i += 1
            saida.append("<p>%s</p>" % inline(" ".join(bloco)))
    return "\n".join(saida), titulos


# ---------------------------------------------------------------- Páginas

def titulo_de(texto):
    m = re.search(r"^#\s+(.*)$", texto, re.M)
    return m.group(1).strip() if m else "Sem título"


def sem_numero(nome):
    return re.sub(r"^\d+-", "", nome)


def texto_simples(t):
    return re.sub(r"[*_`]", "", t)


def pagina(titulo, corpo, trilha, rodape_nav="", lateral=""):
    trilha_html = ""
    if trilha:
        partes = ['<a href="%s">%s</a>' % (h, html.escape(texto_simples(t))) for h, t in trilha]
        trilha_html = '<nav class="trilha" aria-label="Você está em">%s</nav>\n' % " › ".join(partes)
    return """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>{titulo} · Matemática · Taioé</title>
<link rel="icon" href="{base}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{base}estilo.css">
</head>
<body>
<header class="topo">
  <a class="marca" href="/">Taioé</a>
  <nav><a href="{base}">Matemática</a><a href="/admin/">Admin</a></nav>
</header>
<main>
{trilha}<article class="texto">
{corpo}
</article>
{lateral}{rodape_nav}</main>
<footer class="rodape">Matemática · estudos para uma história da matemática · prévia de trabalho</footer>
</body>
</html>
""".format(titulo=html.escape(texto_simples(titulo)), base=BASE, trilha=trilha_html, corpo=corpo,
           lateral=lateral, rodape_nav=rodape_nav)


def nav_vizinhos(ant, prox):
    if not ant and not prox:
        return ""
    s = ['<nav class="vizinhos" aria-label="Partes">']
    s.append('<a class="ant" href="%s"><span>← anterior</span>%s</a>' % (ant[0], inline(ant[1])) if ant else "<span></span>")
    s.append('<a class="prox" href="%s"><span>próxima →</span>%s</a>' % (prox[0], inline(prox[1])) if prox else "<span></span>")
    s.append("</nav>\n")
    return "".join(s)


def sumario_partes(partes, atual=None):
    itens = []
    for n, (href, t) in enumerate(partes, 1):
        cls = ' class="atual" aria-current="page"' if href == atual else ""
        itens.append('<li%s><a href="%s"><span class="num">%d</span>%s</a></li>' % (cls, href, n, inline(t)))
    return '<ol class="partes">%s</ol>' % "".join(itens)


def escrever(destino, conteudo):
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding="utf-8")


def gerar():
    for p in SAIDA.iterdir():
        if p.name in FIXOS:
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()

    estudos = []
    for pasta in sorted(p for p in CONTEUDO.iterdir() if p.is_dir()):
        slug = sem_numero(pasta.name)
        abertura = (pasta / "index.md").read_text(encoding="utf-8")
        arquivos = sorted(p for p in pasta.glob("*.md") if p.name != "index.md")
        partes = []
        for a in arquivos:
            partes.append((BASE + slug + "/" + sem_numero(a.stem) + "/", titulo_de(a.read_text(encoding="utf-8")), a))
        estudos.append((slug, titulo_de(abertura), abertura, partes))

    # Capa
    capa = (CONTEUDO / "index.md").read_text(encoding="utf-8")
    corpo, _ = markdown(capa)
    lista_estudos = ['<ol class="estudos">']
    for n, (slug, t, _, partes) in enumerate(estudos, 1):
        extra = ("%d partes" % len(partes) if len(partes) > 1 else "1 parte") if partes else "uma página"
        lista_estudos.append('<li><a href="%s%s/"><span class="num">Estudo %d</span><strong>%s</strong><span class="apagado">%s</span></a></li>'
                             % (BASE, slug, n, inline(t), extra))
    lista_estudos.append("</ol>")
    corpo = corpo.replace("<p>{{estudos}}</p>", "\n".join(lista_estudos))
    escrever(SAIDA / "index.html", pagina("Matemática", corpo, []))

    # Estudos e partes
    for n, (slug, t, abertura, partes) in enumerate(estudos, 1):
        href_estudo = BASE + slug + "/"
        lista_p = [(h, tt) for h, tt, _ in partes]
        corpo, _ = markdown(abertura)
        if partes:
            corpo += '\n<h2 id="partes">Partes</h2>\n' + sumario_partes(lista_p)
        prox = lista_p[0] if lista_p else None
        escrever(SAIDA / slug / "index.html",
                 pagina(t, corpo, [(BASE, "Matemática")], nav_vizinhos(None, prox)))
        for k, (href, tt, arq) in enumerate(partes):
            corpo, _ = markdown(arq.read_text(encoding="utf-8"))
            corpo = '<p class="sobretitulo">Estudo %d · parte %d de %d</p>\n' % (n, k + 1, len(partes)) + corpo
            ant = lista_p[k - 1] if k > 0 else (href_estudo, "Abertura do estudo")
            prox = lista_p[k + 1] if k + 1 < len(lista_p) else None
            lateral = '<details class="sumario"><summary>Todas as partes</summary>%s</details>\n' % sumario_partes(lista_p, href)
            escrever(SAIDA / slug / sem_numero(arq.stem) / "index.html",
                     pagina(tt, corpo, [(BASE, "Matemática"), (href_estudo, t)], nav_vizinhos(ant, prox), lateral))

    escrever(SAIDA / "404.html", pagina("Página não encontrada",
             '<h1>Página não encontrada</h1>\n<p><a href="%s">Voltar à capa da Matemática</a></p>' % BASE, []))
    print("Gerado:", sum(1 for _ in SAIDA.rglob("*.html")), "páginas")


if __name__ == "__main__":
    gerar()
