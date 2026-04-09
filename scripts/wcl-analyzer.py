#!/usr/bin/env python3
"""
Analizador de Warcraft Logs - Consulta datos de combate reales via API v2 (GraphQL).

Uso:
  python3 scripts/wcl-analyzer.py --personaje Kymera --servidor "Zul'jin" --region EU
  python3 scripts/wcl-analyzer.py --top-brewmaster
  python3 scripts/wcl-analyzer.py --log CODIGO_DEL_LOG

Variables de entorno (o .env):
  WCL_CLIENT_ID
  WCL_CLIENT_SECRET
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: necesitas 'requests'. Instala con: pip install requests")
    sys.exit(1)

SALIDA = Path(__file__).parent.parent / "analisis" / "logs"
WCL_AUTH_URL = "https://www.warcraftlogs.com/oauth/token"
WCL_API_URL = "https://www.warcraftlogs.com/api/v2/client"


class WarcraftLogsAPI:
    """Cliente para Warcraft Logs API v2 (GraphQL)."""

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expiry = 0

    def autenticar(self):
        if self.token and time.time() < self.token_expiry:
            return True

        print("Autenticando con Warcraft Logs API v2...")
        try:
            resp = requests.post(
                WCL_AUTH_URL,
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
                timeout=10,
            )
            resp.raise_for_status()
            datos = resp.json()
            self.token = datos["access_token"]
            self.token_expiry = time.time() + datos.get("expires_in", 3600) - 60
            print("  OK: Autenticación correcta")
            return True
        except Exception as e:
            print(f"  ERROR autenticación: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"  Respuesta: {e.response.text[:300]}")
            return False

    def query(self, graphql_query, variables=None):
        """Ejecuta una query GraphQL contra la API."""
        self.autenticar()
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"query": graphql_query}
        if variables:
            payload["variables"] = variables

        try:
            resp = requests.post(
                WCL_API_URL, json=payload, headers=headers, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                print(f"  WARN GraphQL errors: {data['errors']}")
            return data.get("data")
        except Exception as e:
            print(f"  ERROR query: {e}")
            return None


# ============================================================
# Queries
# ============================================================

def buscar_personaje(api, nombre, servidor, region="EU"):
    """Busca los logs recientes de un personaje."""
    print(f"\n=== Buscando logs de {nombre} - {servidor} ({region}) ===")

    query = """
    query ($name: String!, $serverSlug: String!, $serverRegion: String!) {
      characterData {
        character(name: $name, serverSlug: $serverSlug, serverRegion: $serverRegion) {
          name
          classID
          id
          recentReports(limit: 5) {
            data {
              code
              title
              startTime
              endTime
              zone {
                name
              }
            }
          }
          encounterRankings(specName: "Brewmaster", difficulty: 10, metric: dps)
        }
      }
    }
    """
    variables = {
        "name": nombre,
        "serverSlug": servidor.lower().replace("'", "").replace(" ", "-"),
        "serverRegion": region.lower(),
    }

    data = api.query(query, variables)
    if not data:
        return None

    char = data.get("characterData", {}).get("character")
    if not char:
        print(f"  No se encontró el personaje {nombre} en {servidor}")
        return None

    print(f"  Encontrado: {char['name']} (class ID: {char['classID']})")

    reports = char.get("recentReports", {}).get("data", [])
    print(f"  {len(reports)} reports recientes:")
    for r in reports:
        fecha = time.strftime("%Y-%m-%d", time.localtime(r["startTime"] / 1000))
        zona = r.get("zone", {}).get("name", "?")
        print(f"    [{fecha}] {r['title']} - {zona} (code: {r['code']})")

    rankings = char.get("encounterRankings")
    if rankings:
        print(f"\n  Rankings Brewmaster:")
        print(f"    {json.dumps(rankings, indent=2)[:500]}")

    return {"personaje": char, "reports": reports, "rankings": rankings}


def analizar_log(api, code):
    """Analiza un log específico."""
    print(f"\n=== Analizando log: {code} ===")

    query = """
    query ($code: String!) {
      reportData {
        report(code: $code) {
          title
          startTime
          endTime
          zone {
            name
          }
          owner {
            name
          }
          fights(killType: Encounters) {
            id
            name
            difficulty
            kill
            startTime
            endTime
            friendlyPlayers
          }
          masterData {
            actors(type: "Player") {
              id
              name
              type
              subType
              server
            }
          }
        }
      }
    }
    """

    data = api.query(query, {"code": code})
    if not data:
        return None

    report = data.get("reportData", {}).get("report")
    if not report:
        print(f"  No se encontró el log {code}")
        return None

    fecha = time.strftime("%Y-%m-%d", time.localtime(report["startTime"] / 1000))
    print(f"  Report: {report['title']}")
    print(f"  Fecha: {fecha}")
    print(f"  Zona: {report.get('zone', {}).get('name', '?')}")
    print(f"  Owner: {report.get('owner', {}).get('name', '?')}")

    fights = report.get("fights", [])
    print(f"\n  {len(fights)} encounters:")
    for f in fights:
        estado = "KILL" if f["kill"] else "WIPE"
        duracion = (f["endTime"] - f["startTime"]) / 1000
        print(f"    [{estado}] {f['name']} ({duracion:.0f}s) - fight #{f['id']}")

    players = report.get("masterData", {}).get("actors", [])
    print(f"\n  {len(players)} jugadores:")
    for p in players:
        print(f"    {p['name']} ({p.get('subType', '?')}) - {p.get('server', '?')}")

    return report


def top_brewmaster(api, limit=10):
    """Busca los mejores Brewmaster en rankings actuales."""
    print(f"\n=== Top {limit} Brewmaster (rankings actuales) ===")

    # Primero obtener los encounters actuales
    query = """
    query {
      worldData {
        expansion(id: 6) {
          zones {
            id
            name
            encounters {
              id
              name
            }
          }
        }
      }
    }
    """

    data = api.query(query)
    if not data:
        print("  No se pudieron obtener las zonas actuales")
        return None

    zones = data.get("worldData", {}).get("expansion", {}).get("zones", [])
    print(f"  {len(zones)} zonas encontradas")
    for z in zones:
        print(f"  Zona: {z['name']}")
        encounters = z.get("encounters", [])
        for e in encounters:
            print(f"    Boss: {e['name']} (id: {e['id']})")

    return zones


# ============================================================
# Guardado
# ============================================================

def guardar(datos, nombre_archivo):
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / nombre_archivo
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"\n  GUARDADO: {ruta}")
    return ruta


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analizador de Warcraft Logs"
    )
    parser.add_argument("--client-id", default=os.environ.get("WCL_CLIENT_ID"))
    parser.add_argument("--client-secret", default=os.environ.get("WCL_CLIENT_SECRET"))
    parser.add_argument("--personaje", help="Nombre del personaje")
    parser.add_argument("--servidor", help="Nombre del servidor")
    parser.add_argument("--region", default="EU", help="Región (default: EU)")
    parser.add_argument("--log", help="Código de un log específico para analizar")
    parser.add_argument("--top-brewmaster", action="store_true", help="Ver rankings de Brewmaster")
    parser.add_argument("--test", action="store_true", help="Test de conexión")

    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        print("Necesitas las credenciales de WCL API v2.")
        print("Configura WCL_CLIENT_ID y WCL_CLIENT_SECRET")
        sys.exit(1)

    api = WarcraftLogsAPI(args.client_id, args.client_secret)
    if not api.autenticar():
        sys.exit(1)

    if args.test:
        print("\nTest de conexión exitoso.")
        return

    if args.personaje and args.servidor:
        resultado = buscar_personaje(api, args.personaje, args.servidor, args.region)
        if resultado:
            guardar(resultado, f"{args.personaje.lower()}-logs.json")

    if args.log:
        resultado = analizar_log(api, args.log)
        if resultado:
            guardar(resultado, f"log-{args.log}.json")

    if args.top_brewmaster:
        resultado = top_brewmaster(api)
        if resultado:
            guardar(resultado, "top-brewmaster.json")

    if not args.personaje and not args.log and not args.top_brewmaster and not args.test:
        # Por defecto, buscar a Kymera
        resultado = buscar_personaje(api, "Kymera", "Zul'jin", "EU")
        if resultado:
            guardar(resultado, "kymera-logs.json")


if __name__ == "__main__":
    main()
