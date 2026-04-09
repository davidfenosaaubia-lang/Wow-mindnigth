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
    --todo                  Descargar todo (clases, mazmorras, bandas)
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
        """Obtiene token OAuth2."""
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
            self.token_expiry = time.time() + datos.get("expires_in", 86400) - 60
            print("  OK: Autenticación correcta")
            return True
        except Exception as e:
            print(f"  ERROR autenticación: {e}")
            return False

    def get(self, endpoint, locale="es_ES", namespace=None):
        """Hace una petición GET a la API."""
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
            if resp.status_code == 404:
                print(f"  WARN: {endpoint} no encontrado (404)")
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  ERROR en {endpoint}: {e}")
            return None


# ============================================================
# Descarga de datos
# ============================================================

def descargar_clases(api):
    """Descarga todas las clases con sus specs y habilidades."""
    print("\n=== Descargando clases y especializaciones ===")

    indice_es = api.get("/data/wow/playable-class/index", locale=LOCALES["es"])
    indice_en = api.get("/data/wow/playable-class/index", locale=LOCALES["en"])

    if not indice_es or not indice_en:
        print("  ERROR: No se pudo obtener el índice de clases")
        print(f"  indice_es: {indice_es}")
        print(f"  indice_en: {indice_en}")
        return None

    # Buscar la key correcta para la lista de clases
    clases_key = None
    for key in ["classes", "playable_classes"]:
        if key in indice_es:
            clases_key = key
            break

    if not clases_key:
        print(f"  ERROR: Formato inesperado. Keys disponibles: {list(indice_es.keys())}")
        print(f"  Primeros 500 chars: {json.dumps(indice_es, ensure_ascii=False)[:500]}")
        return None

    print(f"  OK: Encontradas {len(indice_es[clases_key])} clases (key: '{clases_key}')")

    clases_en_map = {}
    for c in indice_en[clases_key]:
        clases_en_map[c["id"]] = c["name"]

    clases = []
    for clase_ref in indice_es[clases_key]:
        clase_id = clase_ref["id"]
        nombre_es = clase_ref["name"]
        nombre_en = clases_en_map.get(clase_id, "?")
        print(f"  Clase: {nombre_es} ({nombre_en}) [id:{clase_id}]")

        # Detalle de la clase para obtener specs
        det_es = api.get(f"/data/wow/playable-class/{clase_id}", locale=LOCALES["es"])
        det_en = api.get(f"/data/wow/playable-class/{clase_id}", locale=LOCALES["en"])

        specs = []
        if det_es and det_en:
            # Buscar la key de especialización
            spec_key = None
            for key in ["specializations", "specs"]:
                if key in det_es:
                    spec_key = key
                    break

            if spec_key:
                specs_en_map = {}
                for s in det_en.get(spec_key, []):
                    specs_en_map[s["id"]] = s["name"]

                for spec_ref in det_es.get(spec_key, []):
                    spec_id = spec_ref["id"]
                    spec_es = spec_ref["name"]
                    spec_en = specs_en_map.get(spec_id, "?")
                    print(f"    Spec: {spec_es} ({spec_en}) [id:{spec_id}]")

                    # Detalle de la spec para habilidades
                    sp_es = api.get(f"/data/wow/playable-specialization/{spec_id}",
                                    locale=LOCALES["es"])
                    sp_en = api.get(f"/data/wow/playable-specialization/{spec_id}",
                                    locale=LOCALES["en"])

                    habilidades = []
                    rol = "?"
                    if sp_es and sp_en:
                        rol = sp_es.get("role", {}).get("type", "?")

                        # Recoger habilidades de todas las estructuras posibles
                        habs_en = {}
                        for source_key in ["abilities", "ability_groups",
                                           "spells", "spell_groups"]:
                            items_en = sp_en.get(source_key, [])
                            for item in items_en:
                                # Puede ser directamente una habilidad o un grupo
                                if "spell" in item or "ability" in item:
                                    spell = item.get("spell", item.get("ability", {}))
                                    if spell and "id" in spell:
                                        habs_en[spell["id"]] = spell.get("name", "?")
                                elif "abilities" in item:
                                    # Es un grupo de habilidades
                                    for hab in item["abilities"]:
                                        spell = hab.get("spell", hab.get("ability", {}))
                                        if spell and "id" in spell:
                                            habs_en[spell["id"]] = spell.get("name", "?")
                                elif "id" in item and "name" in item:
                                    # Es directamente una habilidad
                                    habs_en[item["id"]] = item["name"]

                        for source_key in ["abilities", "ability_groups",
                                           "spells", "spell_groups"]:
                            items_es = sp_es.get(source_key, [])
                            for item in items_es:
                                if "spell" in item or "ability" in item:
                                    spell = item.get("spell", item.get("ability", {}))
                                    if spell and "id" in spell:
                                        habilidades.append({
                                            "id": spell["id"],
                                            "es": spell.get("name", "?"),
                                            "en": habs_en.get(spell["id"], "?"),
                                        })
                                elif "abilities" in item:
                                    for hab in item["abilities"]:
                                        spell = hab.get("spell", hab.get("ability", {}))
                                        if spell and "id" in spell:
                                            habilidades.append({
                                                "id": spell["id"],
                                                "es": spell.get("name", "?"),
                                                "en": habs_en.get(spell["id"], "?"),
                                            })
                                elif "id" in item and "name" in item:
                                    habilidades.append({
                                        "id": item["id"],
                                        "es": item["name"],
                                        "en": habs_en.get(item["id"], "?"),
                                    })

                        if not habilidades:
                            # Debug: mostrar qué keys tiene la spec
                            print(f"      (sin habilidades - keys: {list(sp_es.keys())})")

                    specs.append({
                        "id": spec_id,
                        "es": spec_es,
                        "en": spec_en,
                        "rol": rol,
                        "habilidades": habilidades,
                    })
            else:
                print(f"    WARN: Sin specs. Keys: {list(det_es.keys())}")

        clases.append({
            "id": clase_id,
            "es": nombre_es,
            "en": nombre_en,
            "especializaciones": specs,
        })

    total_habs = sum(
        len(s["habilidades"])
        for c in clases
        for s in c["especializaciones"]
    )
    print(f"\n  TOTAL: {len(clases)} clases, {total_habs} habilidades")

    return {
        "fuente": "Blizzard API",
        "tipo": "Clases, especializaciones y habilidades",
        "region": api.region,
        "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "clases": clases,
    }


def descargar_mazmorras(api):
    """Descarga mazmorras de M+."""
    print("\n=== Descargando mazmorras ===")

    # Probar varios endpoints
    endpoints = [
        ("/data/wow/mythic-keystone/dungeon/index", f"dynamic-{api.region}"),
        ("/data/wow/dungeon/index", f"static-{api.region}"),
        ("/data/wow/journal-instance/index", f"static-{api.region}"),
    ]

    mazmorras = []
    for endpoint, namespace in endpoints:
        print(f"  Probando {endpoint}...")
        data_es = api.get(endpoint, locale=LOCALES["es"], namespace=namespace)
        data_en = api.get(endpoint, locale=LOCALES["en"], namespace=namespace)

        if not data_es or not data_en:
            continue

        # Buscar la key que contiene la lista
        list_key = None
        for key in ["dungeons", "instances"]:
            if key in data_es and len(data_es[key]) > 0:
                list_key = key
                break

        if not list_key:
            print(f"    Keys disponibles: {list(data_es.keys())}")
            continue

        print(f"    OK: {len(data_es[list_key])} entradas (key: '{list_key}')")
        en_map = {m["id"]: m["name"] for m in data_en[list_key]}

        for m in data_es[list_key]:
            mazmorras.append({
                "id": m["id"],
                "es": m["name"],
                "en": en_map.get(m["id"], "?"),
            })
            print(f"    {m['name']} -> {en_map.get(m['id'], '?')}")
        break  # Si encontramos datos, no probar más endpoints

    if not mazmorras:
        print("  ERROR: No se encontraron mazmorras en ningún endpoint")
        return None

    return {
        "fuente": "Blizzard API",
        "tipo": "Mazmorras",
        "region": api.region,
        "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mazmorras": mazmorras,
    }


def descargar_bandas(api):
    """Descarga las bandas (raids) de todas las expansiones."""
    print("\n=== Descargando bandas ===")

    # Intentar con journal-expansion
    idx_es = api.get("/data/wow/journal-expansion/index", locale=LOCALES["es"])
    idx_en = api.get("/data/wow/journal-expansion/index", locale=LOCALES["en"])

    if not idx_es or not idx_en:
        print("  ERROR: No se pudo obtener índice de expansiones")
        return None

    # Buscar la key correcta
    tiers_key = None
    for key in ["tiers", "expansions"]:
        if key in idx_es:
            tiers_key = key
            break

    if not tiers_key:
        print(f"  Keys disponibles: {list(idx_es.keys())}")
        return None

    print(f"  OK: {len(idx_es[tiers_key])} expansiones")

    bandas = []
    for tier in idx_es[tiers_key]:
        tier_id = tier["id"]
        tier_name = tier.get("name", f"Expansion {tier_id}")
        print(f"  Expansion: {tier_name}")

        det_es = api.get(f"/data/wow/journal-expansion/{tier_id}", locale=LOCALES["es"])
        det_en = api.get(f"/data/wow/journal-expansion/{tier_id}", locale=LOCALES["en"])

        if not det_es or not det_en:
            continue

        # Buscar raids y dungeons en la respuesta
        for content_key in ["raids", "dungeons", "instances"]:
            items_es = det_es.get(content_key, [])
            items_en = det_en.get(content_key, [])
            if not items_es:
                continue

            en_map = {i["id"]: i["name"] for i in items_en}
            for item in items_es:
                entry = {
                    "id": item["id"],
                    "es": item["name"],
                    "en": en_map.get(item["id"], "?"),
                    "expansion": tier_name,
                    "tipo": content_key,
                }
                bandas.append(entry)
                print(f"    [{content_key}] {item['name']} -> {en_map.get(item['id'], '?')}")

    if not bandas:
        print("  WARN: No se encontraron instancias")
        return None

    return {
        "fuente": "Blizzard API",
        "tipo": "Bandas, mazmorras y contenido por expansión",
        "region": api.region,
        "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "instancias": bandas,
    }


# ============================================================
# Guardado
# ============================================================

def guardar(datos, nombre_archivo):
    """Guarda datos como JSON."""
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
        "--todo",
        action="store_true",
        help="Descargar todo: clases, mazmorras, bandas",
    )

    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        print("=" * 60)
        print("  NECESITAS UNA API KEY DE BLIZZARD (gratuita)")
        print("=" * 60)
        print()
        print("  Más info: rosetta/api/COMO-OBTENER-API-KEY.md")
        sys.exit(1)

    # Conectar
    api = BlizzardAPI(args.client_id, args.client_secret, args.region)
    if not api.autenticar():
        sys.exit(1)

    archivos = []

    # Siempre descargar clases
    datos = descargar_clases(api)
    if datos:
        archivos.append(guardar(datos, "clases-habilidades.json"))

    if args.todo:
        datos = descargar_mazmorras(api)
        if datos:
            archivos.append(guardar(datos, "mazmorras.json"))

        datos = descargar_bandas(api)
        if datos:
            archivos.append(guardar(datos, "instancias.json"))

    print("\n" + "=" * 60)
    print(f"  Descarga completa. {len(archivos)} archivos generados.")
    if archivos:
        print("  Archivos en: rosetta/api/")
    print("=" * 60)


if __name__ == "__main__":
    main()
