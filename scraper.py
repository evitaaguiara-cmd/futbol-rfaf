import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Configuración con las 3 URLs oficiales de la RFAF
COMPETICIONES = {
    "senior_calavera": {
        "nombre": "2ª Andaluza Senior - Gr. 1",
        "equipo_foco": "CALAVERA",
        "url_base": "https://www.rfaf.es/pnfg/NPcd/NFG_CmpJornada?cod_primaria=1000120&CodCompeticion=48466126&CodGrupo=48466127&CodTemporada=22&cod_agrupacion=1&Sch_Codigo_Delegacion=1&Sch_Tipo_Juego=1",
    },
    "infantil_sevilla": {
        "nombre": "4ª Andaluza Infantil - Gr. 7",
        "equipo_foco": "SEVILLA",
        "url_base": "https://www.rfaf.es/pnfg/NPcd/NFG_CmpJornada?cod_primaria=1000120&CodCompeticion=48466271&CodGrupo=48466278&CodTemporada=22&cod_agrupacion=1&Sch_Codigo_Delegacion=1&Sch_Tipo_Juego=1",
    },
    "benjamin_sevilla": {
        "nombre": "4ª Andaluza Benjamín - Gr. 8",
        "equipo_foco": "SEVILLA",
        "url_base": "https://www.rfaf.es/pnfg/NPcd/NFG_CmpJornada?cod_primaria=1000120&CodCompeticion=48466406&CodGrupo=48466414&CodTemporada=22&cod_agrupacion=1&Sch_Codigo_Delegacion=1&Sch_Tipo_Juego=2",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def parsear_fila_partido(fila, equipo_foco):
    """Extrae local, visitante, fecha, hora y campo de la fila de la RFAF."""
    texto_fila = fila.get_text(separator=" ", strip=True)
    if equipo_foco not in texto_fila.upper():
        return None

    celdas = fila.find_all(["td", "th"])
    textos_celdas = [c.get_text(strip=True) for c in celdas if c.get_text(strip=True)]

    hora = "Horario por definir"
    fecha = "Fecha por confirmar"
    campo = "Campo pendiente de asignación"

    hora_match = re.search(r"\b(\d{1,2}:\d{2})\b", texto_fila)
    if hora_match:
        hora = hora_match.group(1)

    fecha_match = re.search(r"\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b", texto_fila)
    if fecha_match:
        fecha = fecha_match.group(1)

    links_campo = fila.find_all("a", href=re.compile(r"NFG_VerCampo", re.I))
    if links_campo:
        campo = links_campo[0].get_text(strip=True)
    elif len(textos_celdas) >= 4:
        campo = textos_celdas[-1]

    links_equipos = fila.find_all(
        "a", href=re.compile(r"NFG_VisEquipos|NFG_FichaEquipo", re.I)
    )
    if len(links_equipos) >= 2:
        local = links_equipos[0].get_text(strip=True)
        visitante = links_equipos[1].get_text(strip=True)
    else:
        local = textos_celdas[0] if len(textos_celdas) > 0 else "Local"
        visitante = (
            textos_celdas[2]
            if len(textos_celdas) > 2
            else (textos_celdas[1] if len(textos_celdas) > 1 else "Visitante")
        )

    resultado = ""
    res_match = re.search(r"\b(\d+\s*-\s*\d+)\b", texto_fila)
    if res_match:
        resultado = res_match.group(1)

    return {
        "partido": f"{local} vs {visitante}",
        "local": local,
        "visitante": visitante,
        "fecha": fecha,
        "hora": hora,
        "campo": campo,
        "resultado": resultado,
    }


def extraer_jornadas_competicion(config):
    jornadas = {}
    url_base = config["url_base"]
    equipo = config["equipo_foco"]

    for j in range(1, 11):
        url_jornada = f"{url_base}&CodJornada={j}"
        try:
            res = requests.get(url_jornada, headers=HEADERS, timeout=12)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                filas = soup.find_all("tr")

                partido_encontrado = None
                for fila in filas:
                    partido_encontrado = parsear_fila_partido(fila, equipo)
                    if partido_encontrado:
                        break

                if partido_encontrado:
                    jornadas[str(j)] = partido_encontrado
                else:
                    jornadas[str(j)] = {
                        "partido": "Descansa o jornada sin publicar",
                        "fecha": "---",
                        "hora": "---",
                        "campo": "---",
                        "resultado": "",
                    }
        except Exception as e:
            print(f"Error jornada {j}: {e}")

    return jornadas


def main():
    datos = {
        "ultima_actualizacion": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "competiciones": {},
    }

    for clave, conf in COMPETICIONES.items():
        print(f"Procesando {conf['nombre']}...")
        jornadas = extraer_jornadas_competicion(conf)
        datos["competiciones"][clave] = {
            "nombre": conf["nombre"],
            "equipo": conf["equipo_foco"],
            "jornadas": jornadas,
        }

    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print("datos.json guardado con éxito.")


if __name__ == "__main__":
    main()
