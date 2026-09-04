# Gran Estrategia Latinoamérica (RTS Mini-Engine)

Juego de gran estrategia geopolítica en tiempo real para Android ambientado en Latinoamérica con proyección mundial, inspirado en la profundidad territorial, militar y diplomática de los grandes juegos de estrategia histórica.

El proyecto está diseñado bajo una **arquitectura híbrida de alto rendimiento**, combinando una interfaz reactiva en Jetpack Compose con un mini motor nativo integrado en **C++20**, **Rust** y **Lua 5.4.6 original (puro)**, junto a un **sistema automatizado de cartografía global y datos GIS en GitHub Actions**.

---

## 🏛️ Arquitectura del Sistema

| Capa | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Interfaz & UX** | Kotlin + Jetpack Compose | Menús de selección de naciones, HUD superior, controles táctiles y visor de mapa. |
| **Puente JNI & Enlace** | C++20 (NDK Clang) | Gestión del ciclo de vida nativo, comunicación bidireccional y orquestación. |
| **Simulador Militar & IA** | Rust (`strategy_core`) | Cálculos sin pausas de Garbage Collector: bajas de combate, evaluación de amenazas y pathfinding. |
| **Lógica de Eventos & Mods** | Lua 5.4.6 (ANSI C puro) | Motor de eventos históricos, decisiones diplomáticas y capacidad de modding sin wrappers. |
| **Cartografía & Pipeline GIS** | Python + GitHub Actions | Generación automatizada de mapas mundiales en alta resolución, provincias, fronteras y datasets JSON. |

---

## 🚀 Características Principales

- **Cobertura Territorial y Provincias Reales:**
  - Sistema cartográfico con todos los países del mundo y sus subdivisiones provinciales/departamentales/estatales.
  - Fronteras soberanas gruesas y fronteras provinciales tácticas claramente diferenciadas.
- **Selección de Países de Latinoamérica:** México, Colombia, Argentina, Brasil, Perú, Chile, Venezuela, Bolivia, Ecuador, Paraguay, Uruguay, Centroamérica y el Caribe.
- **Detección Táctil de Provincias en Tiempo O(1):**
  - Mapa indexado por canal RGB (`world_provinces_ids.png`) que permite saber al instante qué provincia tocó el jugador sin sobrecargar la CPU con cálculos de polígonos.
- **Etiquetas en Espacio de Pantalla:** Indicadores de tropas y nombres que no obstruyen la visualización al hacer zoom táctico.
- **Motor Nativo Multilenguaje:**
  - Código C++ optimizado con enlace directo por JNI.
  - Núcleo Rust compilado en bibliotecas estáticas nativas (`.a`) para `arm64-v8a` y `x86_64`.
  - Código fuente completo de Lua 5.4 oficial embebido en el proyecto para máxima libertad y extensibilidad.

---

## 🗺️ Generador Automatizado de Mapas Mundiales (GitHub Actions)

Para evitar buscar mapas manualmente en internet o lidiar con imágenes sin división provincial adecuada, el repositorio cuenta con un **flujo de trabajo automatizado y activable manualmente** que procesa datos de dominio público de Natural Earth (`Admin 0` países y `Admin 1` estados/provincias):

### Cómo Ejecutar el Generador
1. Ve a la pestaña **Actions** en tu repositorio de GitHub (accesible desde el navegador de tu móvil o cualquier dispositivo).
2. Selecciona el flujo **Generate World Map** en el menú lateral izquierdo.
3. Toca **Run workflow**.
4. Puedes configurar los siguientes parámetros:
   - **Nivel de detalle geográfico:** `10m` (ultra detallado), `50m` (equilibrado recomendado) o `110m` (rápido).
   - **Ancho y Alto:** Resolución en píxeles (por defecto `4096` x `2048`, o resoluciones mayores como `8192` x `4096`).
5. El flujo genera y empaqueta:
   - `world_provinces_political.png`: Mapa político con colores patrios históricos de todas las naciones, zonas marítimas navegables, puertos clave y canales/estrechos estratégicos.
   - `world_provinces_blank.png`: Mapa táctico limpio con provincias y mares, ideal como lienzo para mods.
   - `world_provinces_ids.png`: Mapa de IDs por píxel RGB (provincias terrestres y mares indexados) para detección táctil instantánea en tiempo O(1).
   - `world_map.db`: Base de datos relacional SQLite completa e indexada para Android (Room o nativo). Evita saturar la ventana de contexto de las IAs y permite consultas instantáneas en O(1).
   - `world_map_data.json`: Archivo JSON completo con países, provincias, zonas marítimas, estrechos/canales, puertos, adyacencias topológicas, tipos de terreno, acceso al mar, demografía y recursos económicos.
   - `world_provinces.geojson`, `world_countries.geojson` y `world_sea_zones.geojson`: Capas vectoriales estándar editables en QGIS o geojson.io.
   - **Artefacto descargable (ZIP):** Todos los archivos se empaquetan en un artefacto descargable (con 90 días de retención). **Nunca se commitean al repositorio** para que puedas revisarlos y probarlos tranquilamente en tu dispositivo sin ensuciar Git.

### Modificación del Mapa para el Futuro
El mapa generado no es estático; se puede modificar de múltiples formas conforme avance el juego:
- **En la web con [geojson.io](https://geojson.io):** Arrastra el archivo `world_provinces.geojson`, edita los vértices de las fronteras, divide o une provincias y guárdalo de nuevo.
- **Con QGIS (GIS profesional gratuito):** Abre las capas vectoriales para ajustar fronteras históricas personalizadas.
- **Ajustando los parámetros:** Vuelve a ejecutar el GitHub Action con otra escala o resolución en cualquier momento.

---

## 🛠️ Cómo Compilar y Generar el APK

El proyecto está preparado para compilarse y distribuirse directamente como APK independiente (ideal para tiendas de terceros como Uptodown o instalación manual directa en dispositivos móviles):

### Compilación Local
```bash
# Compilar el APK en modo depuración (incluye Rust, C++ y Lua)
./gradlew assembleDebug
```

El APK generado se encontrará en:
`app/build/outputs/apk/debug/app-debug.apk`

---

## 🤖 Flujos de Integración Continua (GitHub Actions)

El repositorio incluye tres flujos de trabajo automatizados en `.github/workflows/`:

1. **`generate-world-map.yml` (Generador de Mapa Mundial y Datos GIS):**
   - Activación manual (`workflow_dispatch`).
   - Descarga datos vectoriales de Natural Earth, calcula adyacencias de fronteras, genera mapas PNG en alta resolución y el archivo `world_map_data.json`.
   - Sincroniza los mapas en `app/src/main/assets/world_map/` y sube un paquete descargable con 90 días de retención.

2. **`build-debug-apk.yml` (Compilación Manual de APK Debug):**
   - Activación manual (`workflow_dispatch`).
   - Configura JDK 17, Android SDK, NDK 26, CMake 3.22 y toolchain de Rust (`aarch64-linux-android` y `x86_64-linux-android`).
   - Compila el APK Debug **sin caché** con todo el código nativo y lo publica como artefacto descargable (`app-debug.apk`).

3. **`override-commit-message.yml` (Gestión de Mensajes de Commit):**
   - Activación automática tras cada `push` a las ramas principales.
   - Lee `commit_message.txt` para mantener el historial estandarizado y en español.

---

## 📂 Organización de Fuentes

- `scripts/`: Script de procesamiento cartográfico (`generate_world_map.py`, `requirements.txt`).
- `app/src/main/rust/`: Código fuente de Rust (`Cargo.toml`, `src/lib.rs` y script `build_rust.sh`).
- `app/src/main/cpp/lua/`: Código fuente oficial de Lua 5.4.6 en ANSI C puro.
- `app/src/main/cpp/`: Motor C++ y puente JNI (`strategy_engine.cpp`, `CMakeLists.txt`).
- `app/src/main/java/com/example/`: Código Kotlin en Jetpack Compose, ViewModels y puente nativo.
- `app/src/main/assets/`: Recursos del mapa y assets del juego.

---

## 📜 Licencia y Distribución
Desarrollado para distribución independiente en plataformas móviles Android.
