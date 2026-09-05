# 📁 Estructura del Proyecto (Architecture & Folder Tree)

Detalle de la jerarquía de directorios, módulos y componentes del juego, su mini motor nativo y el pipeline cartográfico.

---

## 🌳 Árbol General de Archivos

```text
├── .github/                           # Automatización y CI/CD
│   └── workflows/
│       ├── generate-world-map.yml     # Flujo manual de generación de mapas mundiales y GIS
│       ├── build-debug-apk.yml        # Flujo manual de compilación de APK Debug
│       └── override-commit-message.yml # Flujo de reescritura de commits en español
├── .gitignore                         # Reglas de exclusión para Git (Java, C++, Rust, Lua, GIS Cache)
├── commit_message.txt                 # Mensaje canónico de commit en español
├── README.md                          # Visión general y guía rápida
├── ROADMAP.md                         # Fases y hoja de ruta de desarrollo
├── STRUCTURE.md                       # Estructura de archivos y módulos
├── AI_CONTEXT.md                      # Contexto técnico para asistentes de IA
├── AGENTS.md                          # Instrucciones y reglas obligatorias para agentes
├── gradlew                            # Script de Gradle Wrapper
├── build.gradle.kts                   # Configuración Gradle raíz del proyecto
├── settings.gradle.kts                # Configuración de repositorios y módulos
│
├── scripts/                           # Herramientas y Pipelines de Datos
│   ├── generate_world_map.py          # Generador de mapas mundiales, provincias, fronteras y JSON
│   └── requirements.txt               # Dependencias GIS (geopandas, shapely, matplotlib, pillow)
│
├── map_data/                          # Salida de la Generación Cartográfica (artefactos)
│   ├── world_overview.db              # Base SQLite ligera (países, fronteras internacionales, métricas, para IA)
│   ├── world_provinces.db             # Base SQLite detallada (provincias, grafo de vecinos para pathfinding, mares)
│   ├── world_map.db                   # Base SQLite unificada maestra
│   ├── world_map_data.json            # Dataset maestro JSON con países, provincias, economía y adyacencias
│   ├── world_provinces_blank.png      # Mapa táctico con delimitación de fronteras y mares
│   ├── world_provinces_political.png  # Mapa coloreado por soberanía nacional, puertos y canales
│   ├── world_provinces_ids.png        # Mapa de IDs por canal RGB exacto (tiempo O(1))
│   ├── world_provinces.geojson        # Capa vectorial estándar de provincias (editable en QGIS/web)
│   ├── world_countries.geojson        # Capa vectorial estándar de países (editable en QGIS/web)
│   ├── world_sea_zones.geojson        # Capa vectorial estándar de zonas marítimas (editable en QGIS/web)
│   └── README_MAP.md                  # Documentación de uso y edición del mapa
│
└── app/
    ├── .gitignore                     # Exclusiones específicas del módulo app
    ├── build.gradle.kts               # Configuración Android, NDK, CMake y tarea de Rust
    ├── proguard-rules.pro             # Reglas de optimización ProGuard
    │
    └── src/
        └── main/
            ├── AndroidManifest.xml    # Manifiesto de Android (orientación landscape y permisos)
            │
            ├── assets/                # Recursos y mapas del juego
            │   ├── world_map/         # Directorio sincronizado de mapas generados
            │   │   ├── world_map_data.json
            │   │   ├── world_provinces_blank.png
            │   │   ├── world_provinces_ids.png
            │   │   └── world_provinces_political.png
            │   ├── blank_province_map.png      # Mapa base regional (5632x2048)
            │   └── political_province_map.png  # Mapa rasterizado regional
            │
            ├── cpp/                   # Mini Motor Nativo en C++20 y Lua
            │   ├── CMakeLists.txt     # Script de compilación CMake (compila C++, Lua y enlaza Rust)
            │   ├── strategy_engine.cpp# Implementación C++ con interfaz JNI
            │   └── lua/               # Código fuente oficial y puro de Lua 5.4.6 (ANSI C)
            │       ├── lua.h, luaconf.h, lualib.h, lauxlib.h
            │       ├── lapi.c, lvm.c, ldo.c, lgc.c, ltable.c, etc. (60 archivos)
            │
            ├── rust/                  # Núcleo de Simulación de Alto Rendimiento
            │   ├── Cargo.toml         # Manifiesto de la biblioteca Rust (strategy_core)
            │   ├── build_rust.sh      # Script de compilación para arquitecturas Android
            │   └── src/
            │       └── lib.rs         # Lógica militar y matemática sin Garbage Collector
            │
            ├── java/com/example/      # Código Kotlin de la Aplicación
            │   ├── MainActivity.kt    # Actividad principal en Compose
            │   │
            │   ├── data/              # Modelos de datos del juego
            │   │   ├── model/GameState.kt
            │   │   └── repository/GameDataRepository.kt
            │   │
            │   ├── engine/            # Integración nativa con Kotlin
            │   │   └── NativeEngineBridge.kt # Interfaz JNI para C++, Rust y Lua
            │   │
            │   ├── ui/                # Capa visual (Jetpack Compose)
            │   │   ├── screens/       # MainGameScreen.kt
            │   │   ├── map/           # StrategyMapCanvas.kt
            │   │   ├── components/    # Diálogos tácticos, HUD y controles
            │   │   └── theme/         # Temas, tipografía y colores
            │   │
            │   └── viewmodel/
            │       └── GameViewModel.kt # Estado reactivo y simulación
            │
            └── res/                   # Recursos visuales de Android (strings, drawables, mipmaps)
```

---

## ⚙️ Flujos Principales del Repositorio

1. **Flujo Cartográfico (GitHub Actions `generate-world-map.yml`):**
   - Ejecutado manualmente cuando se requiera actualizar o reescalar el mapa mundial.
   - Procesa datos cartográficos con Python (`scripts/generate_world_map.py`).
   - Genera imágenes de alta resolución, archivos GeoJSON editables y el archivo `world_map_data.json` con la topología de fronteras.
   - Exporta los archivos exclusivamente como artefacto descargable (ZIP), asegurando que el repositorio de Git permanezca limpio sin archivos binarios generados.

2. **Flujo de Compilación Android (Gradle & NDK):**
   - **Rust:** Tarea `buildRustCore` compila `libstrategy_core.a` para `arm64-v8a` y `x86_64`.
   - **C++ y Lua:** CMake compila `strategy_engine.cpp` y el código fuente original de Lua 5.4.
   - **Enlace:** Produce `libnative-strategy-engine.so` listo para ser cargado por JNI desde Kotlin.
