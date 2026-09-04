# 📁 Estructura del Proyecto (Architecture & Folder Tree)

Detalle de la jerarquía de directorios, módulos y componentes del juego y su mini motor.

---

## 🌳 Árbol General de Archivos

```text
├── .github/                           # Automatización y CI/CD
│   └── workflows/
│       ├── build-debug-apk.yml        # Flujo manual de compilación de APK Debug
│       └── override-commit-message.yml # Flujo de reescritura de commits
├── .gitignore                         # Reglas de exclusión para Git (Java, C++, Rust, Lua)
├── commit_message.txt                 # Mensaje canónico de commit en español
├── README.md                          # Visión general y guía rápida
├── ROADMAP.md                         # Fases y hoja de ruta de desarrollo
├── STRUCTURE.md                       # Estructura de archivos y módulos
├── AI_CONTEXT.md                      # Contexto técnico para asistentes de IA
├── AGENTS.md                          # Instrucciones y reglas para agentes
├── gradlew                            # Script de Gradle Wrapper
├── build.gradle.kts                   # Configuración Gradle raíz del proyecto
├── settings.gradle.kts                # Configuración de repositorios y módulos
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
            ├── assets/                # Recursos de mapa de alta resolución
            │   ├── blank_province_map.png      # Mapa original en blanco (5632x2048)
            │   └── political_province_map.png  # Mapa rasterizado con división política
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
            │   │   ├── LatamCountries.kt  # Definiciones de 13 países de Latinoamérica
            │   │   ├── ProvinceData.kt    # Geometría normalizada de provincias
            │   │   └── GameModels.kt      # Estados de partida, ejércitos y recursos
            │   │
            │   ├── engine/            # Integración nativa con Kotlin
            │   │   └── NativeEngineBridge.kt # Interfaz JNI para C++, Rust y Lua
            │   │
            │   ├── ui/                # Capa visual (Jetpack Compose)
            │   │   ├── screens/
            │   │   │   ├── CountrySelectionScreen.kt # Pantalla de selección de nación
            │   │   │   └── GameScreen.kt             # Pantalla principal de juego
            │   │   ├── map/
            │   │   │   └── StrategyMapCanvas.kt      # Canvas interactivo del mapa táctico
            │   │   ├── components/
            │   │   │   ├── TopHudBar.kt              # Barra de recursos y fecha
            │   │   │   ├── BottomCommandPanel.kt     # Panel de órdenes y reclutamiento
            │   │   │   └── FullMapViewerDialog.kt    # Diálogo para examinar el mapa completo
            │   │   └── theme/
            │   │       ├── Color.kt                  # Paleta táctica y colores patrios
            │   │       ├── Theme.kt                  # Tema Material Design 3
            │   │       └── Type.kt                   # Tipografía militar y estratégica
            │   │
            │   └── viewmodel/
            │       └── GameViewModel.kt              # Estado reactivo y lógica de juego
            │
            └── res/                   # Recursos visuales de Android
                ├── values/
                │   ├── strings.xml    # Cadenas de texto
                │   └── colors.xml     # Colores del sistema
                └── mipmap-*/          # Iconos adaptativos de la aplicación
```

---

## ⚙️ Flujo de Compilación y Enlace Nativo

1. **Paso 1 (Rust):** Antes de iniciar `preBuild`, Gradle ejecuta `build_rust.sh`, que usa el compilador Clang del NDK para generar las librerías estáticas `libstrategy_core.a` para `arm64-v8a` y `x86_64`.
2. **Paso 2 (CMake & C++):** CMake compila todos los archivos fuente de **Lua 5.4.6 en bruto** junto con `strategy_engine.cpp`.
3. **Paso 3 (Enlace JNI):** CMake enlaza `libstrategy_core.a`, el runtime de Lua y las librerías de Android (`log`, `m`) en un único binario compartido: `libnative-strategy-engine.so`.
4. **Paso 4 (Kotlin):** `NativeEngineBridge` carga la librería en tiempo de ejecución y expone los métodos nativos a los ViewModels y pantallas de Jetpack Compose.
