# 🧠 AI Context & Domain Knowledge

Este archivo proporciona contexto técnico para cualquier modelo de Inteligencia Artificial que colabore en este proyecto.

---

## 🎯 Resumen del Proyecto

- **Género:** Gran Estrategia Geopolítica en Tiempo Real (RTS) para Android.
- **Escenario Actual:** Latinoamérica (13 naciones jugables: México, Colombia, Argentina, Brasil, Perú, Chile, Venezuela, Bolivia, Ecuador, Paraguay, Uruguay, Centroamérica y el Caribe).
- **Inspiración:** Profundidad territorial y táctica de *Age of History* y los juegos de gran estrategia clásica.
- **Orientación:** Fija en modo horizontal (*Landscape*).

---

## 🏗️ Arquitectura Híbrida

El juego no depende exclusivamente de la máquina virtual de Java/Android. Se divide deliberadamente en cuatro capas:

1. **Capa Visual & UX (Kotlin + Jetpack Compose):**
   - Maneja el ciclo de vida de las vistas, gestos táctiles (*pinch-to-zoom*, *pan*, *tap*), y el renderizado del Canvas.
   - **Regla de Oro de Renderizado:** Las etiquetas de ejércitos y los nombres de provincias se deben dibujar en **espacio de pantalla (*screen-space*)**, nunca sujetos a la matriz de transformación del zoom, para evitar que aumenten desproporcionadamente de tamaño y tapen el mapa.
   - El sistema de coordenadas del mapa es normalizado de `(0.0, 0.0)` a `(1.0, 1.0)` relativo a las dimensiones originales del mapa de provincias (5632 x 2048).

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

---

## 📱 Perfil del Usuario y Restricciones Técnicas

- **Dispositivo del Usuario:** El usuario opera principalmente desde un dispositivo móvil (teléfono).
- **Canal de Distribución:** El APK se distribuye en tiendas alternativas como **Uptodown** o descarga directa de APK.
- **Compilación Nativa Obligatoria:** Cuando se integre código en C++, Rust o Lua, las herramientas de Gradle **deben compilar las librerías nativas reales**. Está estrictamente prohibido simular o sustituir librerías nativas con código alternativo simulado (*fallback mock*) cuando el usuario solicita una tecnología específica.
- **Propiedad Intelectual:** No utilizar nombres de marcas protegidas por derechos de autor que puedan poner en riesgo al usuario.

---

## 🛠️ Herramientas de Compilación Utilizadas

- **Android NDK:** Versión `26.1.10909125` con Clang 17.
- **CMake:** Versión `3.22.1`.
- **Rust Toolchain:** Compilador `rustc` y `cargo` con targets `aarch64-linux-android` (dispositivos físicos) y `x86_64-linux-android` (emuladores).
- **Compilación Automatizada:** Tarea `buildRustCore` en `app/build.gradle.kts` vinculada a `preBuild`.
- **Integración Continua:**
  - `.github/workflows/build-debug-apk.yml`: Compilación manual sin caché para APK Debug con generación de firma local en el runner.
  - `.github/workflows/override-commit-message.yml`: Sincronización automática de mensajes de commit leyendo `commit_message.txt`.
