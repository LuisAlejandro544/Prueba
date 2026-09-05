#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Generación Automatizada de Mapas Mundiales para Juegos de Gran Estrategia en Android.
- Datos geográficos abiertos vectoriales de Natural Earth (Dominio Público).
- Provincias terrestres detalladas y zonas marítimas mundiales completas (Sea Zones navegables).
- Puntos estratégicos navales (Canales de Panamá, Suez, Kiel, Estrechos de Gibraltar, Magallanes, Bósforo, Malaca, etc.).
- Puertos principales y capitales/ciudades clave.
- Islas con realce geométrico para visibilidad táctica en pantallas móviles.
- Tipos de terreno, acceso costero, demografía, producción industrial y recursos históricos en JSON.
- Generación de mapas de imagen (Político, Táctico blanco y Mapa indexado de IDs por píxel RGB).
- Exportación exclusiva para artefactos descargables.
"""

import os
import sys
import re
import json
import math
import sqlite3
import zipfile
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import requests
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely.affinity import scale as shp_scale
from shapely.ops import unary_union
try:
    from shapely.validation import make_valid
except ImportError:
    try:
        from shapely import make_valid
    except ImportError:
        def make_valid(geom):
            return geom.buffer(0)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
from PIL import Image, ImageDraw


class NpEncoder(json.JSONEncoder):
    """Codificador JSON robusto que convierte tipos de NumPy y GeoPandas a tipos primitivos de Python."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super(NpEncoder, self).default(obj)


def sanitize_for_json(data: Any) -> Any:
    """Convierte recursivamente cualquier entero, flotante o colección de NumPy en tipos nativos de Python."""
    if isinstance(data, dict):
        return {str(k): sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(v) for v in data]
    elif isinstance(data, tuple):
        return tuple(sanitize_for_json(v) for v in data)
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return sanitize_for_json(data.tolist())
    elif isinstance(data, np.bool_):
        return bool(data)
    return data


NATURAL_EARTH_MIRRORS = [
    "https://naturalearth.s3.amazonaws.com",
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/zips"
]

# Canales y estrechos estratégicos globales
STRATEGIC_STRAITS = [
    {"id": "STR_PANAMA", "name": "Canal de Panamá", "lat": 9.08, "lon": -79.68, "type": "canal", "connects": ["Mar Caribe", "Océano Pacífico"]},
    {"id": "STR_SUEZ", "name": "Canal de Suez", "lat": 30.58, "lon": 32.34, "type": "canal", "connects": ["Mar Mediterráneo", "Mar Rojo"]},
    {"id": "STR_GIBRALTAR", "name": "Estrecho de Gibraltar", "lat": 35.98, "lon": -5.60, "type": "estrecho", "connects": ["Océano Atlántico Norte", "Mar Mediterráneo"]},
    {"id": "STR_MAGALLANES", "name": "Estrecho de Magallanes", "lat": -53.48, "lon": -70.76, "type": "estrecho", "connects": ["Océano Atlántico Sur", "Océano Pacífico Sur"]},
    {"id": "STR_MALACCA", "name": "Estrecho de Malaca", "lat": 2.50, "lon": 101.50, "type": "estrecho", "connects": ["Océano Índico", "Mar de China Meridional"]},
    {"id": "STR_BOSPHORUS", "name": "Estrecho del Bósforo", "lat": 41.11, "lon": 29.07, "type": "estrecho", "connects": ["Mar de Mármara", "Mar Negro"]},
    {"id": "STR_DARDANELLES", "name": "Estrecho de los Dardanelos", "lat": 40.21, "lon": 26.40, "type": "estrecho", "connects": ["Mar Egeo", "Mar de Mármara"]},
    {"id": "STR_BAB_EL_MANDEB", "name": "Estrecho de Bab el-Mandeb", "lat": 12.58, "lon": 43.33, "type": "estrecho", "connects": ["Mar Rojo", "Golfo de Adén / Océano Índico"]},
    {"id": "STR_HORMUZ", "name": "Estrecho de Ormuz", "lat": 26.56, "lon": 56.25, "type": "estrecho", "connects": ["Golfo Pérsico", "Mar de Omán"]},
    {"id": "STR_DANISH_STRAITS", "name": "Estrechos Daneses (Skagerrak/Kattegat)", "lat": 57.10, "lon": 11.00, "type": "estrecho", "connects": ["Mar del Norte", "Mar Báltico"]},
    {"id": "STR_KIEL", "name": "Canal de Kiel", "lat": 54.30, "lon": 9.85, "type": "canal", "connects": ["Mar del Norte", "Mar Báltico"]},
    {"id": "STR_BERING", "name": "Estrecho de Bering", "lat": 65.80, "lon": -168.90, "type": "estrecho", "connects": ["Océano Pacífico Norte", "Océano Glacial Ártico"]}
]

# Puertos principales mundiales con datos económicos/navales
MAJOR_PORTS = [
    {"name": "Buenos Aires", "country": "ARG", "lat": -34.60, "lon": -58.37, "level": 5, "type": "puerto_comercial_naval"},
    {"name": "Río de Janeiro / Santos", "country": "BRA", "lat": -23.96, "lon": -46.33, "level": 5, "type": "megapuerto"},
    {"name": "Valparaíso", "country": "CHL", "lat": -33.04, "lon": -71.62, "level": 4, "type": "puerto_naval"},
    {"name": "Callao (Lima)", "country": "PER", "lat": -12.05, "lon": -77.14, "level": 4, "type": "puerto_comercial"},
    {"name": "Cartagena", "country": "COL", "lat": 10.39, "lon": -75.51, "level": 4, "type": "puerto_naval"},
    {"name": "Veracruz", "country": "MEX", "lat": 19.17, "lon": -96.13, "level": 4, "type": "puerto_comercial"},
    {"name": "Nueva York", "country": "USA", "lat": 40.71, "lon": -74.00, "level": 5, "type": "megapuerto"},
    {"name": "Los Ángeles / Long Beach", "country": "USA", "lat": 33.74, "lon": -118.27, "level": 5, "type": "megapuerto"},
    {"name": "Norfolk (Base Naval)", "country": "USA", "lat": 36.95, "lon": -76.32, "level": 5, "type": "base_naval"},
    {"name": "Liverpool / Londres", "country": "GBR", "lat": 51.50, "lon": -0.05, "level": 5, "type": "megapuerto"},
    {"name": "Róterdam", "country": "NLD", "lat": 51.92, "lon": 4.47, "level": 5, "type": "megapuerto"},
    {"name": "Hamburgo", "country": "DEU", "lat": 53.54, "lon": 9.99, "level": 5, "type": "megapuerto"},
    {"name": "Marsella", "country": "FRA", "lat": 43.30, "lon": 5.37, "level": 4, "type": "puerto_comercial_naval"},
    {"name": "Brest (Base Naval)", "country": "FRA", "lat": 48.39, "lon": -4.48, "level": 4, "type": "base_naval"},
    {"name": "San Petersburgo / Kronstadt", "country": "RUS", "lat": 59.93, "lon": 30.31, "level": 5, "type": "puerto_naval"},
    {"name": "Sebastopol", "country": "UKR", "lat": 44.61, "lon": 33.52, "level": 5, "type": "base_naval"},
    {"name": "Vladivostok", "country": "RUS", "lat": 43.11, "lon": 131.88, "level": 4, "type": "puerto_naval"},
    {"name": "Shanghái", "country": "CHN", "lat": 31.23, "lon": 121.47, "level": 5, "type": "megapuerto"},
    {"name": "Yokohama / Kure", "country": "JPN", "lat": 35.44, "lon": 139.63, "level": 5, "type": "megapuerto"},
    {"name": "Singapur", "country": "SGP", "lat": 1.29, "lon": 103.85, "level": 5, "type": "megapuerto"},
    {"name": "Alejandría", "country": "EGY", "lat": 31.20, "lon": 29.91, "level": 4, "type": "puerto_naval"},
    {"name": "Ciudad del Cabo", "country": "ZAF", "lat": -33.92, "lon": 18.42, "level": 4, "type": "puerto_comercial_naval"},
    {"name": "Sídney", "country": "AUS", "lat": -33.86, "lon": 151.20, "level": 4, "type": "puerto_naval"},
    {"name": "Bombay (Mumbai)", "country": "IND", "lat": 18.94, "lon": 72.83, "level": 5, "type": "megapuerto"}
]

# Capitales mundiales destacadas
MAJOR_CAPITALS = {
    "ARG": {"name": "Buenos Aires", "lat": -34.60, "lon": -58.37},
    "BRA": {"name": "Brasilia / Río de Janeiro", "lat": -15.79, "lon": -47.88},
    "CHL": {"name": "Santiago", "lat": -33.44, "lon": -70.66},
    "COL": {"name": "Bogotá", "lat": 4.71, "lon": -74.07},
    "PER": {"name": "Lima", "lat": -12.04, "lon": -77.04},
    "MEX": {"name": "Ciudad de México", "lat": 19.43, "lon": -99.13},
    "VEN": {"name": "Caracas", "lat": 10.48, "lon": -66.90},
    "BOL": {"name": "La Paz / Sucre", "lat": -16.50, "lon": -68.15},
    "PRY": {"name": "Asunción", "lat": -25.26, "lon": -57.57},
    "URY": {"name": "Montevideo", "lat": -34.90, "lon": -56.16},
    "ECU": {"name": "Quito", "lat": -0.18, "lon": -78.46},
    "CUB": {"name": "La Habana", "lat": 23.11, "lon": -82.36},
    "USA": {"name": "Washington D.C.", "lat": 38.90, "lon": -77.03},
    "CAN": {"name": "Ottawa", "lat": 45.42, "lon": -75.69},
    "GBR": {"name": "Londres", "lat": 51.50, "lon": -0.12},
    "FRA": {"name": "París", "lat": 48.85, "lon": 2.35},
    "DEU": {"name": "Berlín", "lat": 52.52, "lon": 13.40},
    "RUS": {"name": "Moscú", "lat": 55.75, "lon": 37.61},
    "ITA": {"name": "Roma", "lat": 41.90, "lon": 12.49},
    "ESP": {"name": "Madrid", "lat": 40.41, "lon": -3.70},
    "CHN": {"name": "Pekín (Beijing)", "lat": 39.90, "lon": 116.40},
    "JPN": {"name": "Tokio", "lat": 35.67, "lon": 139.65},
    "IND": {"name": "Nueva Delhi", "lat": 28.61, "lon": 77.20},
    "TUR": {"name": "Ankara", "lat": 39.93, "lon": 32.85},
    "EGY": {"name": "El Cairo", "lat": 30.04, "lon": 31.23},
    "ZAF": {"name": "Pretoria", "lat": -25.74, "lon": 28.22},
    "AUS": {"name": "Canberra", "lat": -35.28, "lon": 149.13}
}

# Paleta militar y de gran estrategia inspirada en Hearts of Iron IV y juegos de estrategia bélica
HISTORICAL_COUNTRY_COLORS = {
    "ARG": "#0284c7", # Celeste patagónico táctico Argentina
    "BRA": "#15803d", # Verde selva esmeralda Brasil
    "CHL": "#b91c1c", # Rojo andino Chile
    "COL": "#ca8a04", # Amarillo tostado Colombia
    "PER": "#991b1b", # Carmesí Perú
    "MEX": "#047857", # Verde militar México
    "VEN": "#c2410c", # Ocre tostado Venezuela
    "BOL": "#65a30d", # Verde oliva Bolivia
    "PRY": "#dc2626", # Rojo Paraguay
    "URY": "#0284c7", # Azul celeste Uruguay
    "ECU": "#d97706", # Dorado Ecuador
    "CUB": "#1d4ed8", # Azul Caribe Cuba
    "DOM": "#2563eb", # Azul República Dominicana
    "GTM": "#0369a1", # Azul Guatemala
    "HND": "#1d4ed8", # Azul Honduras
    "SLV": "#1e40af", # Azul Salvador
    "NIC": "#0284c7", # Celeste Nicaragua
    "CRI": "#065f46", # Verde Costa Rica
    "PAN": "#991b1b", # Rojo Panamá
    "USA": "#1e3a8a", # Azul naval profundo Estados Unidos
    "CAN": "#be123c", # Rojo salmón Canadá
    "GBR": "#881337", # Rojo imperial británico / Borgoña
    "FRA": "#1d4ed8", # Azul horizonte Francia
    "DEU": "#3f4854", # Gris feldgrau Alemania
    "RUS": "#991b1b", # Rojo carmesí profundo Rusia / URSS
    "CHN": "#b45309", # Amarillo mostaza táctico China
    "JPN": "#f43f5e", # Carmesí sol naciente Japón
    "ITA": "#166534", # Verde alpino militar Italia
    "ESP": "#d97706", # Gualda / Amarillo tostado España
    "PRT": "#065f46", # Verde oscuro Portugal
    "TUR": "#7e22ce", # Púrpura otomano Turquía
    "EGY": "#a16207", # Ocre desierto Egipto
    "ZAF": "#0f766e", # Verde petróleo Sudáfrica
    "IND": "#0891b2", # Turquesa Raj británico / India
    "AUS": "#92400e", # Caqui australiano
    "SAU": "#4d7c0f", # Verde oliva oscuro Arabia
    "IRN": "#854d0e", # Mostaza persa Irán
    "SWE": "#0369a1", # Azul nórdico Suecia
    "NOR": "#991b1b", # Rojo fiordo Noruega
    "FIN": "#e2e8f0", # Blanco / Gris invernal Finlandia
    "POL": "#be123c", # Rosa militar Polonia
    "UKR": "#ca8a04"  # Amarillo estepa Ucrania
}

COUNTRY_PALETTE = [
    "#1e40af", "#991b1b", "#166534", "#ca8a04", "#6b21a8",
    "#be123c", "#0f766e", "#c2410c", "#4338ca", "#4d7c0f",
    "#0891b2", "#881337", "#7e22ce", "#a16207", "#065f46",
    "#1d4ed8", "#b91c1c", "#581c87", "#9a3412", "#0e7490",
    "#3730a3", "#3f6212", "#831843", "#115e59", "#854d0e"
]

SEA_ZONE_PALETTE = [
    "#0a192f", "#0d2238", "#112a45", "#133152", "#173b61",
    "#0f2b48", "#15355b", "#183e6b", "#1b4475", "#0c243f"
]


def download_file(url_list: List[str], dest_path: Path) -> bool:
    """Descarga un archivo intentando varios espejos si alguno falla."""
    headers = {'User-Agent': 'StrategyGame-MapGenerator/2.0 (Open-Source Project)'}
    for base_url in url_list:
        full_url = f"{base_url}/{dest_path.name}"
        print(f"[Descarga] Intentando: {full_url}")
        try:
            response = requests.get(full_url, headers=headers, timeout=60, stream=True)
            if response.status_code == 200:
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=65536):
                        f.write(chunk)
                print(f"[Descarga] Completado exitosamente: {dest_path.name} ({dest_path.stat().st_size / 1024 / 1024:.2f} MB)")
                return True
            else:
                print(f"[Descarga] Código HTTP {response.status_code} desde {base_url}")
        except Exception as e:
            print(f"[Descarga] Error conectando a {base_url}: {e}")
    return False


def get_shapefile_path(cache_dir: Path, scale: str, dataset_name: str, category: str = "cultural") -> Path:
    """Asegura la existencia y extracción del Shapefile correspondiente."""
    filename = f"ne_{scale}_{dataset_name}.zip"
    zip_path = cache_dir / filename
    extract_folder = cache_dir / f"ne_{scale}_{dataset_name}"

    if not extract_folder.exists() or not any(extract_folder.glob("*.shp")):
        extract_folder.mkdir(parents=True, exist_ok=True)
        if not zip_path.exists():
            urls = [
                f"{mirror}/{scale}_{category}"
                for mirror in NATURAL_EARTH_MIRRORS
            ]
            success = download_file(urls, zip_path)
            if not success:
                print(f"[Advertencia] No se pudo descargar {filename} en categoría {category}. Probando categoría alternativa...")
                alt_category = "physical" if category == "cultural" else "cultural"
                urls_alt = [f"{mirror}/{scale}_{alt_category}" for mirror in NATURAL_EARTH_MIRRORS]
                success = download_file(urls_alt, zip_path)
                if not success:
                    raise RuntimeError(f"No se pudo descargar el conjunto de datos {filename}.")

        print(f"[Extracción] Descomprimiendo {zip_path.name}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)

    shp_files = list(extract_folder.glob("*.shp"))
    if not shp_files:
        raise FileNotFoundError(f"No se encontró ningún archivo .shp en {extract_folder}")
    return shp_files[0]


def try_get_shapefile_path(cache_dir: Path, scale: str, dataset_name: str, category: str = "cultural") -> Optional[Path]:
    """Intenta descargar y extraer un shapefile opcional de Natural Earth. Retorna None si no está disponible."""
    try:
        return get_shapefile_path(cache_dir, scale, dataset_name, category)
    except Exception as e:
        print(f"[Dataset Opcional] '{dataset_name}' no se pudo cargar a escala {scale}: {e}")
        return None


def id_to_rgb(numeric_id: int) -> Tuple[int, int, int]:
    """Convierte un ID numérico en un color RGB único para muestreo exacto en el mapa."""
    r = numeric_id % 256
    g = (numeric_id // 256) % 256
    b = (numeric_id // 65536) % 256
    return (r, g, b)


def rgb_to_id(r: int, g: int, b: int) -> int:
    """Convierte un color RGB extraído del mapa al ID original."""
    return r + (g * 256) + (b * 65536)


def lat_lon_to_pixel(lat: float, lon: float, width: int, height: int, min_lat: float, max_lat: float) -> Tuple[int, int]:
    """Convierte coordenadas geográficas WGS84 (lat/lon) a píxeles según el rango vertical acotado."""
    x = int(((lon + 180.0) / 360.0) * width)
    lat_span = max_lat - min_lat
    y = int(((max_lat - lat) / lat_span) * height)
    x = max(0, min(width - 1, x))
    y = max(0, min(height - 1, y))
    return (x, y)


# Diccionario canónico exhaustivo de normalización geopolítica para entidades sin código ISO estándar en Natural Earth
CANONICAL_COUNTRY_MAP: Dict[str, str] = {
    "brazil": "BRA",
    "brasil": "BRA",
    "france": "FRA",
    "francia": "FRA",
    "norway": "NOR",
    "noruega": "NOR",
    "united states of america": "USA",
    "united states": "USA",
    "estados unidos": "USA",
    "somalia": "SOM",
    "somaliland": "SOM",
    "kosovo": "XKX",
    "northern cyprus": "CYN",
    "cyprus": "CYP",
    "chipre": "CYP",
    "western sahara": "ESH",
    "sahara occidental": "ESH",
    "south sudan": "SSD",
    "sudan del sur": "SSD",
    "taiwan": "TWN",
    "palestine": "PSE",
    "palestina": "PSE",
    "west bank": "PSE",
    "gaza": "PSE",
    "vatican": "VAT",
    "holy see": "VAT",
    "san marino": "SMR",
    "monaco": "MCO",
    "liechtenstein": "LIE",
    "andorra": "AND",
    "malta": "MLT",
    "singapore": "SGP",
    "bahrain": "BHR",
    "luxembourg": "LUX",
    "luxemburgo": "LUX",
    "timor-leste": "TLS",
    "east timor": "TLS",
    "hong kong": "HKG",
    "macao": "MAC",
    "macau": "MAC",
    "puerto rico": "PRI",
    "greenland": "GRL",
    "groenlandia": "GRL",
    "falkland islands": "FLK",
    "islas malvinas": "FLK",
    "french guiana": "GUF",
    "guayana francesa": "GUF",
    "new caledonia": "NCL",
    "nueva caledonia": "NCL",
    "guam": "GUM",
    "united kingdom": "GBR",
    "reino unido": "GBR",
    "democratic republic of the congo": "COD",
    "dem. rep. congo": "COD",
    "republic of the congo": "COG",
    "congo": "COG",
    "central african republic": "CAF",
    "republica centroafricana": "CAF",
    "ivory coast": "CIV",
    "cote d'ivoire": "CIV",
    "eswatini": "SWZ",
    "swaziland": "SWZ",
    "north macedonia": "MKD",
    "macedonia": "MKD",
    "bosnia and herzegovina": "BIH",
    "czech republic": "CZE",
    "czechia": "CZE",
    "dominican republic": "DOM",
    "republica dominicana": "DOM",
    "myanmar": "MMR",
}


def normalize_iso(raw_iso: Any, admin_name: str, fallback_prefix: str = "CTY") -> str:
    """Normaliza y rescata códigos ISO para evitar valores nulos, '-99' o fallas entre capas."""
    iso = str(raw_iso).strip().upper() if raw_iso is not None else ""
    if iso and iso not in ("-99", "NONE", "NAN", "NULL", "UNK", ""):
        return iso

    name_clean = str(admin_name).strip().lower()
    for pattern, code in CANONICAL_COUNTRY_MAP.items():
        if pattern in name_clean:
            return code

    # Si no está en el diccionario, generar un código alfanumérico determinista
    alpha_only = re.sub(r'[^A-Z]', '', name_clean.upper())
    if len(alpha_only) >= 3:
        return f"{fallback_prefix}_{alpha_only[:4]}"
    return f"{fallback_prefix}_{abs(hash(name_clean)) % 10000}"


def safe_clean_geometry(geom):
    """
    Sanea, repara y valida geometrías sin descartar provincias o islas por leves
    inconsistencias topológicas de Shapely.
    """
    if geom is None or geom.is_empty:
        return None
    try:
        if not geom.is_valid:
            geom = make_valid(geom)
    except Exception:
        try:
            geom = geom.buffer(0)
        except Exception:
            pass
    if geom is None or geom.is_empty:
        return None
    if geom.geom_type in ('Polygon', 'MultiPolygon'):
        return geom
    elif geom.geom_type == 'GeometryCollection':
        polys = [g for g in geom.geoms if g.geom_type in ('Polygon', 'MultiPolygon') and not g.is_empty]
        if polys:
            try:
                return unary_union(polys)
            except Exception:
                return MultiPolygon(polys) if len(polys) > 1 else polys[0]
    return None


def enhance_small_islands(geometry, min_area: float = 0.08, scale_factor: float = 2.4):
    """
    Realza geométricamente islas pequeñas e importantes para que no desaparezcan
    en pantallas de teléfonos móviles ni queden como píxeles invisibles.
    Garantiza que la provincia nunca se invalide ni se pierda.
    """
    if geometry is None or geometry.is_empty:
        return geometry

    try:
        if geometry.geom_type == 'Polygon':
            if geometry.area < min_area:
                scaled = shp_scale(geometry, xfact=scale_factor, yfact=scale_factor, origin='centroid')
                return safe_clean_geometry(scaled) or geometry
            return geometry
        elif geometry.geom_type == 'MultiPolygon':
            new_polys = []
            for poly in geometry.geoms:
                if poly.is_empty:
                    continue
                if poly.area < min_area:
                    scaled = shp_scale(poly, xfact=scale_factor, yfact=scale_factor, origin='centroid')
                    clean_s = safe_clean_geometry(scaled)
                    if clean_s is not None and not clean_s.is_empty:
                        new_polys.append(clean_s)
                    else:
                        new_polys.append(poly)
                else:
                    new_polys.append(poly)
            if not new_polys:
                return geometry
            try:
                union_geom = unary_union(new_polys)
                return safe_clean_geometry(union_geom) or geometry
            except Exception:
                return MultiPolygon(new_polys)
    except Exception:
        return geometry
    return geometry


def estimate_province_attributes(name: str, country_iso: str, lat: float, lon: float, is_coastal: bool, physical_terrain: Optional[str] = None, measured_population: Optional[int] = None) -> Dict[str, Any]:
    """
    Estima atributos históricos, demográficos y de terreno realistas y listos para modificar en mods.
    Si se dispone de terreno físico determinado por intersección espacial o población medida, se priorizan.
    """
    # 1. Terreno basado en regiones físicas reales si está disponible, o en geografía histórica
    if physical_terrain:
        terrain = physical_terrain
    else:
        name_l = name.lower()
        if any(k in name_l for k in ["mountain", "andes", "cordillera", "alps", "alpes", "sierra", "tibet", "himalaya", "caucasus"]):
            terrain = "mountains"
        elif (-55 <= lat <= 15 and -75 <= lon <= -65) or (35 <= lat <= 50 and 6 <= lon <= 15) or (25 <= lat <= 40 and 70 <= lon <= 100):
            terrain = "mountains"
        elif (-10 <= lat <= 5 and -75 <= lon <= -50) or (-5 <= lat <= 5 and 10 <= lon <= 30) or (-10 <= lat <= 10 and 95 <= lon <= 140):
            terrain = "jungle"
        elif (15 <= lat <= 35 and -15 <= lon <= 55) or (-30 <= lat <= -20 and 15 <= lon <= 30) or (-30 <= lat <= -20 and 120 <= lon <= 140):
            terrain = "desert"
        elif lat > 60:
            terrain = "tundra"
        elif any(k in name_l for k in ["hills", "colinas", "morro", "highland"]):
            terrain = "hills"
        else:
            terrain = "plains" if not is_coastal else "coastal_plains"

    # 2. Demografía y Mano de obra estimada (Manpower)
    if measured_population and measured_population > 0:
        base_population = measured_population
    else:
        base_population = 250000 + (abs(hash(name)) % 1500000)
        if country_iso in ["CHN", "IND"]:
            base_population *= 4
        elif country_iso in ["USA", "RUS", "BRA", "DEU", "JPN"]:
            base_population *= 2
        elif terrain in ["desert", "tundra", "mountains"]:
            base_population = max(30000, base_population // 4)

    manpower = int(base_population * 0.12)

    # 3. Recursos históricos
    name_l = name.lower()
    if any(k in name_l for k in ["texas", "alaska", "maracaibo", "zulia", "baku", "khuzestan", "al-ahsa", "siberia", "kuwait"]):
        resource = "oil"
        resource_amount = 80
    elif any(k in name_l for k in ["antofagasta", "katanga", "potosi", "minas gerais", "kiruna", "lorraine", "ruhr", "donbas", "shansi"]):
        resource = "iron_and_metals"
        resource_amount = 75
    elif terrain in ["jungle"]:
        resource = "rubber_and_wood"
        resource_amount = 50
    elif terrain in ["plains", "coastal_plains"]:
        resource = "agriculture"
        resource_amount = 60
    else:
        resource = "livestock"
        resource_amount = 30

    # 4. Nivel industrial
    if country_iso in ["USA", "GBR", "DEU", "FRA", "JPN", "RUS", "ITA"]:
        industrial_level = 3 + (abs(hash(name)) % 6)
    elif country_iso in ["ARG", "BRA", "CAN", "AUS", "ESP", "SWE", "CHN", "IND"]:
        industrial_level = 2 + (abs(hash(name)) % 4)
    else:
        industrial_level = 1 + (abs(hash(name)) % 3)

    return {
        "terrain": terrain,
        "population": base_population,
        "manpower": manpower,
        "resource": resource,
        "resource_amount": resource_amount,
        "industrial_level": industrial_level
    }


def build_world_map(scale: str, width: int, height: int, output_dir: Path, exclude_antarctica: bool = True):
    """
    Construye el ecosistema completo de mapas terrestres y navales, puntos estratégicos y datasets estructurados.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("GENERADOR PROFESIONAL DE MAPA MUNDIAL: TIERRA, MARES Y ESTRATEGIA")
    print(f"Escala: {scale} | Resolución: {width}x{height} | Sin Antártida: {exclude_antarctica}")
    print("=" * 65)

    # 1. Cargar Provincias Terrestres (Admin 1)
    admin1_shp = get_shapefile_path(cache_dir, scale, "admin_1_states_provinces", category="cultural")
    print(f"[Datos] Cargando provincias terrestres desde: {admin1_shp.name}")
    gdf_provinces = gpd.read_file(admin1_shp).to_crs(epsg=4326)

    # 2. Cargar Países Soberanos (Admin 0)
    admin0_shp = get_shapefile_path(cache_dir, scale, "admin_0_countries", category="cultural")
    print(f"[Datos] Cargando países soberanos desde: {admin0_shp.name}")
    gdf_countries = gpd.read_file(admin0_shp).to_crs(epsg=4326)

    # 3. Cargar Zonas Marítimas (Marine Polygons - Océanos, Mares y Golfos)
    marine_shp = get_shapefile_path(cache_dir, scale, "geography_marine_polys", category="physical")
    print(f"[Datos] Cargando zonas marítimas y océanos desde: {marine_shp.name}")
    gdf_seas = gpd.read_file(marine_shp).to_crs(epsg=4326)

    # --- Datasets Adicionales de Enriquecimiento Cartográfico Profundo ---
    # 3.1 Polígono continuo del Océano Global
    ocean_shp = try_get_shapefile_path(cache_dir, scale, "ocean", category="physical")
    gdf_ocean = gpd.read_file(ocean_shp).to_crs(epsg=4326) if ocean_shp else None
    if gdf_ocean is not None:
        print(f"[Datos Adicionales] Océano global cargado: {len(gdf_ocean)} geometrías")

    # 3.2 Lagos Interiores Mundiales (Grandes Lagos, Baikal, Caspio, Victoria, etc.)
    lakes_shp = try_get_shapefile_path(cache_dir, scale, "lakes", category="physical")
    gdf_lakes = gpd.read_file(lakes_shp).to_crs(epsg=4326) if lakes_shp else None
    if gdf_lakes is not None:
        print(f"[Datos Adicionales] Lagos mundiales cargados: {len(gdf_lakes)} masas lacustres")

    # 3.3 Red Hidrográfica de Ríos Navegables y Estratégicos
    rivers_shp = try_get_shapefile_path(cache_dir, scale, "rivers_lake_centerlines", category="physical")
    gdf_rivers = gpd.read_file(rivers_shp).to_crs(epsg=4326) if rivers_shp else None
    if gdf_rivers is not None:
        print(f"[Datos Adicionales] Red fluvial cargada: {len(gdf_rivers)} tramos de ríos")

    # 3.4 Ciudades y Asentamientos Urbanos (Populated Places con demografía real)
    places_shp = try_get_shapefile_path(cache_dir, scale, "populated_places", category="cultural")
    gdf_places = gpd.read_file(places_shp).to_crs(epsg=4326) if places_shp else None
    if gdf_places is not None:
        print(f"[Datos Adicionales] Ciudades y núcleos urbanos cargados: {len(gdf_places)} urbes")

    # 3.5 Puertos Marítimos Reales de Natural Earth
    ports_shp = try_get_shapefile_path(cache_dir, scale, "ports", category="cultural")
    gdf_ports = gpd.read_file(ports_shp).to_crs(epsg=4326) if ports_shp else None
    if gdf_ports is not None:
        print(f"[Datos Adicionales] Puertos marítimos oficiales cargados: {len(gdf_ports)} puertos")

    # 3.6 Líneas Oficiales de Frontera Terrestre Internacional
    admin0_lines_shp = try_get_shapefile_path(cache_dir, scale, "admin_0_boundary_lines_land", category="cultural")
    gdf_admin0_lines = gpd.read_file(admin0_lines_shp).to_crs(epsg=4326) if admin0_lines_shp else None

    # 3.7 Líneas Oficiales de Límites Provinciales/Estatales
    admin1_lines_shp = try_get_shapefile_path(cache_dir, scale, "admin_1_states_provinces_lines", category="cultural")
    gdf_admin1_lines = gpd.read_file(admin1_lines_shp).to_crs(epsg=4326) if admin1_lines_shp else None

    # 3.8 Regiones y Accidentes Físicos (Desiertos, Selvas, Cordilleras, Altiplanos)
    regions_shp = try_get_shapefile_path(cache_dir, scale, "geography_regions_polys", category="physical")
    gdf_regions = gpd.read_file(regions_shp).to_crs(epsg=4326) if regions_shp else None
    if gdf_regions is not None:
        print(f"[Datos Adicionales] Regiones físicas mundiales cargadas: {len(gdf_regions)} zonas")

    # 3.9 Línea de Costa de Alta Definición (Coastline)
    coastline_shp = try_get_shapefile_path(cache_dir, scale, "coastline", category="physical")
    gdf_coastline = gpd.read_file(coastline_shp).to_crs(epsg=4326) if coastline_shp else None
    if gdf_coastline is not None:
        print(f"[Datos Adicionales] Línea de costa de alta precisión cargada: {len(gdf_coastline)} segmentos")

    # 3.10 Glaciares, Campos de Hielo y Nieves Perpetuas (Glaciated Areas)
    glaciers_shp = try_get_shapefile_path(cache_dir, scale, "glaciated_areas", category="physical")
    gdf_glaciers = gpd.read_file(glaciers_shp).to_crs(epsg=4326) if glaciers_shp else None
    if gdf_glaciers is not None:
        print(f"[Datos Adicionales] Campos de hielo y glaciares cargados: {len(gdf_glaciers)} áreas")

    # 3.11 Red Ferroviaria y Rutas de Suministro Bélico (Railroads)
    railroads_shp = try_get_shapefile_path(cache_dir, scale, "railroads", category="cultural")
    gdf_railroads = gpd.read_file(railroads_shp).to_crs(epsg=4326) if railroads_shp else None
    if gdf_railroads is not None:
        print(f"[Datos Adicionales] Red ferroviaria mundial cargada: {len(gdf_railroads)} tramos logísticos")

    # 3.12 Bases Aéreas y Aeropuertos Mundiales (Airports)
    airports_shp = try_get_shapefile_path(cache_dir, scale, "airports", category="cultural")
    gdf_airports = gpd.read_file(airports_shp).to_crs(epsg=4326) if airports_shp else None
    if gdf_airports is not None:
        print(f"[Datos Adicionales] Bases aéreas y aeropuertos mundiales cargados: {len(gdf_airports)} aeródromos")

    # 3.13 Manchas Urbanas e Industriales (Urban Areas)
    urban_shp = try_get_shapefile_path(cache_dir, scale, "urban_areas", category="cultural")
    gdf_urban = gpd.read_file(urban_shp).to_crs(epsg=4326) if urban_shp else None
    if gdf_urban is not None:
        print(f"[Datos Adicionales] Áreas urbanas e industriales cargadas: {len(gdf_urban)} urbes")

    # 3.14 Líneas Geográficas Tácticas y Cuadrícula Náutica de Almirantazgo
    geolines_shp = try_get_shapefile_path(cache_dir, scale, "geographic_lines", category="physical")
    gdf_geolines = gpd.read_file(geolines_shp).to_crs(epsg=4326) if geolines_shp else None

    graticules_shp = try_get_shapefile_path(cache_dir, scale, "graticules_10", category="physical")
    gdf_graticules = gpd.read_file(graticules_shp).to_crs(epsg=4326) if graticules_shp else None

    reefs_shp = try_get_shapefile_path(cache_dir, scale, "reefs", category="physical")
    gdf_reefs = gpd.read_file(reefs_shp).to_crs(epsg=4326) if reefs_shp else None

    # 4. Filtrar Antártida y acotar coordenadas de juego
    if exclude_antarctica:
        print("[Geometría] Excluyendo Antártida y acotando latitudes (-60°S a 84°N)...")
        gdf_provinces = gdf_provinces[
            ~gdf_provinces['admin'].astype(str).str.contains('Antarctica|Antártida', case=False, na=False) &
            ~gdf_provinces['adm0_a3'].astype(str).str.contains('ATA', case=False, na=False)
        ]
        gdf_countries = gdf_countries[
            ~gdf_countries['ADMIN'].astype(str).str.contains('Antarctica|Antártida', case=False, na=False) &
            ~gdf_countries['ISO_A3'].astype(str).str.contains('ATA', case=False, na=False) &
            ~gdf_countries['ADM0_A3'].astype(str).str.contains('ATA', case=False, na=False)
        ]
        gdf_seas = gdf_seas[
            ~gdf_seas['name'].astype(str).str.contains('Southern Ocean|Antarctic', case=False, na=False)
        ]

        min_lat, max_lat = -60.0, 84.0
        bounding_box = box(-180.0, min_lat, 180.0, max_lat)
        gdf_provinces = gdf_provinces.clip(bounding_box)
        gdf_countries = gdf_countries.clip(bounding_box)
        gdf_seas = gdf_seas.clip(bounding_box)
        if gdf_ocean is not None:
            try:
                gdf_ocean = gdf_ocean.clip(bounding_box)
            except Exception:
                pass
        if gdf_lakes is not None:
            try:
                gdf_lakes = gdf_lakes.clip(bounding_box)
            except Exception:
                pass
        if gdf_rivers is not None:
            try:
                gdf_rivers = gdf_rivers.clip(bounding_box)
            except Exception:
                pass
        if gdf_places is not None:
            try:
                gdf_places = gdf_places.cx[:, min_lat:max_lat]
            except Exception:
                pass
        if gdf_regions is not None:
            try:
                gdf_regions = gdf_regions.clip(bounding_box)
            except Exception:
                pass
        if gdf_coastline is not None:
            try:
                gdf_coastline = gdf_coastline.clip(bounding_box)
            except Exception:
                pass
        if gdf_glaciers is not None:
            try:
                gdf_glaciers = gdf_glaciers.clip(bounding_box)
            except Exception:
                pass
        if gdf_railroads is not None:
            try:
                gdf_railroads = gdf_railroads.clip(bounding_box)
            except Exception:
                pass
        if gdf_airports is not None:
            try:
                gdf_airports = gdf_airports.cx[:, min_lat:max_lat]
            except Exception:
                pass
        if gdf_urban is not None:
            try:
                gdf_urban = gdf_urban.clip(bounding_box)
            except Exception:
                pass
        if gdf_geolines is not None:
            try:
                gdf_geolines = gdf_geolines.clip(bounding_box)
            except Exception:
                pass
        if gdf_graticules is not None:
            try:
                gdf_graticules = gdf_graticules.clip(bounding_box)
            except Exception:
                pass
        if gdf_reefs is not None:
            try:
                gdf_reefs = gdf_reefs.clip(bounding_box)
            except Exception:
                pass
    else:
        min_lat, max_lat = -90.0, 90.0

    # 5. Realce de islas pequeñas para legibilidad táctica en dispositivos móviles
    print("[Geometría] Optimizando geometría de islas pequeñas para visibilidad táctica en móvil...")
    gdf_provinces['geometry'] = gdf_provinces['geometry'].apply(enhance_small_islands)

    # Saneamiento topológico sin descarte de provincias válidas (previene huecos en EE.UU., Canadá o Rusia)
    print("[Geometría] Saneando topología de capas para evitar pérdida de entidades territoriales...")
    gdf_provinces['geometry'] = gdf_provinces['geometry'].apply(safe_clean_geometry)
    gdf_countries['geometry'] = gdf_countries['geometry'].apply(safe_clean_geometry)
    gdf_seas['geometry'] = gdf_seas['geometry'].apply(safe_clean_geometry)

    gdf_provinces = gdf_provinces[gdf_provinces.geometry.notnull() & ~gdf_provinces.geometry.is_empty].copy()
    gdf_countries = gdf_countries[gdf_countries.geometry.notnull() & ~gdf_countries.geometry.is_empty].copy()
    gdf_seas = gdf_seas[gdf_seas.geometry.notnull() & ~gdf_seas.geometry.is_empty].copy()

    if gdf_lakes is not None:
        gdf_lakes['geometry'] = gdf_lakes['geometry'].apply(safe_clean_geometry)
        gdf_lakes = gdf_lakes[gdf_lakes.geometry.notnull() & ~gdf_lakes.geometry.is_empty].copy()

    if gdf_ocean is not None:
        gdf_ocean['geometry'] = gdf_ocean['geometry'].apply(safe_clean_geometry)
        gdf_ocean = gdf_ocean[gdf_ocean.geometry.notnull() & ~gdf_ocean.geometry.is_empty].copy()

    total_provinces = len(gdf_provinces)
    total_countries = len(gdf_countries)
    total_seas = len(gdf_seas)
    print(f"[Estadísticas] Provincias terrestres: {total_provinces}")
    print(f"[Estadísticas] Zonas marítimas: {total_seas}")
    print(f"[Estadísticas] Países/Entidades soberanas: {total_countries}")

    # 6. Estructurar Países y Diccionario
    countries_dict: Dict[str, Any] = {}
    country_color_map: Dict[str, str] = {}
    country_name_to_id: Dict[str, str] = {}
    country_id_to_geom: Dict[str, Any] = {}

    for idx, row in gdf_countries.iterrows():
        name = str(row.get('NAME', row.get('ADMIN', f'País {idx}'))).strip()

        # Jerarquía exhaustiva para obtener el código ISO de 3 letras real
        iso_val = row.get('ISO_A3')
        if not iso_val or str(iso_val).strip() in ("-99", "NONE", "NAN", "NULL", "UNK", ""):
            iso_val = row.get('ISO_A3_EH')
        if not iso_val or str(iso_val).strip() in ("-99", "NONE", "NAN", "NULL", "UNK", ""):
            iso_val = row.get('ADM0_A3')
        if not iso_val or str(iso_val).strip() in ("-99", "NONE", "NAN", "NULL", "UNK", ""):
            iso_val = row.get('GU_A3')
        if not iso_val or str(iso_val).strip() in ("-99", "NONE", "NAN", "NULL", "UNK", ""):
            iso_val = row.get('SOV_A3')

        iso_a3 = normalize_iso(iso_val, name, fallback_prefix="CTY")

        if iso_a3 in HISTORICAL_COUNTRY_COLORS:
            country_color = HISTORICAL_COUNTRY_COLORS[iso_a3]
        else:
            color_idx = abs(hash(iso_a3)) % len(COUNTRY_PALETTE)
            country_color = COUNTRY_PALETTE[color_idx]

        country_color_map[iso_a3] = country_color
        country_name_to_id[name.lower()] = iso_a3

        # Indexar variantes de nombre para emparejamiento exacto con Admin 1
        for col_name in ['ADMIN', 'NAME_LONG', 'FORMAL_EN', 'SOVEREIGNT']:
            val = str(row.get(col_name, '')).strip().lower()
            if val and val not in ("none", "nan", "-99", "null"):
                country_name_to_id[val] = iso_a3

        country_id_to_geom[iso_a3] = row.geometry

        countries_dict[iso_a3] = {
            "id": iso_a3,
            "name": name,
            "iso_a2": str(row.get('ISO_A2', '')).strip(),
            "iso_a3": iso_a3,
            "continent": str(row.get('CONTINENT', 'Desconocido')).strip(),
            "subregion": str(row.get('SUBREGION', 'Desconocido')).strip(),
            "color_hex": country_color,
            "provinces": [],
            "major_ports": [],
            "capital": MAJOR_CAPITALS.get(iso_a3, None)
        }

    # 7. Procesar Zonas Marítimas (Sea Zones) con IDs a partir de 10000
    print("[Mares] Indexando zonas marítimas navegables...")
    sea_zones_list: List[Dict[str, Any]] = []
    gdf_seas = gdf_seas.reset_index(drop=True)
    sea_colors_political = []
    sea_id_colors = []

    for idx, row in gdf_seas.iterrows():
        sea_id = 10001 + idx # ID a partir de 10001 para zonas marítimas
        sea_name = str(row.get('name', row.get('name_en', f'Zona Marítima {idx+1}'))).strip()
        featurecla = str(row.get('featurecla', 'sea')).strip()

        centroid = row.geometry.centroid
        lat, lon = float(centroid.y), float(centroid.x)
        px, py = lat_lon_to_pixel(lat, lon, width, height, min_lat, max_lat)

        r, g, b = id_to_rgb(sea_id)
        id_hex = f"#{r:02x}{g:02x}{b:02x}"
        sea_id_colors.append(id_hex)

        # Color visual para el mapa político/táctico
        palette_idx = abs(hash(sea_name)) % len(SEA_ZONE_PALETTE)
        sea_color_vis = SEA_ZONE_PALETTE[palette_idx]
        sea_colors_political.append(sea_color_vis)

        sea_data = {
            "id": sea_id,
            "name": sea_name,
            "type": featurecla,
            "color_rgb": {"r": r, "g": g, "b": b, "hex": id_hex},
            "center": {
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "pixel_x": px,
                "pixel_y": py
            },
            "bounds": [round(c, 4) for c in row.geometry.bounds],
            "adjacent_seas": [],
            "adjacent_provinces": []
        }
        sea_zones_list.append(sea_data)

    # 8. Adyacencias entre Zonas Marítimas
    print("[Mares] Calculando conexiones entre mares vecinos...")
    sea_sindex = gdf_seas.sindex
    for i, row in gdf_seas.iterrows():
        geom = row.geometry
        cand_idx = list(sea_sindex.intersection(geom.bounds))
        sea_neighbors = []
        for c in cand_idx:
            c_idx = int(c)
            if c_idx != int(i) and geom.touches(gdf_seas.geometry.iloc[c_idx]):
                sea_neighbors.append(int(10001 + c_idx))
        sea_zones_list[i]["adjacent_seas"] = sorted(sea_neighbors)

    # 9. Procesar Provincias Terrestres y Conexión Costa-Mar
    print("[Procesando] Verificando cobertura global y normalizando provincias terrestres...")

    # Mapeo previo para detectar qué países de countries_dict ya tienen provincias en gdf_provinces
    assigned_countries = set()
    for _, prov_row in gdf_provinces.iterrows():
        p_raw_iso = prov_row.get('adm0_a3', prov_row.get('iso_a2', ''))
        p_admin = str(prov_row.get('admin', prov_row.get('adm0_name', ''))).strip()
        p_iso = normalize_iso(p_raw_iso, p_admin)
        if p_iso in countries_dict:
            assigned_countries.add(p_iso)
        elif p_admin.lower() in country_name_to_id:
            assigned_countries.add(country_name_to_id[p_admin.lower()])
        else:
            for c_name_key, c_id_val in country_name_to_id.items():
                if c_name_key in p_admin.lower() or p_admin.lower() in c_name_key:
                    assigned_countries.add(c_id_val)
                    break

    # Países huérfanos: están en countries_dict pero carecen de subdivisiones en Admin 1
    missing_countries = [c_id for c_id in countries_dict if c_id not in assigned_countries]
    print(f"[Cobertura] Países totales en Admin 0: {len(countries_dict)}")
    print(f"[Cobertura] Países con provincias en Admin 1: {len(assigned_countries)}")
    print(f"[Cobertura] Países que requieren provincia nacional de respaldo: {len(missing_countries)}")

    if missing_countries:
        fallback_rows = []
        for c_id in missing_countries:
            c_info = countries_dict[c_id]
            geom = country_id_to_geom.get(c_id)
            if geom is not None and not geom.is_empty:
                fallback_rows.append({
                    'name': f"{c_info['name']}",
                    'name_en': f"{c_info['name']}",
                    'admin': c_info['name'],
                    'adm0_name': c_info['name'],
                    'adm0_a3': c_id,
                    'iso_a2': c_info.get('iso_a2', ''),
                    'type': 'Territorio Nacional',
                    'type_en': 'National Territory',
                    'geometry': geom
                })
        if fallback_rows:
            fallback_gdf = gpd.GeoDataFrame(fallback_rows, crs=gdf_provinces.crs)
            gdf_provinces = pd.concat([gdf_provinces, fallback_gdf], ignore_index=True)
            print(f"[Cobertura] Incorporadas {len(fallback_rows)} provincias nacionales para alcanzar el 100% de cobertura mundial.")

    provinces_list: List[Dict[str, Any]] = []
    gdf_provinces = gdf_provinces.reset_index(drop=True)
    prov_political_colors = []
    prov_id_colors = []

    # Índices espaciales de capas complementarias para enriquecimiento en O(log N)
    regions_sindex = gdf_regions.sindex if gdf_regions is not None else None
    places_sindex = gdf_places.sindex if gdf_places is not None else None
    lakes_sindex = gdf_lakes.sindex if gdf_lakes is not None else None
    rivers_sindex = gdf_rivers.sindex if gdf_rivers is not None else None

    for idx, row in gdf_provinces.iterrows():
        prov_id = idx + 1
        prov_name = str(row.get('name', row.get('name_en', f'Provincia {prov_id}'))).strip()
        if not prov_name or prov_name == 'None':
            prov_name = f"Provincia {prov_id}"

        admin_name = str(row.get('admin', row.get('adm0_name', ''))).strip()
        raw_iso = row.get('adm0_a3', row.get('iso_a2', ''))
        country_iso = normalize_iso(raw_iso, admin_name)

        if country_iso in countries_dict:
            pass
        elif admin_name.lower() in country_name_to_id:
            country_iso = country_name_to_id[admin_name.lower()]
        else:
            matched_iso = None
            for c_id, c_data in countries_dict.items():
                if c_data["name"].lower() in admin_name.lower() or admin_name.lower() in c_data["name"].lower():
                    matched_iso = c_id
                    break
            if matched_iso:
                country_iso = matched_iso
            else:
                if country_iso not in countries_dict:
                    color_fallback = HISTORICAL_COUNTRY_COLORS.get(country_iso, COUNTRY_PALETTE[abs(hash(country_iso)) % len(COUNTRY_PALETTE)])
                    countries_dict[country_iso] = {
                        "id": country_iso,
                        "name": admin_name if admin_name else f"País {country_iso}",
                        "iso_a2": "",
                        "iso_a3": country_iso,
                        "continent": "Desconocido",
                        "subregion": "Desconocido",
                        "color_hex": color_fallback,
                        "provinces": [],
                        "major_ports": [],
                        "capital": None
                    }
                    country_color_map[country_iso] = color_fallback

        color_p = countries_dict[country_iso]["color_hex"]
        prov_political_colors.append(color_p)

        r, g, b = id_to_rgb(prov_id)
        id_hex = f"#{r:02x}{g:02x}{b:02x}"
        prov_id_colors.append(id_hex)

        geom = row.geometry
        centroid = geom.centroid
        lat, lon = float(centroid.y), float(centroid.x)
        pixel_x, pixel_y = lat_lon_to_pixel(lat, lon, width, height, min_lat, max_lat)

        # Detectar si es costera tocando las zonas marítimas
        sea_cand = list(sea_sindex.intersection(geom.bounds))
        adjacent_seas: List[int] = []
        for s in sea_cand:
            s_idx = int(s)
            if geom.touches(gdf_seas.geometry.iloc[s_idx]) or geom.intersects(gdf_seas.geometry.iloc[s_idx]):
                adjacent_seas.append(int(10001 + s_idx))
        is_coastal = len(adjacent_seas) > 0

        # Enriquecimiento físico mediante intersección con regiones geográficas reales
        physical_terrain = None
        if regions_sindex is not None:
            r_cand = list(regions_sindex.intersection(geom.bounds))
            for rc in r_cand:
                rc_geom = gdf_regions.geometry.iloc[rc]
                if geom.intersects(rc_geom):
                    rc_row = gdf_regions.iloc[rc]
                    r_type = str(rc_row.get('featurecla', rc_row.get('type', ''))).lower()
                    r_name = str(rc_row.get('name', '')).lower()
                    if any(w in r_type or w in r_name for w in ['desert', 'erg', 'dune', 'sahara', 'gobi', 'atacama', 'kalahari']):
                        physical_terrain = 'desert'
                        break
                    elif any(w in r_type or w in r_name for w in ['mountain', 'range', 'cordillera', 'sierra', 'alps', 'himalaya', 'andes']):
                        physical_terrain = 'mountains'
                        break
                    elif any(w in r_type or w in r_name for w in ['tundra', 'ice', 'glacier']):
                        physical_terrain = 'tundra'
                        break
                    elif any(w in r_type or w in r_name for w in ['forest', 'jungle', 'rainforest', 'amazon', 'congo']):
                        physical_terrain = 'jungle'
                        break

        # Enriquecimiento demográfico y urbano con ciudades reales de Natural Earth
        prov_cities = []
        measured_pop = 0
        if places_sindex is not None:
            p_cand = list(places_sindex.intersection(geom.bounds))
            for pc in p_cand:
                p_geom = gdf_places.geometry.iloc[pc]
                if geom.contains(p_geom) or geom.intersects(p_geom):
                    p_row = gdf_places.iloc[pc]
                    c_name = str(p_row.get('NAME', p_row.get('name', ''))).strip()
                    c_pop = int(p_row.get('POP_MAX', p_row.get('pop_max', 0))) if pd.notnull(p_row.get('POP_MAX', p_row.get('pop_max', 0))) else 0
                    c_cap = int(p_row.get('FEATURECLA', '') == 'Admin-0 capital') or int(p_row.get('adm0cap', 0) == 1)
                    if c_name:
                        prov_cities.append({
                            "name": c_name,
                            "population": c_pop,
                            "is_capital": bool(c_cap)
                        })
                        measured_pop += c_pop

        # Detectar presencia de lagos interiores o ríos mayores
        has_major_lake = False
        if lakes_sindex is not None:
            lk_cand = list(lakes_sindex.intersection(geom.bounds))
            for lk in lk_cand:
                if geom.touches(gdf_lakes.geometry.iloc[lk]) or geom.intersects(gdf_lakes.geometry.iloc[lk]):
                    has_major_lake = True
                    break

        has_major_river = False
        if rivers_sindex is not None:
            rv_cand = list(rivers_sindex.intersection(geom.bounds))
            for rv in rv_cand:
                if geom.intersects(gdf_rivers.geometry.iloc[rv]):
                    has_major_river = True
                    break

        # Atributos económicos, demográficos y de terreno
        attributes = estimate_province_attributes(
            prov_name, country_iso, lat, lon, is_coastal,
            physical_terrain=physical_terrain,
            measured_population=measured_pop if measured_pop > 0 else None
        )

        # Verificar si es capital nacional
        is_capital = False
        if country_iso in MAJOR_CAPITALS:
            cap_info = MAJOR_CAPITALS[country_iso]
            dist_sq = (lat - cap_info["lat"])**2 + (lon - cap_info["lon"])**2
            if dist_sq < 1.5:
                is_capital = True

        prov_data = {
            "id": prov_id,
            "name": prov_name,
            "country_id": country_iso,
            "country_name": admin_name if admin_name else country_iso,
            "type": str(row.get('type_en', row.get('type', 'Province'))).strip(),
            "color_rgb": {"r": r, "g": g, "b": b, "hex": id_hex},
            "center": {
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "pixel_x": pixel_x,
                "pixel_y": pixel_y
            },
            "bounds": [round(c, 4) for c in geom.bounds],
            "is_coastal": is_coastal,
            "adjacent_seas": adjacent_seas,
            "terrain": attributes["terrain"],
            "population": attributes["population"],
            "manpower": attributes["manpower"],
            "resource": attributes["resource"],
            "resource_amount": attributes["resource_amount"],
            "industrial_level": attributes["industrial_level"],
            "is_capital": is_capital,
            "has_major_lake": has_major_lake,
            "has_major_river": has_major_river,
            "cities_count": len(prov_cities),
            "cities": prov_cities[:5],
            "neighbors": []
        }

        provinces_list.append(prov_data)
        if country_iso in countries_dict:
            countries_dict[country_iso]["provinces"].append(prov_id)

    # Actualizar adyacencia mar-provincia
    for prov in provinces_list:
        for s_id in prov["adjacent_seas"]:
            idx_s = s_id - 10001
            if 0 <= idx_s < len(sea_zones_list):
                sea_zones_list[idx_s]["adjacent_provinces"].append(prov["id"])

    # 10. Fronteras terrestres entre provincias
    print("[Fronteras] Calculando adyacencias topológicas entre provincias terrestres...")
    prov_sindex = gdf_provinces.sindex
    for i, row in gdf_provinces.iterrows():
        geom = row.geometry
        cand_idx = list(prov_sindex.intersection(geom.bounds))
        neighbors: List[int] = []
        for cand in cand_idx:
            c_idx = int(cand)
            if c_idx != int(i) and geom.touches(gdf_provinces.geometry.iloc[c_idx]):
                neighbors.append(int(c_idx + 1))
        provinces_list[i]["neighbors"] = sorted(neighbors)

    # 11. Calcular píxeles de Puertos Principales y Estrechos Estratégicos
    print("[Estrategia] Mapeando estrechos navales, canales y puertos principales...")
    ports_mapped = []
    for port in MAJOR_PORTS:
        px, py = lat_lon_to_pixel(port["lat"], port["lon"], width, height, min_lat, max_lat)
        ports_mapped.append({
            **port,
            "pixel_x": px,
            "pixel_y": py
        })
        c_id = port.get("country")
        if c_id in countries_dict:
            countries_dict[c_id]["major_ports"].append(port["name"])

    # Incorporar puertos adicionales del dataset oficial de Natural Earth si está presente
    if gdf_ports is not None and not gdf_ports.empty:
        existing_port_names = {p["name"].lower() for p in ports_mapped}
        for _, port_row in gdf_ports.iterrows():
            pt_name = str(port_row.get('name', port_row.get('NAME', ''))).strip()
            if pt_name and pt_name.lower() not in existing_port_names:
                pt_geom = port_row.geometry
                if pt_geom and pt_geom.geom_type == 'Point':
                    pt_lat, pt_lon = float(pt_geom.y), float(pt_geom.x)
                    if min_lat <= pt_lat <= max_lat:
                        px, py = lat_lon_to_pixel(pt_lat, pt_lon, width, height, min_lat, max_lat)
                        pt_country = str(port_row.get('adm0name', port_row.get('country', ''))).strip()
                        c_iso = normalize_iso('', pt_country)
                        ports_mapped.append({
                            "name": pt_name,
                            "lat": round(pt_lat, 4),
                            "lon": round(pt_lon, 4),
                            "country": c_iso if c_iso in countries_dict else "",
                            "sea": str(port_row.get('featurecla', 'Coastal Port')),
                            "pixel_x": px,
                            "pixel_y": py
                        })
                        existing_port_names.add(pt_name.lower())

    straits_mapped = []
    for strait in STRATEGIC_STRAITS:
        px, py = lat_lon_to_pixel(strait["lat"], strait["lon"], width, height, min_lat, max_lat)
        straits_mapped.append({
            **strait,
            "pixel_x": px,
            "pixel_y": py
        })

    # Estructurar datos de Lagos Mundiales
    lakes_data_list = []
    if gdf_lakes is not None and not gdf_lakes.empty:
        for lk_i, lk_row in gdf_lakes.iterrows():
            lk_name = str(lk_row.get('name', lk_row.get('NAME', f"Lago {lk_i+1}"))).strip()
            lk_geom = lk_row.geometry
            if lk_geom and not lk_geom.is_empty:
                lk_cent = lk_geom.centroid
                lakes_data_list.append({
                    "id": lk_i + 1,
                    "name": lk_name,
                    "lat": round(float(lk_cent.y), 4),
                    "lon": round(float(lk_cent.x), 4),
                    "featurecla": str(lk_row.get('featurecla', 'Lake'))
                })

    # Estructurar datos de Ríos Principales
    rivers_data_list = []
    if gdf_rivers is not None and not gdf_rivers.empty:
        for rv_i, rv_row in gdf_rivers.iterrows():
            rv_name = str(rv_row.get('name', rv_row.get('NAME', f"Río {rv_i+1}"))).strip()
            rivers_data_list.append({
                "id": rv_i + 1,
                "name": rv_name,
                "featurecla": str(rv_row.get('featurecla', 'River'))
            })

    # Estructurar datos de Asentamientos Urbanos y Ciudades
    places_data_list = []
    if gdf_places is not None and not gdf_places.empty:
        for pl_i, pl_row in gdf_places.iterrows():
            pl_name = str(pl_row.get('NAME', pl_row.get('name', ''))).strip()
            pl_geom = pl_row.geometry
            if pl_name and pl_geom and pl_geom.geom_type == 'Point':
                pl_lat, pl_lon = float(pl_geom.y), float(pl_geom.x)
                if min_lat <= pl_lat <= max_lat:
                    px, py = lat_lon_to_pixel(pl_lat, pl_lon, width, height, min_lat, max_lat)
                    places_data_list.append({
                        "id": pl_i + 1,
                        "name": pl_name,
                        "lat": round(pl_lat, 4),
                        "lon": round(pl_lon, 4),
                        "pixel_x": px,
                        "pixel_y": py,
                        "population": int(pl_row.get('POP_MAX', 0)) if pd.notnull(pl_row.get('POP_MAX', 0)) else 0,
                        "is_capital": int(pl_row.get('FEATURECLA', '') == 'Admin-0 capital') or int(pl_row.get('adm0cap', 0) == 1)
                    })

    # Estructurar datos de Bases Aéreas y Aeropuertos
    airports_data_list = []
    if gdf_airports is not None and not gdf_airports.empty:
        for ap_i, ap_row in gdf_airports.iterrows():
            ap_name = str(ap_row.get('name', ap_row.get('NAME', f"Aeropuerto {ap_i+1}"))).strip()
            ap_geom = ap_row.geometry
            if ap_name and ap_geom and ap_geom.geom_type == 'Point':
                ap_lat, ap_lon = float(ap_geom.y), float(ap_geom.x)
                if min_lat <= ap_lat <= max_lat:
                    px, py = lat_lon_to_pixel(ap_lat, ap_lon, width, height, min_lat, max_lat)
                    airports_data_list.append({
                        "id": ap_i + 1,
                        "name": ap_name,
                        "iata_code": str(ap_row.get('iata_code', ap_row.get('gps_code', ''))),
                        "type": str(ap_row.get('type', 'military_civilian')),
                        "lat": round(ap_lat, 4),
                        "lon": round(ap_lon, 4),
                        "pixel_x": px,
                        "pixel_y": py
                    })

    # Estructurar datos de Ferrocarriles (Rutas de Suministro)
    railroads_data_list = []
    if gdf_railroads is not None and not gdf_railroads.empty:
        for rr_i, rr_row in gdf_railroads.iterrows():
            railroads_data_list.append({
                "id": rr_i + 1,
                "featurecla": str(rr_row.get('featurecla', 'Railroad')),
                "gauge": str(rr_row.get('gauge', 'standard'))
            })

    # Estructurar datos de Glaciares y Campos de Hielo
    glaciers_data_list = []
    if gdf_glaciers is not None and not gdf_glaciers.empty:
        for gl_i, gl_row in gdf_glaciers.iterrows():
            gl_geom = gl_row.geometry
            if gl_geom and not gl_geom.is_empty:
                gl_cent = gl_geom.centroid
                glaciers_data_list.append({
                    "id": gl_i + 1,
                    "name": str(gl_row.get('name', f"Glaciar {gl_i+1}")),
                    "lat": round(float(gl_cent.y), 4),
                    "lon": round(float(gl_cent.x), 4)
                })

    # 12. Guardar capas vectoriales GeoJSON
    print("[Exportación] Guardando capas vectoriales GeoJSON editables...")
    gdf_provinces.to_file(output_dir / "world_provinces.geojson", driver="GeoJSON")
    gdf_countries.to_file(output_dir / "world_countries.geojson", driver="GeoJSON")
    gdf_seas.to_file(output_dir / "world_sea_zones.geojson", driver="GeoJSON")

    # 13. Guardar JSON Estructurado Maestro
    print("[Exportación] Guardando dataset maestro en world_map_data.json...")
    full_dataset = {
        "metadata": {
            "version": "2.2",
            "projection": "Equirectangular Cortada (Optimizado Móvil)",
            "bounds": {
                "min_lon": -180.0,
                "max_lon": 180.0,
                "min_lat": float(min_lat),
                "max_lat": float(max_lat)
            },
            "dimensions": {"width": int(width), "height": int(height)},
            "scale": str(scale),
            "total_countries": len(countries_dict),
            "total_land_provinces": len(provinces_list),
            "total_sea_zones": len(sea_zones_list),
            "total_strategic_straits": len(straits_mapped),
            "total_major_ports": len(ports_mapped),
            "total_airports": len(airports_data_list),
            "total_railroads": len(railroads_data_list),
            "total_glaciers": len(glaciers_data_list),
            "total_lakes": len(lakes_data_list),
            "total_rivers": len(rivers_data_list),
            "total_populated_places": len(places_data_list),
            "ocean_color_id_base": 10001
        },
        "countries": countries_dict,
        "provinces": provinces_list,
        "sea_zones": sea_zones_list,
        "strategic_straits": straits_mapped,
        "major_ports": ports_mapped,
        "airports": airports_data_list[:500],
        "lakes": lakes_data_list[:200],
        "rivers": rivers_data_list[:200],
        "populated_places": places_data_list[:500]
    }
    # Sanitizar explícitamente cualquier tipo NumPy para garantizar 100% serialización JSON nativa
    full_dataset = sanitize_for_json(full_dataset)

    with open(output_dir / "world_map_data.json", 'w', encoding='utf-8') as f:
        json.dump(full_dataset, f, ensure_ascii=False, indent=2, cls=NpEncoder)
    print(f" -> Guardado: world_map_data.json ({(output_dir / 'world_map_data.json').stat().st_size / 1024 / 1024:.2f} MB)")

    # 14. Generar Bases de Datos SQLite Modulares y Especializadas
    # Archivo A: world_overview.db (Ligero, información general para IA, diplomacia y selección de país)
    # Archivo B: world_provinces.db (Detallado, microdatos para el motor de juego en Android)
    # Archivo C: world_map.db (Unificado completo con ambas capas integradas)
    print("[Exportación] Generando bases de datos relacionales SQLite particionadas...")

    # Precalcular estadísticas agregadas de países
    country_stats = {}
    for p in provinces_list:
        c_id = p["country_id"]
        if c_id not in country_stats:
            country_stats[c_id] = {
                "total_provinces": 0,
                "total_population": 0,
                "total_manpower": 0,
                "total_factories": 0,
                "total_ports": 0,
                "coastal_access": False
            }
        country_stats[c_id]["total_provinces"] += 1
        country_stats[c_id]["total_population"] += p["population"]
        country_stats[c_id]["total_manpower"] += p["manpower"]
        country_stats[c_id]["total_factories"] += p["industrial_level"]
        if p["is_coastal"]:
            country_stats[c_id]["coastal_access"] = True

    for pt in ports_mapped:
        c_id = pt.get("country")
        if c_id in country_stats:
            country_stats[c_id]["total_ports"] += 1

    # Precalcular fronteras internacionales a nivel de país
    country_borders_set = set()
    for p in provinces_list:
        c_orig = p["country_id"]
        for n_id in p["neighbors"]:
            if 1 <= n_id <= len(provinces_list):
                c_dest = provinces_list[n_id - 1]["country_id"]
                if c_orig != c_dest:
                    pair = tuple(sorted([c_orig, c_dest]))
                    country_borders_set.add(pair)

    # --- A) GENERAR world_overview.db (Base de Datos General) ---
    overview_db_path = output_dir / "world_overview.db"
    if overview_db_path.exists():
        overview_db_path.unlink()

    conn_ov = sqlite3.connect(overview_db_path)
    cur_ov = conn_ov.cursor()
    cur_ov.execute("PRAGMA foreign_keys = ON;")
    cur_ov.execute("PRAGMA synchronous = OFF;")
    cur_ov.execute("PRAGMA journal_mode = MEMORY;")

    cur_ov.execute("""
    CREATE TABLE metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    for k, v in full_dataset["metadata"].items():
        val_str = json.dumps(v, ensure_ascii=False, cls=NpEncoder) if isinstance(v, (dict, list)) else str(v)
        cur_ov.execute("INSERT INTO metadata (key, value) VALUES (?, ?);", (k, val_str))

    cur_ov.execute("""
    CREATE TABLE countries_overview (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        iso_a2 TEXT,
        iso_a3 TEXT,
        continent TEXT,
        subregion TEXT,
        color_hex TEXT,
        capital_name TEXT,
        capital_lat REAL,
        capital_lon REAL,
        total_provinces INTEGER,
        total_population INTEGER,
        total_manpower INTEGER,
        total_factories INTEGER,
        total_ports INTEGER,
        has_coast INTEGER
    );
    """)

    for c_id, c_data in countries_dict.items():
        stats = country_stats.get(c_id, {
            "total_provinces": len(c_data.get("provinces", [])),
            "total_population": 0,
            "total_manpower": 0,
            "total_factories": 0,
            "total_ports": len(c_data.get("major_ports", [])),
            "coastal_access": False
        })
        cap = c_data.get("capital")
        cur_ov.execute("""
        INSERT INTO countries_overview (
            id, name, iso_a2, iso_a3, continent, subregion, color_hex,
            capital_name, capital_lat, capital_lon, total_provinces,
            total_population, total_manpower, total_factories, total_ports, has_coast
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            str(c_id),
            str(c_data["name"]),
            str(c_data["iso_a2"]),
            str(c_data["iso_a3"]),
            str(c_data["continent"]),
            str(c_data["subregion"]),
            str(c_data["color_hex"]),
            cap["name"] if cap else None,
            cap["lat"] if cap else None,
            cap["lon"] if cap else None,
            stats["total_provinces"],
            stats["total_population"],
            stats["total_manpower"],
            stats["total_factories"],
            stats["total_ports"],
            1 if stats["coastal_access"] else 0
        ))

    cur_ov.execute("""
    CREATE TABLE country_borders (
        country_a TEXT NOT NULL,
        country_b TEXT NOT NULL,
        PRIMARY KEY (country_a, country_b),
        FOREIGN KEY (country_a) REFERENCES countries_overview(id),
        FOREIGN KEY (country_b) REFERENCES countries_overview(id)
    );
    """)
    for (ca, cb) in sorted(country_borders_set):
        if ca in countries_dict and cb in countries_dict:
            cur_ov.execute("INSERT OR IGNORE INTO country_borders (country_a, country_b) VALUES (?, ?);", (ca, cb))

    cur_ov.execute("""
    CREATE TABLE strategic_straits (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER,
        type TEXT,
        connects TEXT
    );
    """)
    for st in straits_mapped:
        cur_ov.execute("""
        INSERT INTO strategic_straits (id, name, lat, lon, pixel_x, pixel_y, type, connects)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            st["id"], st["name"], st["lat"], st["lon"],
            st["pixel_x"], st["pixel_y"], st["type"],
            json.dumps(st.get("connects", []), ensure_ascii=False)
        ))

    cur_ov.execute("CREATE INDEX idx_ov_continent ON countries_overview(continent);")
    cur_ov.execute("CREATE INDEX idx_ov_borders_a ON country_borders(country_a);")
    cur_ov.execute("CREATE INDEX idx_ov_borders_b ON country_borders(country_b);")
    conn_ov.commit()
    conn_ov.close()
    print(f" -> Guardado: world_overview.db ({overview_db_path.stat().st_size / 1024:.1f} KB)")

    # --- B) GENERAR world_provinces.db (Detallada: Provincias, Topología y Mares) ---
    provinces_db_path = output_dir / "world_provinces.db"
    if provinces_db_path.exists():
        provinces_db_path.unlink()

    conn_pr = sqlite3.connect(provinces_db_path)
    cur_pr = conn_pr.cursor()
    cur_pr.execute("PRAGMA synchronous = OFF;")
    cur_pr.execute("PRAGMA journal_mode = MEMORY;")

    cur_pr.execute("""
    CREATE TABLE provinces (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        country_id TEXT NOT NULL,
        color_hex TEXT,
        rgb_r INTEGER,
        rgb_g INTEGER,
        rgb_b INTEGER,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER,
        is_coastal INTEGER,
        terrain TEXT,
        population INTEGER,
        manpower INTEGER,
        resource TEXT,
        resource_amount INTEGER,
        industrial_level INTEGER,
        is_capital INTEGER,
        adjacent_seas TEXT,
        neighbors TEXT
    );
    """)
    for p in provinces_list:
        cur_pr.execute("""
        INSERT INTO provinces (
            id, name, country_id, color_hex, rgb_r, rgb_g, rgb_b,
            lat, lon, pixel_x, pixel_y, is_coastal, terrain,
            population, manpower, resource, resource_amount,
            industrial_level, is_capital, adjacent_seas, neighbors
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            int(p["id"]),
            str(p["name"]),
            str(p["country_id"]),
            str(p["color_rgb"]["hex"] if isinstance(p["color_rgb"], dict) else p.get("color_hex", "")),
            int(p["color_rgb"]["r"] if isinstance(p["color_rgb"], dict) else p["color_rgb"][0]),
            int(p["color_rgb"]["g"] if isinstance(p["color_rgb"], dict) else p["color_rgb"][1]),
            int(p["color_rgb"]["b"] if isinstance(p["color_rgb"], dict) else p["color_rgb"][2]),
            float(p["center"]["lat"]),
            float(p["center"]["lon"]),
            int(p["center"]["pixel_x"]),
            int(p["center"]["pixel_y"]),
            1 if p["is_coastal"] else 0,
            str(p["terrain"]),
            int(p["population"]),
            int(p["manpower"]),
            str(p["resource"]),
            int(p["resource_amount"]),
            int(p["industrial_level"]),
            1 if p["is_capital"] else 0,
            json.dumps(p["adjacent_seas"], cls=NpEncoder),
            json.dumps(p["neighbors"], cls=NpEncoder)
        ))

    # Tabla de adyacencias relacionales normalizada para búsqueda de caminos (Pathfinding A* en Rust)
    cur_pr.execute("""
    CREATE TABLE province_neighbors (
        province_id INTEGER NOT NULL,
        neighbor_id INTEGER NOT NULL,
        PRIMARY KEY (province_id, neighbor_id),
        FOREIGN KEY (province_id) REFERENCES provinces(id),
        FOREIGN KEY (neighbor_id) REFERENCES provinces(id)
    );
    """)
    for p in provinces_list:
        p_id = p["id"]
        for n_id in p["neighbors"]:
            cur_pr.execute("INSERT OR IGNORE INTO province_neighbors (province_id, neighbor_id) VALUES (?, ?);", (p_id, n_id))

    cur_pr.execute("""
    CREATE TABLE sea_zones (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        featurecla TEXT,
        rgb_r INTEGER,
        rgb_g INTEGER,
        rgb_b INTEGER,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER,
        adjacent_seas TEXT,
        adjacent_provinces TEXT
    );
    """)
    for s in sea_zones_list:
        cur_pr.execute("""
        INSERT INTO sea_zones (
            id, name, featurecla, rgb_r, rgb_g, rgb_b,
            lat, lon, pixel_x, pixel_y, adjacent_seas, adjacent_provinces
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            int(s["id"]),
            str(s["name"]),
            str(s["type"]),
            int(s["color_rgb"]["r"] if isinstance(s["color_rgb"], dict) else s["color_rgb"][0]),
            int(s["color_rgb"]["g"] if isinstance(s["color_rgb"], dict) else s["color_rgb"][1]),
            int(s["color_rgb"]["b"] if isinstance(s["color_rgb"], dict) else s["color_rgb"][2]),
            float(s["center"]["lat"]),
            float(s["center"]["lon"]),
            int(s["center"]["pixel_x"]),
            int(s["center"]["pixel_y"]),
            json.dumps(s["adjacent_seas"], cls=NpEncoder),
            json.dumps(s["adjacent_provinces"], cls=NpEncoder)
        ))

    cur_pr.execute("""
    CREATE TABLE major_ports (
        name TEXT PRIMARY KEY,
        country_id TEXT,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER,
        sea TEXT
    );
    """)
    for mp in ports_mapped:
        cur_pr.execute("""
        INSERT INTO major_ports (name, country_id, lat, lon, pixel_x, pixel_y, sea)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            mp["name"], mp["country"], mp["lat"], mp["lon"],
            mp["pixel_x"], mp["pixel_y"], mp.get("sea", "")
        ))

    cur_pr.execute("CREATE INDEX idx_provinces_country ON provinces(country_id);")
    cur_pr.execute("CREATE INDEX idx_provinces_terrain ON provinces(terrain);")
    cur_pr.execute("CREATE INDEX idx_provinces_coastal ON provinces(is_coastal);")
    cur_pr.execute("CREATE INDEX idx_neighbors_source ON province_neighbors(province_id);")
    cur_pr.execute("CREATE INDEX idx_neighbors_target ON province_neighbors(neighbor_id);")
    conn_pr.commit()
    conn_pr.close()
    print(f" -> Guardado: world_provinces.db ({provinces_db_path.stat().st_size / 1024 / 1024:.2f} MB)")

    # --- C) GENERAR world_map.db (Maestro Unificado para Android) ---
    db_path = output_dir / "world_map.db"
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute("PRAGMA synchronous = OFF;")
    cur.execute("PRAGMA journal_mode = MEMORY;")

    cur.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT);")
    for k, v in full_dataset["metadata"].items():
        val_str = json.dumps(v, ensure_ascii=False, cls=NpEncoder) if isinstance(v, (dict, list)) else str(v)
        cur.execute("INSERT INTO metadata (key, value) VALUES (?, ?);", (k, val_str))

    cur.execute("""
    CREATE TABLE countries (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        iso_a2 TEXT,
        iso_a3 TEXT,
        continent TEXT,
        subregion TEXT,
        color_hex TEXT,
        capital TEXT,
        major_ports TEXT
    );
    """)
    for c_id, c_data in countries_dict.items():
        cur.execute("""
        INSERT INTO countries (id, name, iso_a2, iso_a3, continent, subregion, color_hex, capital, major_ports)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            str(c_id),
            str(c_data["name"]),
            str(c_data["iso_a2"]),
            str(c_data["iso_a3"]),
            str(c_data["continent"]),
            str(c_data["subregion"]),
            str(c_data["color_hex"]),
            str(c_data.get("capital")) if c_data.get("capital") else None,
            json.dumps(c_data.get("major_ports", []), ensure_ascii=False, cls=NpEncoder)
        ))

    cur.execute("""
    CREATE TABLE provinces (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        country_id TEXT NOT NULL,
        color_hex TEXT,
        rgb_r INTEGER,
        rgb_g INTEGER,
        rgb_b INTEGER,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER,
        is_coastal INTEGER,
        adjacent_seas TEXT,
        terrain TEXT,
        population INTEGER,
        manpower INTEGER,
        resource TEXT,
        resource_amount INTEGER,
        industrial_level INTEGER,
        is_capital INTEGER,
        neighbors TEXT,
        FOREIGN KEY(country_id) REFERENCES countries(id)
    );
    """)
    for p in provinces_list:
        cur.execute("""
        INSERT INTO provinces (
            id, name, country_id, color_hex, rgb_r, rgb_g, rgb_b,
            lat, lon, pixel_x, pixel_y, is_coastal, adjacent_seas,
            terrain, population, manpower, resource, resource_amount,
            industrial_level, is_capital, neighbors
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            int(p["id"]),
            str(p["name"]),
            str(p["country_id"]),
            str(p["color_rgb"]["hex"] if isinstance(p["color_rgb"], dict) else p.get("color_hex", "")),
            int(p["color_rgb"]["r"] if isinstance(p["color_rgb"], dict) else p["color_rgb"][0]),
            int(p["color_rgb"]["g"] if isinstance(p["color_rgb"], dict) else p["color_rgb"][1]),
            int(p["color_rgb"]["b"] if isinstance(p["color_rgb"], dict) else p["color_rgb"][2]),
            float(p["center"]["lat"]),
            float(p["center"]["lon"]),
            int(p["center"]["pixel_x"]),
            int(p["center"]["pixel_y"]),
            1 if p["is_coastal"] else 0,
            json.dumps(p["adjacent_seas"], cls=NpEncoder),
            str(p["terrain"]),
            int(p["population"]),
            int(p["manpower"]),
            str(p["resource"]),
            int(p["resource_amount"]),
            int(p["industrial_level"]),
            1 if p["is_capital"] else 0,
            json.dumps(p["neighbors"], cls=NpEncoder)
        ))

    cur.execute("""
    CREATE TABLE province_neighbors (
        province_id INTEGER NOT NULL,
        neighbor_id INTEGER NOT NULL,
        PRIMARY KEY (province_id, neighbor_id),
        FOREIGN KEY (province_id) REFERENCES provinces(id),
        FOREIGN KEY (neighbor_id) REFERENCES provinces(id)
    );
    """)
    for p in provinces_list:
        p_id = p["id"]
        for n_id in p["neighbors"]:
            cur.execute("INSERT OR IGNORE INTO province_neighbors (province_id, neighbor_id) VALUES (?, ?);", (p_id, n_id))

    cur.execute("""
    CREATE TABLE country_borders (
        country_a TEXT NOT NULL,
        country_b TEXT NOT NULL,
        PRIMARY KEY (country_a, country_b),
        FOREIGN KEY (country_a) REFERENCES countries(id),
        FOREIGN KEY (country_b) REFERENCES countries(id)
    );
    """)
    for (ca, cb) in sorted(country_borders_set):
        if ca in countries_dict and cb in countries_dict:
            cur.execute("INSERT OR IGNORE INTO country_borders (country_a, country_b) VALUES (?, ?);", (ca, cb))

    cur.execute("""
    CREATE TABLE sea_zones (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        featurecla TEXT,
        rgb_r INTEGER,
        rgb_g INTEGER,
        rgb_b INTEGER,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER,
        adjacent_seas TEXT,
        adjacent_provinces TEXT
    );
    """)
    for s in sea_zones_list:
        cur.execute("""
        INSERT INTO sea_zones (
            id, name, featurecla, rgb_r, rgb_g, rgb_b,
            lat, lon, pixel_x, pixel_y, adjacent_seas, adjacent_provinces
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            int(s["id"]),
            str(s["name"]),
            str(s["type"]),
            int(s["color_rgb"]["r"] if isinstance(s["color_rgb"], dict) else s["color_rgb"][0]),
            int(s["color_rgb"]["g"] if isinstance(s["color_rgb"], dict) else s["color_rgb"][1]),
            int(s["color_rgb"]["b"] if isinstance(s["color_rgb"], dict) else s["color_rgb"][2]),
            float(s["center"]["lat"]),
            float(s["center"]["lon"]),
            int(s["center"]["pixel_x"]),
            int(s["center"]["pixel_y"]),
            json.dumps(s["adjacent_seas"], cls=NpEncoder),
            json.dumps(s["adjacent_provinces"], cls=NpEncoder)
        ))

    cur.execute("""
    CREATE TABLE strategic_straits (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER,
        type TEXT,
        connects TEXT
    );
    """)
    for st in straits_mapped:
        cur.execute("""
        INSERT INTO strategic_straits (id, name, lat, lon, pixel_x, pixel_y, type, connects)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            st["id"], st["name"], st["lat"], st["lon"],
            st["pixel_x"], st["pixel_y"], st["type"],
            json.dumps(st.get("connects", []), ensure_ascii=False)
        ))

    cur.execute("""
    CREATE TABLE major_ports (
        name TEXT PRIMARY KEY,
        country_id TEXT,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER,
        sea TEXT
    );
    """)
    for mp in ports_mapped:
        cur.execute("""
        INSERT INTO major_ports (name, country_id, lat, lon, pixel_x, pixel_y, sea)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            mp["name"], mp["country"], mp["lat"], mp["lon"],
            mp["pixel_x"], mp["pixel_y"], mp.get("sea", "")
        ))

    # Tablas SQLite para datasets geográficos y urbanos adicionales
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lakes (
        id INTEGER PRIMARY KEY,
        name TEXT,
        featurecla TEXT,
        lat REAL,
        lon REAL
    );
    """)
    for lk in lakes_data_list:
        cur.execute("INSERT INTO lakes (id, name, featurecla, lat, lon) VALUES (?, ?, ?, ?, ?);",
                    (lk["id"], lk["name"], lk["featurecla"], lk["lat"], lk["lon"]))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rivers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        featurecla TEXT
    );
    """)
    for rv in rivers_data_list:
        cur.execute("INSERT INTO rivers (id, name, featurecla) VALUES (?, ?, ?);",
                    (rv["id"], rv["name"], rv["featurecla"]))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS populated_places (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER,
        population INTEGER,
        is_capital INTEGER
    );
    """)
    for pl in places_data_list:
        cur.execute("""
        INSERT INTO populated_places (id, name, lat, lon, pixel_x, pixel_y, population, is_capital)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (pl["id"], pl["name"], pl["lat"], pl["lon"], pl["pixel_x"], pl["pixel_y"], pl["population"], pl["is_capital"]))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS airports (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        iata_code TEXT,
        type TEXT,
        lat REAL,
        lon REAL,
        pixel_x INTEGER,
        pixel_y INTEGER
    );
    """)
    for ap in airports_data_list:
        cur.execute("""
        INSERT INTO airports (id, name, iata_code, type, lat, lon, pixel_x, pixel_y)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (ap["id"], ap["name"], ap["iata_code"], ap["type"], ap["lat"], ap["lon"], ap["pixel_x"], ap["pixel_y"]))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS railroads (
        id INTEGER PRIMARY KEY,
        featurecla TEXT,
        gauge TEXT
    );
    """)
    for rr in railroads_data_list:
        cur.execute("INSERT INTO railroads (id, featurecla, gauge) VALUES (?, ?, ?);",
                    (rr["id"], rr["featurecla"], rr["gauge"]))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS glaciers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        lat REAL,
        lon REAL
    );
    """)
    for gl in glaciers_data_list:
        cur.execute("INSERT INTO glaciers (id, name, lat, lon) VALUES (?, ?, ?, ?);",
                    (gl["id"], gl["name"], gl["lat"], gl["lon"]))

    cur.execute("CREATE INDEX idx_provinces_country ON provinces(country_id);")
    cur.execute("CREATE INDEX idx_provinces_terrain ON provinces(terrain);")
    cur.execute("CREATE INDEX idx_provinces_coastal ON provinces(is_coastal);")
    cur.execute("CREATE INDEX idx_sea_zones_name ON sea_zones(name);")
    cur.execute("CREATE INDEX idx_master_neighbors_p ON province_neighbors(province_id);")
    cur.execute("CREATE INDEX idx_master_country_borders ON country_borders(country_a);")
    cur.execute("CREATE INDEX idx_airports_type ON airports(type);")

    conn.commit()
    conn.close()
    print(f" -> Guardado: world_map.db ({db_path.stat().st_size / 1024 / 1024:.2f} MB)")

    # 15. Renderizado de Imágenes PNG
    dpi = 150
    figsize = (width / dpi, height / dpi)

    # A) Mapa Político Mundial con Estética Militar de Gran Estrategia (Hearts of Iron IV Style)
    print("[Renderizado 1/3] Generando world_provinces_political.png (Estilo Hearts of Iron IV)...")
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Fondo Oceánico Táctico Almirantazgo Naval
    hoi4_ocean_deep = '#0a192f'
    hoi4_ocean_mid = '#0f2642'
    hoi4_sea_grid = '#38bdf8'
    hoi4_glacier = '#f1f5f9'
    hoi4_coastline = '#0f172a'
    hoi4_railroads = '#334155'

    fig.patch.set_facecolor(hoi4_ocean_deep)
    ax.set_facecolor(hoi4_ocean_deep)

    # 0. Capa base oceánica total profunda
    ocean_extent = box(-180.0, min_lat, 180.0, max_lat)
    gpd.GeoSeries([ocean_extent], crs=gdf_seas.crs).plot(ax=ax, color=hoi4_ocean_deep, zorder=1)
    if gdf_ocean is not None and not gdf_ocean.empty:
        gdf_ocean.plot(ax=ax, color=hoi4_ocean_mid, edgecolor='none', zorder=1)

    # 1. Zonas Marítimas con cuadrícula e iluminación oceánica naval sobria
    gdf_seas.plot(ax=ax, color=sea_colors_political, edgecolor='#1e3a8a', linewidth=0.3, alpha=0.92, zorder=2)

    # 1.1 Cuadrícula náutica de almirantazgo (Graticules de coordenadas de guerra)
    if gdf_graticules is not None and not gdf_graticules.empty:
        gdf_graticules.plot(ax=ax, color='#38bdf8', linewidth=0.2, alpha=0.18, zorder=2.2)

    # 1.2 Líneas de navegación mayor (Ecuador, Trópicos y Círculos Polares)
    if gdf_geolines is not None and not gdf_geolines.empty:
        gdf_geolines.plot(ax=ax, color='#fbbf24', linewidth=0.4, linestyle='--', alpha=0.35, zorder=2.3)

    # 1.3 Arrecifes y bajíos peligrosos para navegación
    if gdf_reefs is not None and not gdf_reefs.empty:
        gdf_reefs.plot(ax=ax, color='#06b6d4', linewidth=0.25, alpha=0.45, zorder=2.4)

    # 2. Lagos mundiales en azul lacustre marino coordinado
    if gdf_lakes is not None and not gdf_lakes.empty:
        gdf_lakes.plot(ax=ax, color='#0d2238', edgecolor='#38bdf8', linewidth=0.3, zorder=2.5)

    # 3. Provincias terrestres con paleta política militar sobria
    gdf_provinces.plot(ax=ax, color=prov_political_colors, edgecolor='#1f2937', linewidth=0.22, alpha=0.98, zorder=3)

    # 3.1 Glaciares y nieves perpetuas (Himalaya, Groenlandia, Andes, Svalbard)
    if gdf_glaciers is not None and not gdf_glaciers.empty:
        gdf_glaciers.plot(ax=ax, color=hoi4_glacier, edgecolor='#93c5fd', linewidth=0.3, alpha=0.95, zorder=3.5)

    # 4. Red hidrográfica de ríos navegables
    if gdf_rivers is not None and not gdf_rivers.empty:
        gdf_rivers.plot(ax=ax, color='#38bdf8', linewidth=0.35, alpha=0.75, zorder=3.8)

    # 4.1 Línea de costa de alta precisión (Coastline 10m)
    if gdf_coastline is not None and not gdf_coastline.empty:
        gdf_coastline.plot(ax=ax, color=hoi4_coastline, linewidth=0.42, alpha=0.85, zorder=4)

    # 4.2 Red Ferroviaria Mundial / Eje de Suministros Militares
    if gdf_railroads is not None and not gdf_railroads.empty:
        gdf_railroads.plot(ax=ax, color=hoi4_railroads, linewidth=0.3, alpha=0.55, zorder=4.2)

    # 5. Fronteras soberanas de alto contraste (efecto halo internacional HoI4)
    gdf_countries.boundary.plot(ax=ax, edgecolor='#000000', linewidth=1.4, alpha=0.5, zorder=4.8)
    gdf_countries.boundary.plot(ax=ax, edgecolor='#ffffff', linewidth=0.85, alpha=0.98, zorder=5)

    # 5.1 Bases Aéreas Estratégicas (Aeropuertos 10m)
    for ap in airports_data_list[:250]:
        ax.plot(ap["lon"], ap["lat"], marker='^', color='#818cf8', markersize=2.4, markeredgecolor='#0f172a', markeredgewidth=0.3, zorder=5.5)

    # 6. Dibujar Canales y Estrechos Estratégicos (Rombos Dorados Militares)
    for st in straits_mapped:
        ax.plot(st["lon"], st["lat"], marker='D', color='#fbbf24', markersize=4.0, markeredgecolor='#000000', markeredgewidth=0.6, zorder=6.5)

    # 7. Dibujar Puertos Principales y Bases Navales (Círculos Cian)
    for pt in ports_mapped:
        ax.plot(pt["lon"], pt["lat"], marker='o', color='#38bdf8', markersize=3.0, markeredgecolor='#0f172a', markeredgewidth=0.5, zorder=6)

    ax.set_xlim(-180, 180)
    ax.set_ylim(min_lat, max_lat)
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.savefig(output_dir / "world_provinces_political.png", dpi=dpi, facecolor=hoi4_ocean_deep, bbox_inches='tight', pad_inches=0)
    plt.close()
    print(" -> Guardado: world_provinces_political.png")

    # B) Mapa Táctico en Blanco (Lienzo para Mods con Mar Náutico Distinguible y Lagos Rellenos)
    print("[Renderizado 2/3] Generando world_provinces_blank.png con mar náutico claro...")
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    tactical_ocean_bg = '#0a192f'      # Azul marino táctico profundo
    tactical_sea_zone = '#112a45'      # Zonas marítimas navegables
    tactical_sea_grid = '#38bdf8'      # Cuadrícula naval en cian suave
    tactical_land_fill = '#1e293b'     # Tierra táctica en pizarra militar
    tactical_prov_edge = '#334155'     # Bordes de provincia
    tactical_nation_edge = '#ffffff'   # Fronteras internacionales en blanco puro

    fig.patch.set_facecolor(tactical_ocean_bg)
    ax.set_facecolor(tactical_ocean_bg)

    # 0. Capa base oceánica total continua
    gpd.GeoSeries([ocean_extent], crs=gdf_seas.crs).plot(ax=ax, color=tactical_ocean_bg, zorder=1)
    if gdf_ocean is not None and not gdf_ocean.empty:
        gdf_ocean.plot(ax=ax, color='#0f2642', edgecolor='none', zorder=1)

    # 1. Zonas Marítimas navegables con cuadrícula náutica distinguible
    gdf_seas.plot(ax=ax, facecolor=tactical_sea_zone, edgecolor='#1e3a8a', linewidth=0.3, alpha=0.9, zorder=2)
    if gdf_graticules is not None and not gdf_graticules.empty:
        gdf_graticules.plot(ax=ax, color='#38bdf8', linewidth=0.2, alpha=0.18, zorder=2.2)

    # 2. Lagos interiores mundiales
    if gdf_lakes is not None and not gdf_lakes.empty:
        gdf_lakes.plot(ax=ax, facecolor=tactical_sea_zone, edgecolor=tactical_sea_grid, linewidth=0.3, zorder=2)

    # 3. Provincias terrestres en paleta monocromática táctica
    gdf_provinces.plot(ax=ax, facecolor=tactical_land_fill, edgecolor=tactical_prov_edge, linewidth=0.25, zorder=3)

    # 3.1 Glaciares
    if gdf_glaciers is not None and not gdf_glaciers.empty:
        gdf_glaciers.plot(ax=ax, color='#f8fafc', edgecolor='#cbd5e1', linewidth=0.25, zorder=3.4)

    # 4. Ríos principales y líneas de costa
    if gdf_rivers is not None and not gdf_rivers.empty:
        gdf_rivers.plot(ax=ax, color='#38bdf8', linewidth=0.35, alpha=0.75, zorder=3.8)
    if gdf_coastline is not None and not gdf_coastline.empty:
        gdf_coastline.plot(ax=ax, color='#0f172a', linewidth=0.4, alpha=0.85, zorder=4)

    # 5. Fronteras soberanas de alto contraste blanco nítido
    gdf_countries.boundary.plot(ax=ax, edgecolor='#000000', linewidth=1.4, alpha=0.5, zorder=4.8)
    gdf_countries.boundary.plot(ax=ax, edgecolor=tactical_nation_edge, linewidth=0.85, alpha=0.98, zorder=5)

    # 6. Puntos navales estratégicos
    for st in straits_mapped:
        ax.plot(st["lon"], st["lat"], marker='D', color='#fbbf24', markersize=3.6, markeredgecolor='#000000', markeredgewidth=0.5, zorder=6)

    ax.set_xlim(-180, 180)
    ax.set_ylim(min_lat, max_lat)
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.savefig(output_dir / "world_provinces_blank.png", dpi=dpi, facecolor=tactical_ocean_bg, bbox_inches='tight', pad_inches=0)
    plt.close()
    print(" -> Guardado: world_provinces_blank.png")

    # C) Mapa Indexado por Color (Pixel ID Map: Tierra + Zonas Marítimas)
    print("[Renderizado 3/3] Generando world_provinces_ids.png (Pixel ID Map: Provincias + Mares)...")
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor('#000000') # 0 = Mar abierto / Profundo sin asignar
    ax.set_facecolor('#000000')

    # Pintar zonas marítimas con su ID único
    gdf_seas.plot(ax=ax, color=sea_id_colors, edgecolor='none', linewidth=0)
    # Pintar provincias terrestres con su ID único por encima
    gdf_provinces.plot(ax=ax, color=prov_id_colors, edgecolor='none', linewidth=0)

    ax.set_xlim(-180, 180)
    ax.set_ylim(min_lat, max_lat)
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.savefig(output_dir / "world_provinces_ids.png", dpi=dpi, facecolor='#000000', bbox_inches='tight', pad_inches=0)
    plt.close()
    print(" -> Guardado: world_provinces_ids.png")

    # 16. Crear Documentación Actualizada
    with open(output_dir / "README_MAP.md", 'w', encoding='utf-8') as f:
        f.write(f"""# 🗺️ Recursos del Mapa Mundial Estratégico (Versión 2.0)

Este paquete contiene los mapas de alta definición y datos geográficos completos para el juego de gran estrategia en Android.

## ✨ Novedades y Mejoras Implementadas:
1. **Base de Datos SQLite (`world_map.db`):**
   - Base de datos relacional compacta lista para Android (Room/SQLite nativo) y libre de saturación para la ventana de contexto de IA.
   - Tablas indexadas: `metadata`, `countries`, `provinces`, `sea_zones`, `strategic_straits` y `major_ports`.
   - Permite consultas ultra rápidas en O(1) y modificaciones directas con apps como DB Browser for SQLite.
2. **Zonas Marítimas Navegables (Sea Zones):**
   - Todos los mares, océanos y golfos están segmentados e indexados (IDs a partir de 10001).
   - Detección táctil directa en el mar y adyacencias topológicas entre mares y costas para convoyes y desembarcos navales.
3. **Puntos Estratégicos Navales:**
   - Ubicación exacta y conexión de canales y estrechos cruciales (Canal de Panamá, Suez, Gibraltar, Magallanes, Bósforo, Malaca, Ormuz, etc.).
4. **Puertos Principales y Capitales:**
   - Mapeo de las bases navales y puertos de mayor tonelaje del mundo con coordenadas exactas en lat/lon y en píxeles.
5. **Realce de Islas Pequeñas:**
   - Las islas pequeñas han sido escaladas geométricamente con preservación de forma para ser visibles y pulsables en pantallas móviles.
6. **Datos Socioeconómicos y de Terreno:**
   - Terreno por provincia (`mountains`, `plains`, `jungle`, `desert`, etc.).
   - Población y mano de obra militar (`manpower`).
   - Recursos estratégicos (`oil`, `iron_and_metals`, `agriculture`, etc.).
   - Capacidad industrial y estado de capital nacional.
7. **Resolución de Inconsistencias:**
   - Mancha negra de Brasil eliminada; colores nacionales armónicos aplicados; Antártida excluida para optimizar pantalla.
""")
    print("=" * 65)
    print("¡SISTEMA CARTOGRÁFICO Y MARÍTIMO GENERADO EXITOSAMENTE!")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Generador de Mapas Mundiales Estratégicos.")
    parser.add_argument("--scale", choices=["10m", "50m", "110m"], default="10m",
                        help="Escala cartográfica de Natural Earth (10m, 50m o 110m). Default: 10m.")
    parser.add_argument("--width", type=int, default=4096, help="Ancho en píxeles (default: 4096).")
    parser.add_argument("--height", type=int, default=2048, help="Alto en píxeles (default: 2048).")
    parser.add_argument("--output-dir", type=str, default="map_data", help="Directorio de salida.")
    parser.add_argument("--include-antarctica", action="store_true", help="Incluir Antártida si se requiere.")

    args = parser.parse_args()
    build_world_map(
        scale=args.scale,
        width=args.width,
        height=args.height,
        output_dir=Path(args.output_dir),
        exclude_antarctica=not args.include_antarctica
    )


if __name__ == "__main__":
    main()
