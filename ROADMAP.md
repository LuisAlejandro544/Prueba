# 🗺️ Hoja de Ruta de Desarrollo (Roadmap)

Plan de evolución estratégica y técnica para el juego y su mini motor nativo.

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

### ⏳ Fase 3: Sistema Militar y Movimiento Táctico (Próxima)
- [ ] Selección interactiva de regimientos en el mapa provincial.
- [ ] Trazado de rutas de movimiento de tropas entre provincias vecinas.
- [ ] Implementación de pathfinding A* nativo en Rust para cálculo instantáneo de rutas.
- [ ] Sistema de combate y asedio ejecutado mediante `rust_strategy_core_calculate_combat`:
  - Modificadores de terreno (montaña, selva, llanura).
  - Bonificaciones defensivas y desgaste militar.

---

### ⏳ Fase 4: Economía y Desarrollo de Provincias
- [ ] Generación de oro, puntos de diplomacia y mano de obra (*manpower*) por provincia.
- [ ] Menú de reclutamiento de infantería, caballería y artillería.
- [ ] Construcción de edificios tácticos:
  - Fuertes defensivos para resistir invasiones.
  - Talleres y centros de suministros para acelerar la economía.
- [ ] Simulación de crecimiento poblacional e ingresos calculados en Rust.

---

### ⏳ Fase 5: Diplomacia, IA y Eventos en Lua
- [ ] Acciones diplomáticas completas:
  - Declarar guerra y firmar tratados de paz con cesión de territorios.
  - Pactos de no agresión y alianzas militares.
  - Mejorar o empeorar relaciones bilaterales.
- [ ] Motor de eventos históricos ejecutados mediante scripts de Lua:
  - Tratados limítrofes.
  - Crisis económicas y revueltas populares.
- [ ] Sistema de Modding: Permitir la lectura de archivos `.lua` externos para crear escenarios y campañas personalizadas.

---

### ⏳ Fase 6: Interfaz Definitiva y Optimización APK
- [ ] Panel de estadísticas globales y clasificación de potencias de Latinoamérica.
- [ ] Efectos de sonido tácticos (marcha de ejércitos, clarines de guerra y campanas de paz).
- [ ] Optimización de tamaño y rendimiento del APK para distribución en tiendas de terceros (Uptodown, descarga directa).
