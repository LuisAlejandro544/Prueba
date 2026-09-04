# Gran Estrategia Latinoamérica (RTS Mini-Engine)

Juego de gran estrategia geopolítica en tiempo real para Android ambientado en Latinoamérica, inspirado en la profundidad territorial y militar de los grandes juegos de estrategia histórica.

El proyecto está diseñado bajo una **arquitectura híbrida de alto rendimiento**, combinando una interfaz reactiva en Jetpack Compose con un mini motor nativo integrado en **C++20**, **Rust** y **Lua 5.4.6 original (puro)**.

---

## 🏛️ Arquitectura del Sistema

| Capa | Tecnología | Propósito |
| :--- | :--- | :--- |
| **Interfaz & UX** | Kotlin + Jetpack Compose | Menús de selección de naciones, HUD superior, controles táctiles y visor de mapa. |
| **Puente JNI & Enlace** | C++20 (NDK Clang) | Gestión del ciclo de vida nativo, comunicación bidireccional y orquestación. |
| **Simulador Militar & IA** | Rust (`strategy_core`) | Cálculos sin pausas de Garbage Collector: bajas de combate, evaluación de amenazas e ingresos. |
| **Lógica de Eventos & Mods** | Lua 5.4.6 (ANSI C puro) | Motor de eventos históricos, decisiones diplomáticas y capacidad de modding sin wrappers. |

---

## 🚀 Características Principales

- **Selección de Países de Latinoamérica:** México, Colombia, Argentina, Brasil, Perú, Chile, Venezuela, Bolivia, Ecuador, Paraguay, Uruguay, Centroamérica y el Caribe.
- **Mapa Político y Territorial Preciso:** Provincias coloreadas con sus tonos patrios correspondientes, fronteras tácticas y visualizador de mapa original.
- **Etiquetas en Espacio de Pantalla:** Indicadores de tropas y nombres que no obstruyen la visualización al hacer zoom táctico.
- **Motor Nativo Multilenguaje:**
  - Código C++ listo para renderizado gráfico avanzado (Vulkan / OpenGL ES).
  - Núcleo Rust compilado en bibliotecas estáticas nativas (`.a`) para `arm64-v8a` y `x86_64`.
  - Código fuente completo de Lua 5.4 oficial embebido en el proyecto para máxima libertad y extensibilidad.

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

## 🤖 Integración Continua (GitHub Actions)

El repositorio incluye dos flujos de trabajo automatizados en `.github/workflows/`:

1. **`build-debug-apk.yml` (Compilación Manual de APK Debug):**
   - Se activa **únicamente de forma manual** (`workflow_dispatch`) desde la pestaña *Actions* de GitHub.
   - Descarga todo el código, instala el NDK 26, CMake 3.22, el compilador de Rust con soporte para arquitecturas `arm64-v8a` y `x86_64`, y las fuentes oficiales de Lua.
   - Genera dinámicamente la firma de depuración (`debug.keystore`) dentro del runner.
   - Compila el APK Debug **sin caché** y lo publica como artefacto descargable (`app-debug.apk`) con 30 días de retención.

2. **`override-commit-message.yml` (Gestión de Mensajes de Commit):**
   - Se activa automáticamente con cada `push` a las ramas `main` o `master`.
   - Lee el contenido de `commit_message.txt` y, si difiere del último mensaje de commit, reescribe el commit automáticamente para mantener el historial estandarizado y en español.

---

## 📂 Organización de Fuentes Nativas

- `app/src/main/rust/`: Código fuente de Rust (`Cargo.toml`, `src/lib.rs` y script de compilación `build_rust.sh`).
- `app/src/main/cpp/lua/`: Código fuente original de Lua 5.4.6 en ANSI C puro.
- `app/src/main/cpp/`: Motor C++ y puente JNI (`strategy_engine.cpp`, `CMakeLists.txt`).
- `app/src/main/java/com/example/engine/`: Clase puente Kotlin (`NativeEngineBridge.kt`).

---

## 📜 Licencia y Distribución
Desarrollado para distribución independiente en plataformas móviles Android.
