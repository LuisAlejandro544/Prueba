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
import json
import math
import sqlite3
import zipfile
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import requests
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely.affinity import scale as shp_scale
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
from PIL import Image, ImageDraw


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

# Paleta histórica para grandes potencias y países de Latinoamérica
HISTORICAL_COUNTRY_COLORS = {
    "ARG": "#4da6ff", # Celeste argentino
    "BRA": "#16a34a", # Verde Brasil
    "CHL": "#dc2626", # Rojo Chile
    "COL": "#eab308", # Amarillo Colombia
    "PER": "#be123c", # Carmesí Perú
    "MEX": "#0d9488", # Verde esmeralda México
    "VEN": "#ea580c", # Naranja/Ocre Venezuela
    "BOL": "#84cc16", # Verde lima Bolivia
    "PRY": "#ef4444", # Rojo Paraguay
    "URY": "#38bdf8", # Celeste Uruguay
    "ECU": "#f59e0b", # Dorado Ecuador
    "CUB": "#3b82f6", # Azul Cuba
    "DOM": "#60a5fa", # Azul Caribe
    "GTM": "#0284c7", # Azul Guatemala
    "HND": "#2563eb", # Azul Honduras
    "SLV": "#1d4ed8", # Azul Salvador
    "NIC": "#0ea5e9", # Celeste Nicaragua
    "CRI": "#059669", # Verde Costa Rica
    "PAN": "#b91c1c", # Rojo Panamá
    "USA": "#1d4ed8", # Azul Estados Unidos
    "CAN": "#dc2626", # Rojo Canadá
    "GBR": "#b91c1c", # Rojo británico
    "FRA": "#2563eb", # Azul Francia
    "DEU": "#475569", # Gris acero Alemania
    "RUS": "#991b1b", # Rojo carmesí Rusia
    "CHN": "#ea580c", # Naranja/Rojo China
    "JPN": "#e11d48", # Carmesí Japón
    "ITA": "#15803d", # Verde Italia
    "ESP": "#d97706", # Gualda/Amarillo España
    "PRT": "#047857", # Verde Portugal
    "TUR": "#c026d3", # Magenta Turquía
    "EGY": "#b45309", # Ocre Egipto
    "ZAF": "#0d9488", # Verde Sudáfrica
    "IND": "#06b6d4", # Turquesa India
    "AUS": "#7c3aed", # Violeta Australia
    "SAU": "#65a30d", # Verde olivo Arabia
    "IRN": "#ca8a04", # Mostaza Irán
    "SWE": "#0284c7", # Azul Suecia
    "NOR": "#be123c", # Rojo Noruega
    "FIN": "#e2e8f0", # Blanco/Hielo Finlandia
    "POL": "#f43f5e", # Rosa fuerte Polonia
    "UKR": "#eab308"  # Amarillo Ucrania
}

COUNTRY_PALETTE = [
    "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
    "#06b6d4", "#e11d48", "#a855f7", "#d97706", "#059669",
    "#2563eb", "#dc2626", "#7c3aed", "#ea580c", "#0891b2",
    "#4f46e5", "#65a30d", "#be123c", "#0d9488", "#b45309"
]

SEA_ZONE_PALETTE = [
    "#1e293b", "#0f172a", "#172554", "#1e3a8a", "#0c4a6e",
    "#164e63", "#083344", "#111827", "#1e1b4b", "#14532d"
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


def normalize_iso(raw_iso: Any, admin_name: str, fallback_prefix: str = "UNK") -> str:
    """Normaliza y rescata códigos ISO para evitar valores nulos, '-99' o fallas en Brasil/otras regiones."""
    iso = str(raw_iso).strip().upper() if raw_iso is not None else ""
    if not iso or iso in ("-99", "NONE", "NAN", "NULL", "UNK"):
        name_clean = str(admin_name).strip().lower()
        if "brazil" in name_clean or "brasil" in name_clean:
            return "BRA"
        if "france" in name_clean or "francia" in name_clean:
            return "FRA"
        if "norway" in name_clean or "noruega" in name_clean:
            return "NOR"
        if "united states" in name_clean or "estados unidos" in name_clean:
            return "USA"
        if "somalia" in name_clean or "somaliland" in name_clean:
            return "SOM"
        if "kosovo" in name_clean:
            return "XKX"
        if "cyprus" in name_clean:
            return "CYP"
        return f"{fallback_prefix}_{abs(hash(name_clean)) % 10000}"
    return iso


def enhance_small_islands(geometry, min_area: float = 0.08, scale_factor: float = 2.4):
    """
    Realza geométricamente islas pequeñas e importantes para que no desaparezcan
    en pantallas de teléfonos móviles ni queden como píxeles invisibles, manteniendo su forma y posición realista.
    """
    if geometry is None or geometry.is_empty:
        return geometry

    if geometry.geom_type == 'Polygon':
        if geometry.area < min_area:
            return shp_scale(geometry, xfact=scale_factor, yfact=scale_factor, origin='centroid')
        return geometry
    elif geometry.geom_type == 'MultiPolygon':
        new_polys = []
        for poly in geometry.geoms:
            if poly.area < min_area:
                new_polys.append(shp_scale(poly, xfact=scale_factor, yfact=scale_factor, origin='centroid'))
            else:
                new_polys.append(poly)
        return MultiPolygon(new_polys)
    return geometry


def estimate_province_attributes(name: str, country_iso: str, lat: float, lon: float, is_coastal: bool) -> Dict[str, Any]:
    """
    Estima atributos históricos, demográficos y de terreno realistas y listos para modificar en mods.
    """
    # 1. Terreno basado en geografía real
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
    base_population = 250000 + (abs(hash(name)) % 1500000)
    if country_iso in ["CHN", "IND"]:
        base_population *= 4
    elif country_iso in ["USA", "RUS", "BRA", "DEU", "JPN"]:
        base_population *= 2
    elif terrain in ["desert", "tundra", "mountains"]:
        base_population = max(30000, base_population // 4)

    manpower = int(base_population * 0.12)

    # 3. Recursos históricos
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
    else:
        min_lat, max_lat = -90.0, 90.0

    # 5. Realce de islas pequeñas para legibilidad táctica en dispositivos móviles
    print("[Geometría] Optimizando geometría de islas pequeñas para visibilidad táctica en móvil...")
    gdf_provinces['geometry'] = gdf_provinces['geometry'].apply(enhance_small_islands)

    # Limpiar geometrías nulas
    gdf_provinces = gdf_provinces[gdf_provinces.geometry.notnull() & ~gdf_provinces.geometry.is_empty & gdf_provinces.geometry.is_valid].copy()
    gdf_countries = gdf_countries[gdf_countries.geometry.notnull() & ~gdf_countries.geometry.is_empty & gdf_countries.geometry.is_valid].copy()
    gdf_seas = gdf_seas[gdf_seas.geometry.notnull() & ~gdf_seas.geometry.is_empty & gdf_seas.geometry.is_valid].copy()

    total_provinces = len(gdf_provinces)
    total_countries = len(gdf_countries)
    total_seas = len(gdf_seas)
    print(f"[Estadísticas] Provincias terrestres: {total_provinces}")
    print(f"[Estadísticas] Zonas marítimas: {total_seas}")
    print(f"[Estadísticas] Países/Entidades soberanas: {total_countries}")

    # 6. Estructurar Países y Diccionario
    countries_dict: Dict[str, Any] = {}
    country_color_map: Dict[str, str] = {}

    for idx, row in gdf_countries.iterrows():
        name = str(row.get('NAME', row.get('ADMIN', f'País {idx}'))).strip()
        iso_a3 = normalize_iso(row.get('ISO_A3'), name, fallback_prefix=f"CTY_{idx}")
        if iso_a3.startswith("CTY_") and row.get('ADM0_A3'):
            iso_a3 = normalize_iso(row.get('ADM0_A3'), name, fallback_prefix=f"CTY_{idx}")

        if iso_a3 in HISTORICAL_COUNTRY_COLORS:
            country_color = HISTORICAL_COUNTRY_COLORS[iso_a3]
        else:
            color_idx = abs(hash(iso_a3)) % len(COUNTRY_PALETTE)
            country_color = COUNTRY_PALETTE[color_idx]

        country_color_map[iso_a3] = country_color

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
            if c != i and geom.touches(gdf_seas.geometry.iloc[c]):
                sea_neighbors.append(10001 + c)
        sea_zones_list[i]["adjacent_seas"] = sorted(sea_neighbors)

    # 9. Procesar Provincias Terrestres y Conexión Costa-Mar
    print("[Procesando] Normalizando provincias terrestres, acceso al mar y datos socio-económicos...")
    provinces_list: List[Dict[str, Any]] = []
    gdf_provinces = gdf_provinces.reset_index(drop=True)
    prov_political_colors = []
    prov_id_colors = []

    for idx, row in gdf_provinces.iterrows():
        prov_id = idx + 1
        prov_name = str(row.get('name', row.get('name_en', f'Provincia {prov_id}'))).strip()
        if not prov_name or prov_name == 'None':
            prov_name = f"Provincia {prov_id}"

        admin_name = str(row.get('admin', row.get('adm0_name', ''))).strip()
        raw_iso = row.get('adm0_a3', row.get('iso_a2', ''))
        country_iso = normalize_iso(raw_iso, admin_name)

        if country_iso in country_color_map:
            color_p = country_color_map[country_iso]
        else:
            matched_iso = None
            for c_id, c_data in countries_dict.items():
                if c_data["name"].lower() in admin_name.lower() or admin_name.lower() in c_data["name"].lower():
                    matched_iso = c_id
                    break
            if matched_iso:
                country_iso = matched_iso
                color_p = country_color_map.get(country_iso, "#64748b")
            else:
                color_p = HISTORICAL_COUNTRY_COLORS.get(country_iso, COUNTRY_PALETTE[abs(hash(country_iso)) % len(COUNTRY_PALETTE)])
                country_color_map[country_iso] = color_p

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
            if geom.touches(gdf_seas.geometry.iloc[s]) or geom.intersects(gdf_seas.geometry.iloc[s]):
                adjacent_seas.append(10001 + s)
        is_coastal = len(adjacent_seas) > 0

        # Atributos económicos, demográficos y de terreno
        attributes = estimate_province_attributes(prov_name, country_iso, lat, lon, is_coastal)

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
            if cand != i and geom.touches(gdf_provinces.geometry.iloc[cand]):
                neighbors.append(cand + 1)
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

    straits_mapped = []
    for strait in STRATEGIC_STRAITS:
        px, py = lat_lon_to_pixel(strait["lat"], strait["lon"], width, height, min_lat, max_lat)
        straits_mapped.append({
            **strait,
            "pixel_x": px,
            "pixel_y": py
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
            "version": "2.0",
            "projection": "Equirectangular Cortada (Optimizado Móvil)",
            "bounds": {
                "min_lon": -180.0,
                "max_lon": 180.0,
                "min_lat": min_lat,
                "max_lat": max_lat
            },
            "dimensions": {"width": width, "height": height},
            "scale": scale,
            "total_countries": len(countries_dict),
            "total_land_provinces": len(provinces_list),
            "total_sea_zones": len(sea_zones_list),
            "total_strategic_straits": len(straits_mapped),
            "total_major_ports": len(ports_mapped),
            "ocean_color_id_base": 10001
        },
        "countries": countries_dict,
        "provinces": provinces_list,
        "sea_zones": sea_zones_list,
        "strategic_straits": straits_mapped,
        "major_ports": ports_mapped
    }
    with open(output_dir / "world_map_data.json", 'w', encoding='utf-8') as f:
        json.dump(full_dataset, f, ensure_ascii=False, indent=2)
    print(f" -> Guardado: world_map_data.json ({(output_dir / 'world_map_data.json').stat().st_size / 1024 / 1024:.2f} MB)")

    # 14. Generar Base de Datos SQLite (world_map.db) para Android y consultas de IA sin saturar contexto
    print("[Exportación] Generando base de datos relacional SQLite (world_map.db)...")
    db_path = output_dir / "world_map.db"
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA synchronous = OFF;")
    cur.execute("PRAGMA journal_mode = MEMORY;")

    # Tabla metadata
    cur.execute("""
    CREATE TABLE metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    for k, v in full_dataset["metadata"].items():
        val_str = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
        cur.execute("INSERT INTO metadata (key, value) VALUES (?, ?);", (k, val_str))

    # Tabla countries
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
            c_id,
            c_data["name"],
            c_data["iso_a2"],
            c_data["iso_a3"],
            c_data["continent"],
            c_data["subregion"],
            c_data["color_hex"],
            c_data.get("capital"),
            json.dumps(c_data.get("major_ports", []), ensure_ascii=False)
        ))

    # Tabla provinces
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
            p["id"],
            p["name"],
            p["country_id"],
            p["color_hex"],
            p["color_rgb"][0],
            p["color_rgb"][1],
            p["color_rgb"][2],
            p["centroid"]["lat"],
            p["centroid"]["lon"],
            p["centroid"]["pixel_x"],
            p["centroid"]["pixel_y"],
            1 if p["is_coastal"] else 0,
            json.dumps(p["adjacent_seas"]),
            p["terrain"],
            p["population"],
            p["manpower"],
            p["resource"],
            p["resource_amount"],
            p["industrial_level"],
            1 if p["is_capital"] else 0,
            json.dumps(p["neighbors"])
        ))

    # Tabla sea_zones
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
            s["id"],
            s["name"],
            s["featurecla"],
            s["color_rgb"][0],
            s["color_rgb"][1],
            s["color_rgb"][2],
            s["centroid"]["lat"],
            s["centroid"]["lon"],
            s["centroid"]["pixel_x"],
            s["centroid"]["pixel_y"],
            json.dumps(s["adjacent_seas"]),
            json.dumps(s["adjacent_provinces"])
        ))

    # Tabla strategic_straits
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
            st["id"],
            st["name"],
            st["lat"],
            st["lon"],
            st["pixel_x"],
            st["pixel_y"],
            st["type"],
            json.dumps(st.get("connects", []), ensure_ascii=False)
        ))

    # Tabla major_ports
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
            mp["name"],
            mp["country"],
            mp["lat"],
            mp["lon"],
            mp["pixel_x"],
            mp["pixel_y"],
            mp.get("sea", "")
        ))

    # Índices para acelerar búsquedas en Android / consultas SQL
    cur.execute("CREATE INDEX idx_provinces_country ON provinces(country_id);")
    cur.execute("CREATE INDEX idx_provinces_terrain ON provinces(terrain);")
    cur.execute("CREATE INDEX idx_provinces_coastal ON provinces(is_coastal);")
    cur.execute("CREATE INDEX idx_sea_zones_name ON sea_zones(name);")

    conn.commit()
    conn.close()
    print(f" -> Guardado: world_map.db ({db_path.stat().st_size / 1024 / 1024:.2f} MB)")

    # 15. Renderizado de Imágenes PNG
    dpi = 150
    figsize = (width / dpi, height / dpi)

    # A) Mapa Político Mundial con Mares Navegables, Puntos Estratégicos y Puertos
    print("[Renderizado 1/3] Generando world_provinces_political.png...")
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')

    # 1. Zonas Marítimas con cuadrícula sutil
    gdf_seas.plot(ax=ax, color=sea_colors_political, edgecolor='#1e293b', linewidth=0.35, alpha=0.92)
    # 2. Provincias terrestres con paleta política corregida
    gdf_provinces.plot(ax=ax, color=prov_political_colors, edgecolor='#1f2937', linewidth=0.22)
    # 3. Fronteras soberanas de alto contraste
    gdf_countries.boundary.plot(ax=ax, edgecolor='#ffffff', linewidth=0.9, alpha=0.98)

    # 4. Dibujar Canales y Estrechos Estratégicos (Rombos Dorados)
    for st in straits_mapped:
        ax.plot(st["lon"], st["lat"], marker='D', color='#fbbf24', markersize=3.8, markeredgecolor='#000000', markeredgewidth=0.6, zorder=5)

    # 5. Dibujar Puertos Principales (Círculos Cian)
    for pt in ports_mapped:
        ax.plot(pt["lon"], pt["lat"], marker='o', color='#38bdf8', markersize=3.0, markeredgecolor='#0f172a', markeredgewidth=0.5, zorder=4)

    ax.set_xlim(-180, 180)
    ax.set_ylim(min_lat, max_lat)
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.savefig(output_dir / "world_provinces_political.png", dpi=dpi, facecolor='#0f172a', bbox_inches='tight', pad_inches=0)
    plt.close()
    print(" -> Guardado: world_provinces_political.png")

    # B) Mapa Táctico en Blanco (Lienzo para Mods y Modos de Mapa)
    print("[Renderizado 2/3] Generando world_provinces_blank.png...")
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor('#131d2e')
    ax.set_facecolor('#131d2e')

    # Mares con tono oscuro náutico
    gdf_seas.plot(ax=ax, facecolor='#162235', edgecolor='#1e2d42', linewidth=0.35)
    # Provincias monocromáticas
    gdf_provinces.plot(ax=ax, facecolor='#2d3748', edgecolor='#4a5568', linewidth=0.25)
    # Fronteras soberanas blancas
    gdf_countries.boundary.plot(ax=ax, edgecolor='#f8fafc', linewidth=0.85, alpha=0.95)

    ax.set_xlim(-180, 180)
    ax.set_ylim(min_lat, max_lat)
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.savefig(output_dir / "world_provinces_blank.png", dpi=dpi, facecolor='#131d2e', bbox_inches='tight', pad_inches=0)
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
    parser.add_argument("--scale", choices=["10m", "50m", "110m"], default="50m",
                        help="Escala cartográfica de Natural Earth (10m, 50m o 110m).")
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
