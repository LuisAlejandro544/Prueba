# 🗺️ Hoja de Ruta de Desarrollo (Roadmap)

Plan de evolución estratégica y técnica para el juego, su mini motor nativo y el ecosistema cartográfico.

---

### ✅ Fase 1: Fundamentos Visuales y Geopolíticos (Completada)
- [x] Orientación horizontal fija (*Landscape*) optimizada para móviles.
- [x] Selección completa de países de Latinoamérica con banderas, capitales y estadísticas iniciales.
- [x] Renderizado de mapa provincial con colores patrios nítidos y fronteras tácticas.
- [x] Sistema de zoom y arrastre (*pinch-to-zoom* y *pan*) fluido.
- [x] Centrado dinámico de cámara en la capital del jugador al comenzar la partida.
- [x] Visor de mapa de alta resolución con alternancia entre mapa político y mapa en blanco.
- [x] Etiquetas de ejércitos y provincias fijadas en espacio de pantalla para evitar obstrucción visual.

---

### ✅ Fase 2: Infraestructura del Mini Motor Nativo y CI/CD (Completada)
- [x] Integración de compilación nativa en Gradle con NDK y CMake 3.22.
- [x] Implementación de **Rust Core** (`strategy_core`) para simulación matemática y lógica pesada sin Garbage Collector.
- [x] Inclusión del código fuente original de **Lua 5.4.6** (ANSI C en bruto, sin wrappers de terceros).
- [x] Capa intermedia en **C++20** con puente JNI (`NativeEngineBridge`) comunicando Kotlin, Lua y Rust.
- [x] Reglas de exclusión en `.gitignore` para artefactos de compilación nativa.
- [x] GitHub Action `build-debug-apk.yml` para compilación manual de APK Debug sin caché y generación de firma.
- [x] GitHub Action `override-commit-message.yml` con sincronización de commits vía `commit_message.txt`.

---

### ✅ Fase 3: Pipeline Automatizado de Cartografía Mundial y Datos GIS (Completada)
- [x] Creación del script generador de mapas geoespaciales (`scripts/generate_world_map.py`) con librerías estándar GIS (`geopandas`, `shapely`, `matplotlib`, `pillow`).
- [x] Extracción y procesamiento de todas las provincias (`Admin 1`) y países soberanos (`Admin 0`) de la base de datos abierta Natural Earth.
- [x] Generación del dataset maestro estructurado `world_map_data.json` y la base de datos relacional `world_map.db` (SQLite) con esquema indexado, permitiendo consultas SQL ultra rápidas y protegiendo la ventana de contexto de las IAs contra saturación.
- [x] Renderizado automático de tres modalidades de mapa en alta resolución:
  - Mapa táctico con delimitación de fronteras provinciales e internacionales destacadas (`world_provinces_blank.png`).
  - Mapa político con tonos patrios armonizados (`world_provinces_political.png`).
  - Mapa indexado por canal RGB (`world_provinces_ids.png`) para selección táctil instantánea O(1) sin sobrecargar el procesador móvil.
- [x] Exportación de capas vectoriales abiertas `world_provinces.geojson`, `world_countries.geojson` y `world_sea_zones.geojson` editables en software GIS (QGIS) o herramientas web (geojson.io).
- [x] Flujo de GitHub Actions con activación manual (`generate-world-map.yml`) configurable por escala (10m, 50m, 110m) y dimensiones de imagen, empaquetando los archivos exclusivamente como artefacto descargable (ZIP) sin subirlos al repositorio.

---

### ⏳ Fase 4: Integración del Mapa Mundial en el Motor y Movimiento Táctico
- [x] Reemplazo y eliminación de mapas provisionales anteriores (`blank_province_map.png` y `political_province_map.png`).
- [x] Integración en assets del nuevo mapa mundial de alta fidelidad `world_provinces_political.png` con estética Hearts of Iron IV.
- [x] Incorporación de datasets 10M de máxima definición (costas, glaciares, ferrocarriles, aeropuertos, áreas urbanas, arrecifes y cuadrículas navales).
- [x] Integración de bases de datos relacionales SQLite en assets (`world_overview.db`, `world_provinces.db`, `world_map.db`) con tablas ampliadas de aeropuertos, ferrocarriles y glaciares.
- [x] Vinculación táctil precisa en Compose mediante algoritmo de Ray-Casting (Point-in-Polygon) y búsqueda de proximidad adaptativa para móviles.
- [x] Adaptación de relación de aspecto dinámica y centrado de facción en `StrategyMapCanvas` y `FullMapViewerDialog`.
- [x] Selección interactiva de provincias y países en el mapa mundial con respuesta háptica/visual.
- [x] Mantenimiento de jugabilidad y selección táctica para los países de Latinoamérica sobre el nuevo mapa global.
- [ ] Trazado interactivo de rutas de movimiento y asedio de tropas entre provincias vecinas utilizando el grafo de adyacencias.
- [ ] Implementación de pathfinding A* nativo en Rust para cálculo instantáneo de rutas operacionales.
- [ ] Sistema de combate y asedio ejecutado mediante `rust_strategy_core_calculate_combat`:
  - Modificadores de terreno (montaña, selva, llanura).
  - Bonificaciones defensivas y desgaste militar.

---

### ⏳ Fase 5: Economía y Desarrollo de Provincias
- [ ] Generación de oro, puntos de diplomacia y mano de obra (*manpower*) por provincia.
- [ ] Menú de reclutamiento de infantería, caballería y artillería.
- [ ] Construcción de edificios tácticos:
  - Fuertes defensivos para resistir invasiones.
  - Talleres y centros de suministros para acelerar la economía.
- [ ] Simulación de crecimiento poblacional e ingresos calculados en Rust.

---

### ⏳ Fase 6: Diplomacia, IA y Eventos en Lua
- [ ] Acciones diplomáticas completas:
  - Declarar guerra y firmar tratados de paz con cesión de territorios.
  - Pactos de no agresión y alianzas militares.
  - Mejorar o empeorar relaciones bilaterales.
- [ ] Motor de eventos históricos ejecutados mediante scripts de Lua:
  - Tratados limítrofes.
  - Crisis económicas y revueltas populares.
- [ ] Sistema de Modding: Permitir la lectura de archivos `.lua` externos para crear escenarios y campañas personalizadas.

---

### ⏳ Fase 7: Interfaz Definitiva y Distribución APK
- [ ] Panel de estadísticas globales y clasificación de potencias mundiales.
- [ ] Efectos de sonido tácticos (marcha de ejércitos, clarines de guerra y campanas de paz).
- [ ] Optimización de rendimiento para distribución en tiendas de terceros (Uptodown, descarga directa).
