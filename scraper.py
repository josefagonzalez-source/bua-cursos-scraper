import requests
import json

def main():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; BUA-scraper/1.0)"}
    resp = requests.get(
        "https://biblioteca.ua.es/es/estudia-y-aprende/cursos-de-formacion/cursos-programados-o-bajo-demanda.html",
        headers=headers, timeout=15
    )
    resp.encoding = "utf-8"
    
    # Guardar el HTML completo para inspeccionarlo
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    
    print(f"Status: {resp.status_code}")
    print(f"Tamaño HTML: {len(resp.text)} caracteres")
    print("Contiene 'Descripción':", "Descripción" in resp.text)
    print("Contiene 'catálogo':", "catálogo" in resp.text.lower())
    print("Contiene 'h2':", "<h2" in resp.text)

    with open("cursos.json", "w") as f:
        json.dump([], f)

if __name__ == "__main__":
    main()
