#!/usr/bin/env python3
"""
Rosetta Automática - Descarga terminología oficial ES/EN de la Blizzard API.

Uso:
  python3 scripts/rosetta-api.py --client-id TU_ID --client-secret TU_SECRET

  O con variables de entorno:
  export BLIZZARD_CLIENT_ID=tu_id
  export BLIZZARD_CLIENT_SECRET=tu_secret
  python3 scripts/rosetta-api.py

  Opciones:
    --region eu|us|kr|tw    Región (default: eu)
    --solo-clase NOMBRE     Descargar solo una clase (en inglés: warrior, mage, etc.)
    --todo                  Descargar todo (clases, mazmorras, bandas, objetos)
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
    print("Error: necesitas la librería 'requests'.")
    print("Instálala con: pip install requests")
    sys.exit(1)


# ============================================================
# Configuración
# ============================================================

REGIONES = {
    "eu": {"api": "https://eu.api.blizzard.com", "auth": "https://oauth.battle.net"},
    "us": {"api": "https://us.api.blizzard.com", "auth": "https://oauth.battle.net"},
    "kr": {"api": "https://kr.api.blizzard.com", "auth": "https://oauth.battle.net"},
    "tw": {"api": "https://tw.api.blizzard.com", "auth": "https://oauth.battle.net"},
}

LOCALES = {
    "es": "es_ES",
    "en": "en_US",
}

# Carpeta donde se guardan los resultados
SALIDA = Path(__file__).parent.parent / "rosetta" / "api"


# ============================================================
# Autenticación OAuth2
# ============================================================

class BlizzardAPI:
    """Cliente para la Blizzard API con autenticación OAuth2."""

    def __init__(self, client_id, client_secret, region="eu"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.urls = REGIONES[region]
        self.token = None
        self.token_expiry = 0

    def autenticar(self):
        """Obtiene token OAuth2. Se renueva automáticamente si expira."""
        if self.token and time.time() < self.token_expiry:
            return True

        print("Autenticando con Blizzard API...")
        try:
            resp = requests.post(
                f"{self.urls['auth']}/token",
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
                timeout=10,
            )
            resp.raise_for_status()
            datos = resp.json()
            self.token = datos["access_token"]
            # Renovar 60s antes de que expire
            self.token_expiry = time.time() + datos.get("expires_in", 86400) - 60
            print("  ✓ Autenticación correcta")
            return True
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 401:
                print("  ✗ Error de autenticación: client_id o client_secret incorrectos")
            else:
                print(f"  ✗ Error HTTP: {e}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error de conexión: {e}")
            return False

    def get(self, endpoint, locale="es_ES", namespace=None):
        """Hace una petición GET a la API. Reintenta si el token expiró."""
        self.autenticar()

        if namespace is None:
            namespace = f"static-{self.region}"

        params = {
            "namespace": namespace,
            "locale": locale,
            "access_token": self.token,
        }

        url = f"{self.urls['api']}{endpoint}"
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 404:
                return None  # Recurso no existe
            print(f"  ✗ Error en {endpoint}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error de conexión en {endpoint}: {e}")
            return None

    def get_bilingue(self, endpoint, namespace=None):
        """Obtiene un recurso en español e inglés."""
        es = self.get(endpoint, locale=LOCALES["es"], namespace=namespace)
        en = self.get(endpoint, locale=LOCALES["en"], namespace=namespace)
        return es, en


# ============================================================
# Descarga de datos
# ============================================================

def descargar_clases(api):
    """Descarga todas las clases y sus especializaciones con habilidades."""
    print("\n=== Descargando clases y especializaciones ===")

    indice_es, indice_en = api.get_bilingue("/data/wow/playable-class/index")
    if not indice_es or not indice_en:
        print("  ✗ No se pudo obtener el índice de clases")
        return None

    clases = []
    clases_en = {c["id"]: c["name"] for c in indice_en["classes"]}

    for clase_ref in indice_es["classes"]:
        clase_id = clase_ref["id"]
        nombre_es = clase_ref["name"]
        nombre_en = clases_en.get(clase_id, "?")
        print(f"  Descargando: {nombre_es} ({nombre_en})...")

        # Detalle de la clase
        detalle_es, detalle_en = api.get_bilingue(f"/data/wow/playable-class/{clase_id}")
        if not detalle_es or not detalle_en:
            continue

        specs = []
        specs_en = {s["id"]: s["name"] for s in detalle_en.get("specializations", [])}

        for spec_ref in detalle_es.get("specializations", []):
            spec_id = spec_ref["id"]
            spec_nombre_es = spec_ref["name"]
            spec_nombre_en = specs_en.get(spec_id, "?")

            # Detalle de la especialización (incluye habilidades)
            spec_es, spec_en = api.get_bilingue(
                f"/data/wow/playable-specialization/{spec_id}"
            )

            habilidades = []
            if spec_es and spec_en:
                habs_en = {}
                for grupo in spec_en.get("ability_groups", []):
                    for hab in grupo.get("abilities", []):
                        spell = hab.get("spell", hab.get("ability", {}))
                        if spell and "id" in spell:
                            habs_en[spell["id"]] = spell.get("name", "?")

                for grupo in spec_es.get("ability_groups", []):
                    for hab in grupo.get("abilities", []):
                        spell = hab.get("spell", hab.get("ability", {}))
                        if spell and "id" in spell:
                            habilidades.append({
                                "id": spell["id"],
                                "es": spell.get("name", "?"),
                                "en": habs_en.get(spell["id"], "?"),
                            })

                rol = spec_es.get("role", {}).get("type", "?")
            else:
                rol = "?"

            specs.append({
                "id": spec_id,
                "es": spec_nombre_es,
                "en": spec_nombre_en,
                "rol": rol,
                "habilidades": habilidades,
            })

        clases.append({
            "id": clase_id,
            "es": nombre_es,
            "en": nombre_en,
            "especializaciones": specs,
        })

    return {
        "fuente": "Blizzard API",
        "tipo": "Clases, especializaciones y habilidades",
        "region": api.region,
        "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "clases": clases,
    }


def descargar_mazmorras(api):
    """Descarga las mazmorras actuales."""
    print("\n=== Descargando mazmorras ===")

    # El índice de mazmorras de M+ está en el endpoint de mythic keystone
    indice_es = api.get("/data/wow/mythic-keystone/dungeon/index",
                        locale=LOCALES["es"], namespace=f"dynamic-{api.region}")
    indice_en = api.get("/data/wow/mythic-keystone/dungeon/index",
                        locale=LOCALES["en"], namespace=f"dynamic-{api.region}")

    if not indice_es or not indice_en:
        print("  ✗ No se pudo obtener el índice de mazmorras M+")
        # Intentar con el índice estático
        indice_es, indice_en = api.get_bilingue("/data/wow/dungeon/index")
        if not indice_es or not indice_en:
            print("  ✗ Tampoco se pudo con el índice estático")
            return None

    mazmorras = []
    maz_en = {}
    for m in indice_en.get("dungeons", indice_en.get("instances", [])):
        maz_en[m["id"]] = m["name"]

    for m in indice_es.get("dungeons", indice_es.get("instances", [])):
        mazmorras.append({
            "id": m["id"],
            "es": m["name"],
            "en": maz_en.get(m["id"], "?"),
        })
        print(f"  {m['name']} → {maz_en.get(m['id'], '?')}")

    return {
        "fuente": "Blizzard API",
        "tipo": "Mazmorras",
        "region": api.region,
        "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mazmorras": mazmorras,
    }


def descargar_bandas(api):
    """Descarga las bandas (raids)."""
    print("\n=== Descargando bandas ===")

    indice_es, indice_en = api.get_bilingue("/data/wow/raid/index")
    if not indice_es or not indice_en:
        # Intentar con journal
        indice_es, indice_en = api.get_bilingue("/data/wow/journal-expansion/index")
        if not indice_es or not indice_en:
            print("  ✗ No se pudo obtener el índice de bandas")
            return None

    bandas = []

    # Si tenemos raids directamente
    if "raids" in indice_es:
        raids_en = {r["id"]: r["name"] for r in indice_en.get("raids", [])}
        for r in indice_es.get("raids", []):
            bandas.append({
                "id": r["id"],
                "es": r["name"],
                "en": raids_en.get(r["id"], "?"),
            })
            print(f"  {r['name']} → {raids_en.get(r['id'], '?')}")
    # Si tenemos expansiones del journal, buscar instancias de tipo RAID
    elif "tiers" in indice_es:
        tiers_en = {t["id"]: t for t in indice_en.get("tiers", [])}
        for tier in indice_es.get("tiers", []):
            tier_id = tier["id"]
            det_es = api.get(f"/data/wow/journal-expansion/{tier_id}", locale=LOCALES["es"])
            det_en = api.get(f"/data/wow/journal-expansion/{tier_id}", locale=LOCALES["en"])
            if det_es and det_en:
                raids_en = {r["id"]: r["name"] for r in det_en.get("raids", [])}
                for r in det_es.get("raids", []):
                    bandas.append({
                        "id": r["id"],
                        "es": r["name"],
                        "en": raids_en.get(r["id"], "?"),
                        "expansion": tier.get("name", "?"),
                    })
                    print(f"  {r['name']} → {raids_en.get(r['id'], '?')}")

    return {
        "fuente": "Blizzard API",
        "tipo": "Bandas (Raids)",
        "region": api.region,
        "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "bandas": bandas,
    }


def descargar_stats_personaje(api):
    """Descarga los nombres oficiales de las estadísticas del juego."""
    print("\n=== Descargando nombres de estadísticas ===")

    # Las power types dan los nombres de recursos
    pt_es = api.get("/data/wow/power-type/index", locale=LOCALES["es"])
    pt_en = api.get("/data/wow/power-type/index", locale=LOCALES["en"])

    recursos = []
    if pt_es and pt_en:
        rec_en = {r["id"]: r["name"] for r in pt_en.get("power_types", [])}
        for r in pt_es.get("power_types", []):
            recursos.append({
                "id": r["id"],
                "es": r["name"],
                "en": rec_en.get(r["id"], "?"),
            })
            print(f"  {r['name']} → {rec_en.get(r['id'], '?')}")

    return {
        "fuente": "Blizzard API",
        "tipo": "Estadísticas y recursos",
        "region": api.region,
        "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "recursos": recursos,
    }


# ============================================================
# Guardado
# ============================================================

def guardar(datos, nombre_archivo):
    """Guarda datos como JSON con formato legible."""
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / nombre_archivo
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"\n  ✓ Guardado en: {ruta}")
    return ruta


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Rosetta Automática - Descarga terminología ES/EN de Blizzard API"
    )
    parser.add_argument(
        "--client-id",
        default=os.environ.get("BLIZZARD_CLIENT_ID"),
        help="Client ID de Blizzard API (o variable BLIZZARD_CLIENT_ID)",
    )
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("BLIZZARD_CLIENT_SECRET"),
        help="Client Secret de Blizzard API (o variable BLIZZARD_CLIENT_SECRET)",
    )
    parser.add_argument(
        "--region",
        default="eu",
        choices=REGIONES.keys(),
        help="Región del servidor (default: eu)",
    )
    parser.add_argument(
        "--solo-clase",
        help="Descargar solo una clase (nombre en inglés: warrior, mage, etc.)",
    )
    parser.add_argument(
        "--todo",
        action="store_true",
        help="Descargar todo: clases, mazmorras, bandas, stats",
    )

    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        print("=" * 60)
        print("  NECESITAS UNA API KEY DE BLIZZARD (gratuita)")
        print("=" * 60)
        print()
        print("  1. Ve a https://develop.battle.net/access/clients")
        print("  2. Inicia sesión con tu cuenta de Battle.net")
        print("  3. Crea un nuevo cliente (nombre: lo que quieras)")
        print("  4. Copia el Client ID y Client Secret")
        print("  5. Ejecuta:")
        print()
        print("     python3 scripts/rosetta-api.py \\")
        print("       --client-id TU_CLIENT_ID \\")
        print("       --client-secret TU_CLIENT_SECRET")
        print()
        print("  O con variables de entorno:")
        print()
        print("     export BLIZZARD_CLIENT_ID=tu_id")
        print("     export BLIZZARD_CLIENT_SECRET=tu_secret")
        print("     python3 scripts/rosetta-api.py --todo")
        print()
        print("  Más info: rosetta/api/COMO-OBTENER-API-KEY.md")
        sys.exit(1)

    # Conectar
    api = BlizzardAPI(args.client_id, args.client_secret, args.region)
    if not api.autenticar():
        sys.exit(1)

    archivos_generados = []

    # Por defecto, descargar clases
    if args.todo or not args.solo_clase:
        datos = descargar_clases(api)
        if datos:
            archivos_generados.append(guardar(datos, "clases-habilidades.json"))

    if args.todo:
        datos = descargar_mazmorras(api)
        if datos:
            archivos_generados.append(guardar(datos, "mazmorras.json"))

        datos = descargar_bandas(api)
        if datos:
            archivos_generados.append(guardar(datos, "bandas.json"))

        datos = descargar_stats_personaje(api)
        if datos:
            archivos_generados.append(guardar(datos, "stats-recursos.json"))

    print("\n" + "=" * 60)
    print(f"  Descarga completa. {len(archivos_generados)} archivos generados.")
    print("  Los archivos están en: rosetta/api/")
    print("=" * 60)


if __name__ == "__main__":
    main()
