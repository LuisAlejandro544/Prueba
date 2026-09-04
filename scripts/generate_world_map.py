#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Generación Automatizada de Mapas Mundiales con Provincias y Fronteras
Diseñado para juegos de gran estrategia histórica en Android.
Descarga datos geográficos vectoriales abiertos de Natural Earth (Dominio Público),
procesa todas las provincias y países del mundo, calcula adyacencias/fronteras
y genera imágenes de mapa de alta resolución junto con metadatos en JSON y GeoJSON editable.
"""

import os
import sys
import json
import math
import zipfile
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple

import requests
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
from PIL import Image, ImageDraw


# URLs oficiales y espejos de Natural Earth
NATURAL_EARTH_MIRRORS = [
    "https://naturalearth.s3.amazonaws.com",
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/zips"
]

COUNTRY_PALETTE = [
    "#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16",
    "#06b6d4", "#e11d48", "#a855f7", "#d97706", "#059669",
    "#2563eb", "#dc2626", "#7c3aed", "#ea580c", "#0891b2",
    "#4f46e5", "#65a30d", "#be123c", "#0d9488", "#b45309"
]


def download_file(url_list: List[str], dest_path: Path) -> bool:
    """Descarga un archivo intentando varios espejos si alguno falla."""
    headers = {'User-Agent': 'StrategyGame-MapGenerator/1.0 (Open-Source Project)'}
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


def get_shapefile_path(cache_dir: Path, scale: str, dataset_name: str) -> Path:
    """Asegura la existencia y extracción del Shapefile correspondiente."""
    filename = f"ne_{scale}_{dataset_name}.zip"
    zip_path = cache_dir / filename
    extract_folder = cache_dir / f"ne_{scale}_{dataset_name}"

    if not extract_folder.exists() or not any(extract_folder.glob("*.shp")):
        extract_folder.mkdir(parents=True, exist_ok=True)
        if not zip_path.exists():
            urls = [
                f"{mirror}/{scale}_cultural" if "amazon" in mirror else f"{mirror}/{scale}_cultural"
                for mirror in NATURAL_EARTH_MIRRORS
            ]
            success = download_file(urls, zip_path)
            if not success:
                raise RuntimeError(f"No se pudo descargar el conjunto de datos {filename} desde ningún espejo.")

        print(f"[Extracción] Descomprimiendo {zip_path.name}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)

    shp_files = list(extract_folder.glob("*.shp"))
    if not shp_files:
        raise FileNotFoundError(f"No se encontró ningún archivo .shp en {extract_folder}")
    return shp_files[0]


def id_to_rgb(province_id: int) -> Tuple[int, int, int]:
    """Convierte un ID numérico de provincia en un color RGB único para muestreo exacto en el mapa."""
    r = province_id % 256
    g = (province_id // 256) % 256
    b = (province_id // 65536) % 256
    return (r, g, b)


def rgb_to_id(r: int, g: int, b: int) -> int:
    """Convierte un color RGB extraído del mapa al ID de provincia original."""
    return r + (g * 256) + (b * 65536)


def lat_lon_to_pixel(lat: float, lon: float, width: int, height: int) -> Tuple[int, int]:
    """Convierte coordenadas geográficas WGS84 (lat/lon) a píxeles en proyección equirectangular."""
    x = int(((lon + 180.0) / 360.0) * width)
    # Latitud va de 90 (norte) a -90 (sur) -> pixel 0 es norte
    y = int(((90.0 - lat) / 180.0) * height)
    x = max(0, min(width - 1, x))
    y = max(0, min(height - 1, y))
    return (x, y)


def build_world_map(scale: str, width: int, height: int, output_dir: Path):
    """
    Función principal de construcción de mapas y datasets estructurados.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"GENERADOR DE MAPA MUNDIAL DETALLADO (Escala: {scale}, Resolución: {width}x{height})")
    print("=" * 60)

    # 1. Cargar Provincias (Admin 1)
    admin1_shp = get_shapefile_path(cache_dir, scale, "admin_1_states_provinces")
    print(f"[Datos] Cargando provincias desde: {admin1_shp.name}")
    gdf_provinces = gpd.read_file(admin1_shp)
    gdf_provinces = gdf_provinces.to_crs(epsg=4326) # WGS84

    # 2. Cargar Países (Admin 0)
    admin0_shp = get_shapefile_path(cache_dir, scale, "admin_0_countries")
    print(f"[Datos] Cargando fronteras soberanas desde: {admin0_shp.name}")
    gdf_countries = gpd.read_file(admin0_shp)
    gdf_countries = gdf_countries.to_crs(epsg=4326)

    # Filtrar geometrías inválidas o nulas
    gdf_provinces = gdf_provinces[gdf_provinces.geometry.notnull() & gdf_provinces.geometry.is_valid].copy()
    gdf_countries = gdf_countries[gdf_countries.geometry.notnull() & gdf_countries.geometry.is_valid].copy()

    total_provinces = len(gdf_provinces)
    total_countries = len(gdf_countries)
    print(f"[Estadísticas] Provincias procesadas: {total_provinces}")
    print(f"[Estadísticas] Países/Estados soberanos: {total_countries}")

    # 3. Estructurar Diccionario de Países
    countries_dict: Dict[str, Any] = {}
    country_color_map: Dict[str, str] = {}

    for idx, row in gdf_countries.iterrows():
        iso_a3 = str(row.get('ISO_A3', row.get('ADM0_A3', f'CTY_{idx}'))).strip()
        if iso_a3 == "-99" or not iso_a3:
            iso_a3 = str(row.get('ADM0_A3', f'CTY_{idx}')).strip()

        name = str(row.get('NAME', row.get('ADMIN', f'País {idx}'))).strip()
        continent = str(row.get('CONTINENT', 'Desconocido')).strip()
        subregion = str(row.get('SUBREGION', 'Desconocido')).strip()

        # Asignar color de paleta determinista por hash del código ISO
        color_idx = abs(hash(iso_a3)) % len(COUNTRY_PALETTE)
        country_color = COUNTRY_PALETTE[color_idx]
        country_color_map[iso_a3] = country_color

        countries_dict[iso_a3] = {
            "id": iso_a3,
            "name": name,
            "iso_a2": str(row.get('ISO_A2', '')).strip(),
            "iso_a3": iso_a3,
            "continent": continent,
            "subregion": subregion,
            "color_hex": country_color,
            "provinces": []
        }

    # 4. Asignar Provincias con ID único y calcular centroides
    provinces_list: List[Dict[str, Any]] = []
    gdf_provinces = gdf_provinces.reset_index(drop=True)

    print("[Procesando] Calculando centroides, identificadores y paletas...")
    for idx, row in gdf_provinces.iterrows():
        prov_id = idx + 1 # ID 1-indexed (el 0 se reserva para agua/océano)
        prov_name = str(row.get('name', row.get('name_en', f'Provincia {prov_id}'))).strip()
        if not prov_name or prov_name == 'None':
            prov_name = f"Provincia {prov_id}"

        country_iso = str(row.get('adm0_a3', row.get('iso_a2', 'UNK'))).strip()
        country_name = str(row.get('admin', row.get('adm0_name', 'País Desconocido'))).strip()
        type_en = str(row.get('type_en', row.get('type', 'Province'))).strip()

        # Centroide geométrico
        geom = row.geometry
        centroid = geom.centroid
        lat = float(centroid.y)
        lon = float(centroid.x)
        pixel_x, pixel_y = lat_lon_to_pixel(lat, lon, width, height)

        r, g, b = id_to_rgb(prov_id)
        color_hex = f"#{r:02x}{g:02x}{b:02x}"

        prov_data = {
            "id": prov_id,
            "name": prov_name,
            "country_id": country_iso,
            "country_name": country_name,
            "type": type_en,
            "color_rgb": {"r": r, "g": g, "b": b, "hex": color_hex},
            "center": {
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "pixel_x": pixel_x,
                "pixel_y": pixel_y
            },
            "bounds": [round(coord, 4) for coord in geom.bounds], # [minx, miny, maxx, maxy]
            "neighbors": [] # Se calcula a continuación
        }

        provinces_list.append(prov_data)
        if country_iso in countries_dict:
            countries_dict[country_iso]["provinces"].append(prov_id)

    # 5. Cálculo Espacial de Fronteras / Provincias Vecinas (Adyacencias)
    print("[Fronteras] Calculando adyacencias topológicas entre provincias...")
    sindex = gdf_provinces.sindex
    for i, row in gdf_provinces.iterrows():
        prov_id = i + 1
        geom = row.geometry
        # Candidatos espaciales usando el R-tree index
        candidate_indices = list(sindex.intersection(geom.bounds))
        neighbors: List[int] = []
        for cand_idx in candidate_indices:
            if cand_idx != i:
                cand_geom = gdf_provinces.geometry.iloc[cand_idx]
                if geom.touches(cand_geom):
                    neighbors.append(int(cand_idx + 1))
        provinces_list[i]["neighbors"] = sorted(neighbors)

    # 6. Guardar GeoJSON editable para que el usuario pueda modificarlo en QGIS, Inkscape o editores web
    print("[Exportación] Guardando capas vectoriales editables GeoJSON...")
    geojson_prov_path = output_dir / "world_provinces.geojson"
    geojson_cty_path = output_dir / "world_countries.geojson"
    gdf_provinces.to_file(geojson_prov_path, driver="GeoJSON")
    gdf_countries.to_file(geojson_cty_path, driver="GeoJSON")
    print(f" -> Guardado: {geojson_prov_path.name}")
    print(f" -> Guardado: {geojson_cty_path.name}")

    # 7. Guardar JSON estructurado maestro
    print("[Exportación] Guardando metadatos completos en world_map_data.json...")
    json_path = output_dir / "world_map_data.json"
    full_dataset = {
        "metadata": {
            "projection": "Equirectangular (WGS84 lat/lon)",
            "width": width,
            "height": height,
            "scale": scale,
            "total_countries": len(countries_dict),
            "total_provinces": len(provinces_list),
            "ocean_color_id": 0
        },
        "countries": countries_dict,
        "provinces": provinces_list
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(full_dataset, f, ensure_ascii=False, indent=2)
    print(f" -> Guardado: {json_path.name} ({json_path.stat().st_size / 1024 / 1024:.2f} MB)")

    # 8. Renderizar Imágenes PNG de Alta Resolución
    dpi = 150
    figsize = (width / dpi, height / dpi)

    # A) Mapa en Blanco / Visual Táctico
    # Océano suave, Provincias delimitadas con línea fina, Países con línea destacada
    print("[Renderizado 1/3] Generando world_provinces_blank.png...")
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor('#1a2332') # Océano estilo estratégico naval
    ax.set_facecolor('#1a2332')

    # Relleno de tierra / provincias
    gdf_provinces.plot(ax=ax, facecolor='#2d3748', edgecolor='#4a5568', linewidth=0.25)
    # Fronteras internacionales gruesas y nítidas
    gdf_countries.boundary.plot(ax=ax, edgecolor='#e2e8f0', linewidth=0.8, alpha=0.9)

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    blank_png_path = output_dir / "world_provinces_blank.png"
    plt.savefig(blank_png_path, dpi=dpi, facecolor='#1a2332', bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f" -> Guardado: {blank_png_path.name}")

    # B) Mapa Político Mundial
    print("[Renderizado 2/3] Generando world_provinces_political.png...")
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor('#151e29')
    ax.set_facecolor('#151e29')

    # Mapear colores de país a las provincias
    prov_colors = []
    for _, row in gdf_provinces.iterrows():
        c_iso = str(row.get('adm0_a3', row.get('iso_a2', 'UNK'))).strip()
        prov_colors.append(country_color_map.get(c_iso, '#64748b'))

    gdf_provinces.plot(ax=ax, color=prov_colors, edgecolor='#1e293b', linewidth=0.2)
    gdf_countries.boundary.plot(ax=ax, edgecolor='#ffffff', linewidth=0.9, alpha=0.95)

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    political_png_path = output_dir / "world_provinces_political.png"
    plt.savefig(political_png_path, dpi=dpi, facecolor='#151e29', bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f" -> Guardado: {political_png_path.name}")

    # C) Mapa Indexado por Color (Color-Indexed ID Map para detección táctil sin raycasting)
    print("[Renderizado 3/3] Generando world_provinces_ids.png (Pixel ID Map)...")
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor('#000000') # Negro puro (0,0,0) = Agua/Océano
    ax.set_facecolor('#000000')

    id_colors = []
    for prov in provinces_list:
        id_colors.append(prov["color_rgb"]["hex"])

    # Pintar cada provincia con su color exacto sin bordes (sin anti-aliasing)
    gdf_provinces.plot(ax=ax, color=id_colors, edgecolor='none', linewidth=0)

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.axis('off')
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    ids_png_path = output_dir / "world_provinces_ids.png"
    plt.savefig(ids_png_path, dpi=dpi, facecolor='#000000', bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f" -> Guardado: {ids_png_path.name}")

    # 9. Crear Documentación y Guía de Modificación
    readme_map_path = output_dir / "README_MAP.md"
    with open(readme_map_path, 'w', encoding='utf-8') as f:
        f.write(f"""# 🗺️ Recursos del Mapa Mundial (Generación Automatizada)

Este directorio contiene los mapas y conjuntos de datos geográficos generados automáticamente para el motor de estrategia.

## 📦 Archivos Generados

1. **`world_map_data.json`**:
   - Diccionario completo con **{len(countries_dict)} países** y **{len(provinces_list)} provincias**.
   - Cada provincia incluye: nombre, país soberano, centroide (lat/lon y píxeles exactos `x, y`), color RGB indexado, y lista de **fronteras/vecinos adyacentes** para pathfinding y combate.

2. **`world_provinces_blank.png`** ({width}x{height}):
   - Mapa táctico con delimitación limpia de fronteras provinciales e internacionales destacadas. Ideal como lienzo base.

3. **`world_provinces_political.png`** ({width}x{height}):
   - Mapa coloreado por país soberano con fronteras de alta definición.

4. **`world_provinces_ids.png`** ({width}x{height}):
   - Mapa indexado por color único (RGB exacto).
   - Al tocar la pantalla en `(x, y)`, el motor en Kotlin/C++ lee el píxel: `id = R + (G * 256) + (B * 65536)`. Si `id == 0`, es océano. Esto permite selección de provincias instantánea en tiempo O(1).

5. **`world_provinces.geojson`** y **`world_countries.geojson`**:
   - Capas vectoriales estándar de la industria.

---

## ✏️ ¿Cómo Modificar el Mapa para el Futuro?

Puedes editar las fronteras o añadir provincias personalizadas de 3 maneras sencillas:

1. **En la Web (Sin instalar nada):**
   - Ve a [geojson.io](https://geojson.io) y arrastra el archivo `world_provinces.geojson`.
   - Modifica los vértices, divide o fusiona territorios y descárgalo de nuevo.

2. **Con software GIS profesional gratuito (QGIS):**
   - Abre `world_provinces.geojson` en QGIS.
   - Utiliza las herramientas de edición de polígonos para cambiar fronteras históricas (por ejemplo, 1936 o época victoriana).

3. **Re-ejecutar el GitHub Action:**
   - Puedes ir a la pestaña **Actions** en GitHub, seleccionar **Generate World Map** y ejecutarlo con la resolución y escala deseada (`10m`, `50m` o `110m`).
""")
    print(f" -> Guardado: {readme_map_path.name}")
    print("=" * 60)
    print("¡GENERACIÓN DE MAPA MUNDIAL COMPLETADA EXITOSAMENTE!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Generador de Mapas Mundiales para Juegos de Estrategia.")
    parser.add_argument("--scale", choices=["10m", "50m", "110m"], default="50m",
                        help="Escala de detalle cartográfico de Natural Earth (10m = ultra detallado, 50m = recomendado, 110m = rápido).")
    parser.add_argument("--width", type=int, default=4096, help="Ancho del mapa en píxeles (default: 4096).")
    parser.add_argument("--height", type=int, default=2048, help="Alto del mapa en píxeles (default: 2048).")
    parser.add_argument("--output-dir", type=str, default="map_data", help="Directorio de destino.")

    args = parser.parse_args()
    build_world_map(args.scale, args.width, args.height, Path(args.output_dir))


if __name__ == "__main__":
    main()
