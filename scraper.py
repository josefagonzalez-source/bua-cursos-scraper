import requests
from bs4 import BeautifulSoup
import json
import re

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
    "revistas y libros": "Bases de datos y recursos-e",
    "catálogo": "Catálogo BUA",
    "catalogo": "Catálogo BUA",
    "dialnet": "Dialnet y CSIC",
    "csic": "Dialnet y CSIC",
    "prensa": "Prensa digital",
    "hemeroteca": "Prensa digital",
    "repositorio": "Repositorios institucionales",
    "repositorios": "Repositorios institucionales",
    "servicios virtuales": "Servicios virtuales BUA",
    "biblioteca en un click": "Servicios virtuales BUA",
    "técnicas": "Técnicas de búsqueda",
    "tecnicas": "Técnicas de búsqueda",
    "estrategias de búsqueda": "Técnicas de búsqueda",
}

def detectar_categoria(titulo):
    titulo_lower = titulo.lower()
    for clave, categoria in CATEGORIAS.items():
        if clave in titulo_lower:
            return categoria
    return "Otros"

def extraer_cursos(url, lugar_default):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; BUA-scraper/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    cursos = []
    contenido = soup.find("div", id="contenido-pagina") or soup.find("main") or soup.body

    # Buscar bloques de curso: título en negrita seguido de h2 Descripción
    titulos = contenido.find_all("strong")

    for strong in titulos:
        titulo = strong.get_text(strip=True)
        if len(titulo) < 10:
            continue

        # Buscar el siguiente h2 con texto "Descripción"
        siguiente = strong.find_next("h2")
        if not siguiente or "escripci" not in siguiente.get_text():
            continue

        # Descripción: párrafo tras el h2
        desc_tag = siguiente.find_next_sibling()
        desc = ""
        if desc_tag and desc_tag.name == "p":
            desc = desc_tag.get_text(strip=True)

        # Lista ul con Duración, Lugar, Modalidad, Inscripción
        ul = siguiente.find_next("ul")
        duracion = lugar = modalidad = ""
        url_inscripcion = url_formulario = ""

        if ul:
            for li in ul.find_all("li"):
                texto = li.get_text(" ", strip=True)
                texto_lower = texto.lower()
                if "duración" in texto_lower or "duracion" in texto_lower:
                    duracion = re.sub(r"(?i)duración\s*:?\s*", "", texto).strip()
                elif "lugar" in texto_lower:
                    lugar = re.sub(r"(?i)lugar\s*:?\s*", "", texto).strip()
                elif "modalidad" in texto_lower:
                    modalidad = re.sub(r"(?i)modalidad\s*:?\s*", "", texto).strip()
                elif "inscripci" in texto_lower:
                    enlaces = li.find_all("a", href=True)
                    for a in enlaces:
                        href = a["href"]
                        texto_a = a.get_text(strip=True).lower()
                        if "inscripci" in texto_a:
                            url_inscripcion = href
                        elif "formulario" in texto_a or "rellena" in texto_a:
                            url_formulario = href

        # Normalizar lugar
        lugar_filtro = lugar_default
        if "punt" in lugar.lower():
            lugar_filtro = "Punt BIU"

        # Normalizar modalidad
        modalidad_norm = modalidad.lower().strip()
        if "presencial" in modalidad_norm and "online" in modalidad_norm:
            modalidad_norm = "presencial / online"
        elif "presencial" in modalidad_norm:
            modalidad_norm = "presencial"
        elif "online" in modalidad_norm:
            modalidad_norm = "online"

        cursos.append({
            "titulo": titulo,
            "categoria": detectar_categoria(titulo),
            "desc": desc,
            "duracion": duracion,
            "lugar": lugar_filtro,
            "lugarCompleto": lugar,
            "modalidad": modalidad_norm,
            "urlInscripcion": url_inscripcion,
            "urlFormulario": url_formulario
        })

    return cursos

def main():
    todos = []
    for fuente in FUENTES:
        try:
            cursos = extraer_cursos(fuente["url"], fuente["lugar"])
            todos.extend(cursos)
            print(f"✅ {fuente['url']}: {len(cursos)} cursos extraídos")
        except Exception as e:
            print(f"❌ Error en {fuente['url']}: {e}")

    with open("cursos.json", "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
    print(f"✅ cursos.json generado con {len(todos)} cursos en total")

if __name__ == "__main__":
    main()
