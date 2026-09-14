import json
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

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
    texto_fila = fila.get_text(separator=" ", strip=True)
    if equipo_foco not in texto_fila.upper():
        return None

    # 1. Extracción de Fecha (ej: 13-09-2026, 13-09, 13/09/2026)
    fecha = "Fecha por confirmar"
    fecha_match = re.search(
        r"\b(\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?)\b", texto_fila
    )
    if fecha_match:
        fecha = fecha_match.group(1).replace("-", "/")

    # 2. Extracción de Hora (ej: 19:00, 10:30)
    hora = "Horario por definir"
    hora_match = re.search(r"\b(\d{1,2}:\d{2})\b", texto_fila)
    if hora_match:
        hora = hora_match.group(1)

    # 3. Extracción de Campo (limpiando árbitros y texto sobrante)
    campo = "Campo pendiente de asignación"
    links_campo = fila.find_all("a", href=re.compile(r"NFG_VerCampo", re.I))
    if links_campo:
        campo = links_campo[0].get_text(strip=True)
    else:
        # Si no hay link directo, buscar texto de campo/instalación
        celdas = [
            c.get_text(strip=True)
            for c in fila.find_all(["td", "th"])
            if c.get_text(strip=True)
        ]
        if len(celdas) >= 3:
            posible_campo = celdas[-1]
            if (
                "Árbitro" in posible_campo
                or "Hierba" in posible_campo
                or "Campo" in posible_campo
            ):
                campo = posible_campo

    # Limpieza de etiquetas de árbitro pegadas al campo
    campo = re.split(r"Árbitro:|Arbitro:", campo)[0].strip()

    # 4. Equipos
    links_equipos = fila.find_all(
        "a", href=re.compile(r"NFG_VisEquipos|NFG_FichaEquipo", re.I)
    )
    if len(links_equipos) >= 2:
        local = links_equipos[0].get_text(strip=True)
        visitante = links_equipos[1].get_text(strip=True)
    else:
        partes = [p.strip() for p in texto_fila.split(" - ") if p.strip()]
        local = partes[0] if len(partes) > 0 else "Equipo Local"
        visitante = partes[1] if len(partes) > 1 else "Equipo Visitante"

    return {
        "partido": f"{local} vs {visitante}",
        "local": local,
        "visitante": visitante,
        "fecha": fecha,
        "hora": hora,
        "campo": campo,
    }


def extraer_jornadas_competicion(config):
    jornadas = {}
    url_base = config["url_base"]
    equipo = config["equipo_foco"]

    for j in range(1, 15):
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

    print("datos.json actualizado con éxito.")


if __name__ == "__main__":
    main()
