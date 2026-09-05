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
   - Genera mapas con el 100% de los países del mundo y sus provincias reales con fuentes abiertas de Natural Earth (`Admin 0` y `Admin 1`), incorporando un mecanismo de respaldo territorial (*fallback*) que convierte la geometría soberana en provincia nacional para aquellas naciones sin subdivisiones en Admin 1.
   - Produce tres bases de datos SQLite relacionales indexadas con integridad referencial:
     1. `world_overview.db`: Base ligera orientada a diplomacia, selección de país y consultas de IA (países, fronteras internacionales, capitales y métricas macroeconómicas) que evita saturar la ventana de contexto.
     2. `world_provinces.db`: Base detallada para el motor de simulación móvil (provincias, grafo relacional de adyacencias `province_neighbors` para pathfinding A*, recursos y mares navegables).
     3. `world_map.db`: Base maestra unificada con todas las capas consolidadas.
   - Produce `world_map_data.json` con países, provincias, zonas marítimas, estrechos, puertos, tipos de terreno y fronteras.
   - Genera el mapa indexado por píxel (`world_provinces_ids.png`) para detección de toques en tiempo `O(1)`: cada provincia y zona marítima tiene un color RGB único `(r, g, b)` tal que `id = R + (G * 256) + (B * 65536)`.
   - Exporta capas vectoriales `world_provinces.geojson`, `world_countries.geojson` y `world_sea_zones.geojson` para posibilitar modificaciones manuales futuras en QGIS o geojson.io.

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
