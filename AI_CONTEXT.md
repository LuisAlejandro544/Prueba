# 🧠 AI Context & Domain Knowledge

Este archivo proporciona contexto técnico para cualquier modelo de Inteligencia Artificial que colabore en este proyecto.

---

## 🎯 Resumen del Proyecto

- **Género:** Gran Estrategia Geopolítica en Tiempo Real (RTS) para Android.
- **Escenario Actual:** Latinoamérica con expansión global a todos los países del mundo.
- **Inspiración:** Profundidad territorial y táctica de los grandes juegos de estrategia histórica clásica.
- **Orientación:** Fija en modo horizontal (*Landscape*).

---

## 🏗️ Arquitectura del Sistema

El juego divide sus responsabilidades en cinco componentes especializados:

1. **Capa Visual & UX (Kotlin + Jetpack Compose):**
   - Maneja el ciclo de vida de las vistas, gestos táctiles (*pinch-to-zoom*, *pan*, *tap*), y el renderizado del Canvas.
   - **Regla de Oro de Renderizado:** Las etiquetas de ejércitos y los nombres de provincias se deben dibujar en **espacio de pantalla (*screen-space*)**, nunca sujetos a la matriz de transformación del zoom, para evitar que aumenten desproporcionadamente de tamaño y tapen el mapa.

2. **Capa Intermedia & JNI (C++20):**
   - Archivos: `app/src/main/cpp/strategy_engine.cpp` y `CMakeLists.txt`.
   - Inicializa el entorno nativo, gestiona el paso de datos entre Kotlin y el motor, y alberga el punto de enlace JNI.

3. **Capa de Simulación Militar & IA (Rust):**
   - Archivos: `app/src/main/rust/src/lib.rs` (`strategy_core`).
   - Todo cálculo intensivo que deba ejecutarse periódicamente (resolución de bajas de combate, evaluación de amenazas de países vecinos, búsqueda de caminos de ejércitos) debe programarse en Rust para evitar cualquier pausa por el Garbage Collector (GC) de Android.

4. **Capa de Scripting & Eventos (Lua 5.4.6 Puro):**
   - Archivos: `app/src/main/cpp/lua/*.c` y `*.h`.
   - Se utiliza **Lua original en bruto (ANSI C)**, sin envoltorios (*wrappers*) externos.
   - Diseñado para ejecutar scripts de eventos diplomáticos, misiones históricas y futuros mods creados por la comunidad.

5. **Pipeline de Cartografía Global & Datos GIS (Python + GitHub Actions):**
   - Archivos: `.github/workflows/generate-world-map.yml` y `scripts/generate_world_map.py`.
   - **Escala 10M Predeterminada:** Configuración por defecto a escala 10m (máxima resolución de Natural Earth) para una definición cartográfica superior.
   - Genera mapas con el 100% de los países del mundo y sus provincias reales con fuentes abiertas de Natural Earth (`Admin 0` y `Admin 1`), incorporando un mecanismo de respaldo territorial (*fallback*) que convierte la geometría soberana en provincia nacional para aquellas naciones sin subdivisiones en Admin 1.
   - Corrige anomalías topológicas y huecos en provincias aplicando validación y limpieza geométrica estricta (`safe_clean_geometry` con `make_valid` y `buffer(0)`).
   - **Datasets 10M de Alta Fidelidad Integrados:** Costas de alta definición (`coastline`), campos de hielo y glaciares perpetuos (`glaciated_areas`), red ferroviaria mundial (`railroads`), bases aéreas y aeropuertos (`airports`), manchas urbanas (`urban_areas`), arrecifes de coral (`reefs`), cuadrícula de coordenadas náuticas (`graticules_10`), líneas geográficas tácticas (`geographic_lines`), lagos (`lakes`), ríos (`rivers_lake_centerlines`), regiones físicas (`geography_regions_polys`), urbes pobladas (`populated_places`) y puertos oficiales (`ports`).
   - **Estética Militar de Gran Estrategia (Hearts of Iron IV Style):**
     - Océano táctico en azul marino de almirantazgo (`#0a192f`) con cuadrícula de coordenadas navales discretas.
     - Paleta de naciones militar sobria y desaturada con alto contraste sobre el lienzo oceánico.
     - Doble trazo en fronteras soberanas (halo exterior oscuro y línea interior nítida blanca) simulando los mapas de operaciones de estados mayores.
     - Glaciares y campos de hielo árticos/andinos/himalayos destacados en blanco escarcha táctico (`#f1f5f9`).
     - Trazado de vías ferroviarias de suministro logístico y aeródromos militares.
   - Produce bases de datos SQLite relacionales indexadas con integridad referencial (`world_overview.db`, `world_provinces.db` y `world_map.db`), ampliadas con tablas de `airports`, `railroads` y `glaciers`.
   - **Vinculación Táctil en la App:** Algoritmo de Ray-Casting (Point-in-Polygon) para detectar el toque exacto dentro de los polígonos provinciales y selección de proximidad adaptativa para pantallas móviles en `StrategyMapCanvas`.
   - **Estado de Integración en la App:** Los assets de la app integran directamente `world_provinces_political.png` (4096x1675), `world_overview.db`, `world_provinces.db` y `world_map.db`. La selección y jugabilidad estratégica están habilitadas para los países de Latinoamérica sobre la geografía y mapa mundial.

---

## 📱 Perfil del Usuario y Restricciones Técnicas

- **Dispositivo del Usuario:** El usuario opera principalmente desde un dispositivo móvil (teléfono).
- **Canal de Distribución:** El APK se distribuye en tiendas alternativas como **Uptodown** o descarga directa de APK.
- **Compilación Nativa Obligatoria:** Cuando se integre código en C++, Rust o Lua, las herramientas de Gradle **deben compilar las librerías nativas reales**. Está estrictamente prohibido simular o sustituir librerías nativas con código alternativo simulado (*fallback mock*) cuando el usuario solicita una tecnología específica.
- **Propiedad Intelectual:** No utilizar nombres de marcas protegidas por derechos de autor que puedan poner en riesgo al usuario.
- **Uso de Dependencias Reales:** Se prefieren herramientas y librerías completas y funcionales por sobre soluciones improvisadas sin dependencias. El peso final del APK no es una restricción limitante.

---

## 🛠️ Herramientas y Automatización (GitHub Actions)

- **`generate-world-map.yml`:** Flujo manual (`workflow_dispatch`) que procesa datos GIS con Python, genera los mapas en PNG de alta resolución y el JSON con todas las fronteras, exportándolos exclusivamente como artefacto descargable (ZIP) sin tocar ni commitear en el árbol de fuentes del repositorio.
- **`build-debug-apk.yml`:** Flujo manual (`workflow_dispatch`) para compilar el APK Debug completo con NDK 26, CMake y Rust, generando la firma en el runner y exportando el APK listo para instalar.
- **`override-commit-message.yml`:** Sincronización automática de mensajes de commit en español leyendo el archivo canónico `commit_message.txt`.
