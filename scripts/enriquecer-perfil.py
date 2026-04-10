#!/usr/bin/env python3
"""
Enriquecedor de perfil SimC - Consulta la Blizzard API para obtener
datos completos de cada item del perfil (nombre ES/EN, stats, calidad, icono).

Uso:
  python3 scripts/enriquecer-perfil.py --perfil conocimiento/monje/perfiles/kymera-brewmaster-2026-04-09.simc

Variables de entorno:
  BLIZZARD_CLIENT_ID
  BLIZZARD_CLIENT_SECRET
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: necesitas 'requests'. pip install requests")
    sys.exit(1)


class BlizzardAPI:
    def __init__(self, client_id, client_secret, region="eu"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.api_url = f"https://{region}.api.blizzard.com"
        self.token = None
        self.token_expiry = 0

    def autenticar(self):
        if self.token and time.time() < self.token_expiry:
            return True
        try:
            resp = requests.post(
                "https://oauth.battle.net/token",
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
                timeout=10,
            )
            resp.raise_for_status()
            datos = resp.json()
            self.token = datos["access_token"]
            self.token_expiry = time.time() + datos.get("expires_in", 86400) - 60
            print("  OK: Autenticación Blizzard")
            return True
        except Exception as e:
            print(f"  ERROR auth: {e}")
            return False

    def get_item(self, item_id, locale="es_ES"):
        self.autenticar()
        try:
            resp = requests.get(
                f"{self.api_url}/data/wow/item/{item_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                params={
                    "namespace": f"static-{self.region}",
                    "locale": locale,
                },
                timeout=10,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  ERROR item {item_id}: {e}")
            return None

    def get_item_media(self, item_id):
        self.autenticar()
        try:
            resp = requests.get(
                f"{self.api_url}/data/wow/media/item/{item_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                params={"namespace": f"static-{self.region}"},
                timeout=10,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            assets = data.get("assets", [])
            for a in assets:
                if a.get("key") == "icon":
                    return a.get("value")
            return None
        except:
            return None

    def get_character_media(self, realm_slug, character_name):
        """Obtiene la imagen render del personaje."""
        self.autenticar()
        try:
            resp = requests.get(
                f"{self.api_url}/profile/wow/character/{realm_slug}/{character_name.lower()}/character-media",
                headers={"Authorization": f"Bearer {self.token}"},
                params={
                    "namespace": f"profile-{self.region}",
                    "locale": "es_ES",
                },
                timeout=10,
            )
            if resp.status_code != 200:
                print(f"  WARN: character-media {resp.status_code}")
                return None
            data = resp.json()
            resultado = {}
            for asset in data.get("assets", []):
                resultado[asset["key"]] = asset["value"]
            return resultado
        except Exception as e:
            print(f"  ERROR character-media: {e}")
            return None


def parsear_simc(ruta_perfil):
    """Extrae items del perfil SimC."""
    items = []
    personaje = {}
    ultimo_comentario = ""

    with open(ruta_perfil, "r") as f:
        for linea in f:
            linea = linea.strip()
            if linea.startswith("#"):
                ultimo_comentario = linea
                continue
            if not linea:
                continue

            # Datos del personaje
            for campo in ["monk=", "level=", "race=", "region=", "server=", "spec="]:
                if linea.startswith(campo):
                    key = campo.rstrip("=")
                    if key == "monk":
                        key = "nombre"
                    valor = linea.split("=", 1)[1].strip().strip('"')
                    personaje[key] = valor

            # Items equipados (no los de la bolsa que empiezan con #)
            match = re.match(r'^(\w+)=,id=(\d+)', linea)
            if match:
                ranura = match.group(1)
                item_id = int(match.group(2))

                # Extraer enchant, gems, bonus
                enchant = re.search(r'enchant_id=(\d+)', linea)
                gems = re.findall(r'gem_id=(\d+)', linea)
                crafted = 'crafting_quality' in linea

                # ilvl real del comentario: "# Nombre del item (276)"
                ilvl_real = 0
                ilvl_match = re.search(r'\((\d+)\)', ultimo_comentario)
                if ilvl_match:
                    ilvl_real = int(ilvl_match.group(1))

                items.append({
                    "ranura": ranura,
                    "item_id": item_id,
                    "ilvl_real": ilvl_real,
                    "enchant_id": int(enchant.group(1)) if enchant else None,
                    "gem_ids": [int(g) for g in gems],
                    "crafted": crafted,
                })

    return personaje, items


RANURA_ES = {
    "head": "Cabeza",
    "neck": "Cuello",
    "shoulder": "Hombros",
    "back": "Espalda",
    "chest": "Pecho",
    "wrist": "Muñecas",
    "hands": "Manos",
    "waist": "Cintura",
    "legs": "Piernas",
    "feet": "Pies",
    "finger1": "Anillo 1",
    "finger2": "Anillo 2",
    "trinket1": "Trinket 1",
    "trinket2": "Trinket 2",
    "main_hand": "Arma",
    "off_hand": "Mano secundaria",
}

CALIDAD_COLOR = {
    1: {"es": "Común", "color": "#ffffff"},
    2: {"es": "Poco común", "color": "#1eff00"},
    3: {"es": "Raro", "color": "#0070dd"},
    4: {"es": "Épico", "color": "#a335ee"},
    5: {"es": "Legendario", "color": "#ff8000"},
}


def enriquecer(api, personaje, items):
    """Consulta la API para cada item y genera datos enriquecidos."""
    print(f"\n=== Enriqueciendo perfil de {personaje.get('nombre', '?')} ===")

    # Imagen del personaje
    server_slug = personaje.get("server", "zuljin").lower().replace("'", "").replace(" ", "-")
    nombre = personaje.get("nombre", "").lower()
    print(f"  Buscando imagen: {nombre} @ {server_slug}")
    media = api.get_character_media(server_slug, nombre)
    if media:
        print(f"  OK: Imagen encontrada ({len(media)} assets)")
    else:
        print("  WARN: No se pudo obtener imagen del personaje")

    equipo_enriquecido = []

    for item in items:
        item_id = item["item_id"]
        ranura = item["ranura"]
        print(f"  [{RANURA_ES.get(ranura, ranura)}] item {item_id}...", end=" ")

        # Nombre en español
        data_es = api.get_item(item_id, locale="es_ES")
        data_en = api.get_item(item_id, locale="en_US")

        if not data_es:
            print("NO ENCONTRADO")
            equipo_enriquecido.append({
                "ranura_en": ranura,
                "ranura_es": RANURA_ES.get(ranura, ranura),
                "item_id": item_id,
                "nombre_es": "?",
                "nombre_en": "?",
                "ilvl": 0,
                "calidad": 0,
                "enchant_id": item["enchant_id"],
                "gem_ids": item["gem_ids"],
                "crafted": item["crafted"],
            })
            continue

        nombre_es = data_es.get("name", "?")
        nombre_en = data_en.get("name", "?") if data_en else "?"
        # ilvl: usar el del SimC (real con upgrades), no el de la API (base)
        ilvl = item["ilvl_real"] if item.get("ilvl_real", 0) > 0 else data_es.get("level", data_es.get("item_level", 0))
        calidad_raw = data_es.get("quality", {})
        calidad = calidad_raw.get("type", "COMMON") if isinstance(calidad_raw, dict) else calidad_raw

        # Mapear calidad a número
        calidad_map = {"POOR": 0, "COMMON": 1, "UNCOMMON": 2, "RARE": 3, "EPIC": 4, "LEGENDARY": 5}
        calidad_num = calidad_map.get(calidad, 1)

        # Icono
        icon_url = api.get_item_media(item_id)

        # Extraer stats del item de la respuesta de la API
        stats = []
        for stat_entry in data_es.get("preview_item", {}).get("stats", []):
            stat_type = stat_entry.get("type", {})
            stats.append({
                "tipo": stat_type.get("name", stat_type.get("type", "?")),
                "valor": stat_entry.get("value", 0),
                "display": stat_entry.get("display", {}).get("display_string", ""),
            })

        # Si no hay stats en preview_item, intentar stats directas
        if not stats:
            for stat_entry in data_es.get("stats", []):
                if isinstance(stat_entry, dict):
                    stat_type = stat_entry.get("type", {})
                    stats.append({
                        "tipo": stat_type.get("name", stat_type.get("type", "?")),
                        "valor": stat_entry.get("value", 0),
                    })

        # Tipo de item, subtipo, armadura
        item_class = data_es.get("item_class", {}).get("name", "")
        item_subclass = data_es.get("item_subclass", {}).get("name", "")
        armor = data_es.get("preview_item", {}).get("armor", {}).get("value", 0)
        durability = data_es.get("preview_item", {}).get("durability", {}).get("value", 0)
        binding = data_es.get("preview_item", {}).get("binding", {}).get("name", "")
        inventory_type = data_es.get("inventory_type", {}).get("name", "")

        # Procedencia (de dónde sale)
        source = data_es.get("source", {})
        source_type = source.get("type", "") if isinstance(source, dict) else ""
        source_name = source.get("name", "") if isinstance(source, dict) else ""

        print(f"{nombre_es} ({len(stats)} stats)")

        equipo_enriquecido.append({
            "ranura_en": ranura,
            "ranura_es": RANURA_ES.get(ranura, ranura),
            "item_id": item_id,
            "nombre_es": nombre_es,
            "nombre_en": nombre_en,
            "ilvl": ilvl,
            "calidad": calidad_num,
            "calidad_nombre": CALIDAD_COLOR.get(calidad_num, {}).get("es", "?"),
            "calidad_color": CALIDAD_COLOR.get(calidad_num, {}).get("color", "#fff"),
            "icono": icon_url,
            "tipo": item_subclass or item_class,
            "ranura_tipo": inventory_type,
            "armadura": armor,
            "durabilidad": durability,
            "vinculacion": binding,
            "stats": stats,
            "procedencia_tipo": source_type,
            "procedencia_nombre": source_name,
            "enchant_id": item["enchant_id"],
            "tiene_enchant": item["enchant_id"] is not None,
            "gem_ids": item["gem_ids"],
            "tiene_gemas": len(item["gem_ids"]) > 0,
            "crafted": item["crafted"],
        })

    return {
        "personaje": {
            "nombre": personaje.get("nombre", "?"),
            "nivel": int(personaje.get("level", 0)),
            "raza": personaje.get("race", "?"),
            "servidor": personaje.get("server", "?"),
            "spec": personaje.get("spec", "?"),
            "region": personaje.get("region", "eu"),
            "media": media,
        },
        "equipo": equipo_enriquecido,
        "ilvl_medio": round(sum(e["ilvl"] for e in equipo_enriquecido) / max(len(equipo_enriquecido), 1)),
        "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def main():
    parser = argparse.ArgumentParser(description="Enriquecer perfil SimC con datos de Blizzard API")
    parser.add_argument("--perfil", required=True, help="Ruta al archivo .simc")
    parser.add_argument("--client-id", default=os.environ.get("BLIZZARD_CLIENT_ID"))
    parser.add_argument("--client-secret", default=os.environ.get("BLIZZARD_CLIENT_SECRET"))
    parser.add_argument("--region", default="eu")
    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        print("Necesitas BLIZZARD_CLIENT_ID y BLIZZARD_CLIENT_SECRET")
        sys.exit(1)

    # Parsear SimC
    personaje, items = parsear_simc(args.perfil)
    print(f"Personaje: {personaje.get('nombre', '?')}")
    print(f"Items encontrados: {len(items)}")

    # Enriquecer con API
    api = BlizzardAPI(args.client_id, args.client_secret, args.region)
    if not api.autenticar():
        sys.exit(1)

    resultado = enriquecer(api, personaje, items)

    # Guardar
    salida = Path("pizarra/datos/jugadores")
    salida.mkdir(parents=True, exist_ok=True)
    nombre = personaje.get("nombre", "perfil").lower()
    ruta = salida / f"{nombre}.json"

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\n  GUARDADO: {ruta}")
    print(f"  ilvl medio: {resultado['ilvl_medio']}")
    print(f"  Items: {len(resultado['equipo'])}")
    if resultado['personaje']['media']:
        print(f"  Imagen: SI")


if __name__ == "__main__":
    main()
