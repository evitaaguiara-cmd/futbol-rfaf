import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Enlaces directos a la pestaña de CALENDARIO de cada grupo
COMPETICIONES = {
    "senior_calavera": {
        "nombre": "2ª Andaluza Senior - Gr. 1",
        "equipo_foco": "CALAVERA",
        "url": "https://www.rfaf.es/pnfg/NPcd/NFG_CmpCalendario?cod_primaria=1000120&cod_competicion=1000000&cod_grupo=1000001",
    },
    "infantil_sevilla": {
        "nombre": "4ª Andaluza Infantil - Gr. 7",
        "equipo_foco": "SEVILLA",
        "url": "https://www.rfaf.es/pnfg/NPcd/NFG_CmpCalendario?cod_primaria=1000120&cod_competicion=1000000&cod_grupo=1000007",
    },
    "benjamin_sevilla": {
        "nombre": "4ª Andaluza Benjamín - Gr. 8",
        "equipo_foco": "SEVILLA",
        "url": "https://www.rfaf.es/pnfg/NPcd/NFG_CmpCalendario?cod_primaria=1000120&cod_competicion=1000000&cod_grupo=1000008",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def extraer_todas_las_jornadas(url, equipo_foco):
    jornadas = {}
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200:
            return jornadas

        soup = BeautifulSoup(res.text, "html.parser")
        texto_completo = soup.get_text()

        # Extraemos bloques de jornadas
        bloques_jornada = re.split(
            r"Jornada\s+(\d+)", texto_completo, flags=re.IGNORECASE
        )

        # Si no detecta el patrón, busca filas de partidos comunes
        if len(bloques_jornada) > 1:
            for i in range(1, len(bloques_jornada), 2):
                num_jornada = int(bloques_jornada[i])
                contenido = bloques_jornada[i + 1]

                lineas = [
                    l.strip()
                    for l in contenido.split("\n")
                    if l.strip() and equipo_foco in l.upper()
                ]
                if lineas:
                    jornadas[str(num_jornada)] = lineas[0]
        else:
            filas = soup.find_all("tr")
            j_actual = 1
            for f in filas:
                txt = f.get_text(separator=" ", strip=True).upper()
                if equipo_foco in txt:
                    cols = [
                        c.get_text(strip=True)
                        for c in f.find_all(["td", "th"])
                        if c.get_text(strip=True)
                    ]
                    jornadas[str(j_actual)] = (
                        " | ".join(cols) if cols else txt[:100]
                    )
                    j_actual += 1
    except Exception as e:
        print(f"Error: {e}")

    return jornadas


def main():
    resultado = {
        "ultima_actualizacion": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "competiciones": {},
    }

    for clave, conf in COMPETICIONES.items():
        jornadas_equipo = extraer_todas_las_jornadas(
            conf["url"], conf["equipo_foco"]
        )

        # Si aún no hay datos de la federación, crea jornadas plantilla para poder probar la navegación
        if not jornadas_equipo:
            jornadas_equipo = {
                str(i): f"Jornada {i}: Horario pendiente de fijar por federación"
                for i in range(1, 31)
            }

        resultado["competiciones"][clave] = {
            "nombre": conf["nombre"],
            "equipo": conf["equipo_foco"],
            "jornadas": jornadas_equipo,
        }

    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
