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
    "optimiza tus búsquedas": "Google avanzado",
    "bases de datos": "Bases de datos y recursos-e",
    "revistas y libros": "Bases de datos y recursos-e",
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

# Títulos a ignorar (falsos positivos)
IGNORAR = {
    "formulario de inscripción", "inscripción", "inscripcion",
    "modalidad:", "modalidad", "duración:", "lugar:", "lugar",
    "rellena este formulario", "indíces csic", "indíces csic",
    "recolecta", "rua", "dialnet", "indices csic"
}

def detectar_categoria(titulo):
    titulo_lower = titulo.lower()
    for clave, categoria in CATEGORIAS.items():
        if clave in titulo_lower:
            return categoria
    return "Otros"

def es_titulo_valido(texto):
    """Comprueba que el texto es un título real de curso y no un elemento de la lista."""
    t = texto.strip().lower().rstrip(":")
    if t in IGNORAR:
        return False
    if len(texto) < 15:
        return False
    # Los títulos reales tienen al menos 4 palabras
    if len(texto.split()) < 4:
        return False
    # No empieza por dígito (teléfonos)
    if texto[0].isdigit():
        return False
    # No es un email
    if "@" in texto:
        return False
    return True

def extraer_cursos(url, lugar_default):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; BUA-scraper/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    cursos = []

    # Buscar todos los elementos <strong> que sean títulos de curso
    # Los títulos están en <strong> seguidos de un <h2>Descripción</h2>
    for strong in soup.find_all("strong"):
        titulo = strong.get_text(strip=True)

        if not es_titulo_valido(titulo):
            continue

        # Verificar que va seguido de un h2 con "Descripción"
        siguiente_h2 = strong.find_next("h2")
        if not siguiente_h2:
            continue
        if "escripci" not in siguiente_h2.get_text():
            continue

        # Comprobar que el h2 está suficientemente cerca (no más de 3 elementos entre medias)
        # Para evitar falsos positivos lejanos
        entre = []
        nodo = strong.next_sibling
        encontrado = False
        for _ in range(10):
            if nodo is None:
                break
            if hasattr(nodo, 'name') and nodo.name == 'h2' and "escripci" in nodo.get_text():
                encontrado = True
                break
            nodo = nodo.next_sibling
        
        if not encontrado:
            continue

        # Descripción: párrafo tras el h2
        desc_tag = siguiente_h2.find_next_sibling()
        desc = ""
        if desc_tag and desc_tag.name == "p":
            desc = desc_tag.get_text(strip=True)

        # Lista ul con Duración, Lugar, Modalidad, Inscripción
        ul = siguiente_h2.find_next("ul")
        duracion = lugar = modalidad = ""
        url_inscripcion = url_formulario = ""

        if ul:
            for li in ul.find_all("li"):
                texto_li = li.get_text(" ", strip=True)
                texto_lower = texto_li.lower()
                if "duración" in texto_lower or "duracion" in texto_lower:
                    duracion = re.sub(r"(?i)\*?\*?duración\s*:?\s*\*?\*?", "", texto_li).strip()
                elif "lugar" in texto_lower and not duracion == "":
                    lugar = re.sub(r"(?i)\*?\*?lugar\s*:?\s*\*?\*?", "", texto_li).strip()
                elif "modalidad" in texto_lower:
                    modalidad = re.sub(r"(?i)\*?\*?modalidad\s*:?\s*\*?\*?", "", texto_li).strip()
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
            "lugarCompleto": lugar if lugar else "Punt BIU / Aula informática planta baja de la Biblioteca General",
            "modalidad": modalidad_norm if modalidad_norm else "presencial / online",
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
