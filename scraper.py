import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup

COMPETICIONES = {
    "senior_calavera": {
        "nombre": "2ª Andaluza Senior - Gr. 1",
        "equipo_foco": "CALAVERA",
        "url": "https://www.rfaf.es/pnfg/NPcd/NFG_CmpJornada?cod_primaria=1000120&cod_competicion=1000000&cod_grupo=1000001",
    },
    "infantil_sevilla": {
        "nombre": "4ª Andaluza Infantil - Gr. 7",
        "equipo_foco": "SEVILLA",
        "url": "https://www.rfaf.es/pnfg/NPcd/NFG_CmpJornada?cod_primaria=1000120&cod_competicion=1000000&cod_grupo=1000007",
    },
    "benjamin_sevilla": {
        "nombre": "4ª Andaluza Benjamín - Gr. 8",
        "equipo_foco": "SEVILLA",
        "url": "https://www.rfaf.es/pnfg/NPcd/NFG_CmpJornada?cod_primaria=1000120&cod_competicion=1000000&cod_grupo=1000008",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def extraer_partidos(url, equipo_foco):
    partidos = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            filas = soup.find_all("tr")
            for f in filas:
                texto = f.get_text(separator=" ", strip=True).upper()
                if equipo_foco in texto:
                    cols = [
                        c.get_text(strip=True)
                        for c in f.find_all(["td", "th"])
                        if c.get_text(strip=True)
                    ]
                    if cols:
                        partidos.append(" | ".join(cols))
    except Exception:
        pass
    return partidos


def main():
    resultado = {
        "ultima_actualizacion": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "grupos": {},
    }

    for clave, config in COMPETICIONES.items():
        partidos = extraer_partidos(config["url"], config["equipo_foco"])
        resultado["grupos"][clave] = {
            "nombre": config["nombre"],
            "equipo": config["equipo_foco"],
            "partidos": (
                partidos
                if partidos
                else ["No hay datos publicados aún para esta jornada"]
            ),
        }

    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
