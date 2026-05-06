import json
import re
from playwright.sync_api import sync_playwright

FUENTES = [
    {
        "url": "https://biblioteca.ua.es/es/estudia-y-aprende/cursos-de-formacion/cursos-programados-o-bajo-demanda.html",
        "lugar": "Punt BIU"
    }
]

CATEGORIAS = {
    "alternativas a google": "Alternativas a Google",
    "google avanzado": "Google avanzado",
    "bases de datos": "Bases de datos y recursos-e",
    "catálogo": "Catálogo BUA",
    "catalogo": "Catálogo BUA",
    "dialnet": "Dialnet y CSIC",
    "csic": "Dialnet y CSIC",
    "prensa digital": "Prensa digital",
    "hemeroteca": "Prensa digital",
    "repositorio": "Repositorios institucionales",
    "servicios virtuales": "Servicios virtuales BUA",
    "biblioteca en un click": "Servicios virtuales BUA",
    "técnicas y estrategias": "Técnicas de búsqueda",
    "estrategias de búsqueda": "Técnicas de búsqueda",
}

def detectar_categoria(titulo):
    titulo_lower = titulo.lower()
    for clave, categoria in CATEGORIAS.items():
        if clave in titulo_lower:
            return categoria
    return "Otros"

def extraer_cursos(page, url, lugar_default):
    page.goto(url, wait_until="networkidle", timeout=30000)
    html = page.content()

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    h2s = [h2.get_text(strip=True) for h2 in soup.find_all("h2")]
    print("H2s encontrados:", h2s)

    cursos = []

    for h2 in soup.find_all("h2"):
        if "escripci" not in h2.get_text():
            continue

        prev = h2.find_previous_sibling()
        if not prev:
            continue

        titulo = ""
        if prev.name == "p":
            strong = prev.find("strong")
            if strong:
                titulo = strong.get_text(strip=True)
        elif prev.name == "strong":
            titulo = prev.get_text(strip=True)

        if not titulo or len(titulo) < 10 or len(titulo.split()) < 3:
            continue

        desc = ""
        desc_tag = h2.find_next_sibling()
        if desc_tag and desc_tag.name == "p":
            desc = desc_tag.get_text(strip=True)

        ul = h2.find_next("ul")
        duracion = lugar = modalidad = ""
        url_inscripcion = url_formulario = ""

        if ul:
            for li in ul.find_all("li"):
                texto_li = li.get_text(" ", strip=True)
                texto_lower = texto_li.lower()
                if "duración" in texto_lower or "duracion" in texto_lower:
                    duracion = re.sub(r"(?i)duración\s*:?\s*", "", texto_li).strip()
                elif "lugar" in texto_lower:
                    lugar = re.sub(r"(?i)lugar\s*:?\s*", "", texto_li).strip()
                elif "modalidad" in texto_lower:
                    modalidad = re.sub(r"(?i)modalidad\s*:?\s*", "", texto_li).strip()
                elif "inscripci" in texto_lower:
                    enlaces = li.find_all("a", href=True)
                    for a in enlaces:
                        href = a["href"]
                        texto_a = a.get_text(strip=True).lower()
                        if "inscripci" in texto_a:
                            url_inscripcion = href
                        elif "formulario" in texto_a or "rellena" in texto_a:
                            url_formulario = href

        lugar_filtro = lugar_default
        if lugar and "punt" in lugar.lower():
            lugar_filtro = "Punt BIU"

        modalidad_norm = modalidad.lower().strip()
        if "presencial" in modalidad_norm and "online" in modalidad_norm:
            modalidad_norm = "presencial / online"
        elif "presencial" in modalidad_norm:
            modalidad_norm = "presencial"
        elif "online" in modalidad_norm:
            modalidad_norm = "online"
        else:
            modalidad_norm = "presencial / online"

        cursos.append({
            "titulo": titulo,
            "categoria": detectar_categoria(titulo),
            "desc": desc,
            "duracion": duracion,
            "lugar": lugar_filtro,
            "lugarCompleto": lugar if lugar else "Punt BIU / Aula informática planta baja de la Biblioteca General",
            "modalidad": modalidad_norm,
            "urlInscripcion": url_inscripcion,
            "urlFormulario": url_formulario
        })

    return cursos

def main():
    todos = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for fuente in FUENTES:
            try:
                cursos = extraer_cursos(page, fuente["url"], fuente["lugar"])
                todos.extend(cursos)
                print(f"✅ {fuente['url']}: {len(cursos)} cursos extraídos")
            except Exception as e:
                print(f"❌ Error en {fuente['url']}: {e}")
        browser.close()

    with open("cursos.json", "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
    print(f"✅ cursos.json generado con {len(todos)} cursos en total")

if __name__ == "__main__":
    main()
