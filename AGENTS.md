# 🤖 Instrucciones para Agentes (AGENTS.md)

Este documento define las reglas de comportamiento, flujo de trabajo y directrices técnicas obligatorias para cualquier agente de IA que trabaje en este repositorio.

---

## 🧭 Flujo de Trabajo del Ciclo de Desarrollo

Cada intervención debe alinearse con el rol correspondiente del ciclo:

1. **El Arquitecto (Planificación y Diseño):**
   - Antes de escribir código para una nueva mecánica mayor, define el modelo de datos, la estructura de archivos y el flujo de ejecución.
2. **El Constructor (Implementación):**
   - Código modular, limpio, tipado y listo para producción. No usar ejemplos incompletos o simplificados.
3. **El Detective (Resolución de Errores):**
   - Utilizar razonamiento paso a paso: hipótesis ordenada por probabilidad, análisis línea por línea, causa raíz y corrección enfocada.
4. **El Crítico (Revisión de Código):**
   - Evaluar seguridad, rendimiento en dispositivos móviles (evitar sobrecargas de GC en bucles de renderizado) y mantenibilidad.
5. **El Optimizador (Rendimiento y Refactor):**
   - Priorizar algoritmos eficientes en el motor nativo (Rust/C++) para operaciones matemáticas pesadas (ej: combate de ejércitos, pathfinding).
6. **El Escudo (Pruebas y Verificación):**
   - Validar que cada cambio compile correctamente mediante la herramienta de compilación antes de dar la tarea por concluida.
7. **El Narrador (Documentación Técnica):**
   - Mantener actualizados los documentos `README.md`, `ROADMAP.md`, `STRUCTURE.md` y `AI_CONTEXT.md`. Toda documentación y mensajes deben estar en español.

---

## 🛑 Reglas Críticas e Inquebrantables

1. **Compilación Nativa Real:**
   - Si se utiliza C++, Rust o Lua, **deben compilarse realmente** a través del flujo de Gradle (`buildRustCore`, `externalNativeBuild` con CMake). Está estrictamente prohibido simular funciones o saltarse la compilación nativa sustituyéndola con código simulado (*mock fallback*).
2. **Uso de Dependencias Reales:**
   - El usuario prefiere herramientas y librerías completas y funcionales por sobre soluciones improvisadas sin dependencias. El peso final del APK no es una restricción limitante.
3. **Representación Visual del Mapa:**
   - **Espacio de Pantalla Obligatorio:** Las etiquetas de texto (nombres de provincias, cantidades de tropas) deben dibujarse siempre en coordenadas de pantalla fijas (`screen-space`) para que no se agranden desproporcionadamente al aplicar zoom táctico.
4. **Respeto a la Propiedad Intelectual:**
   - Nunca nombrar archivos o identificadores con marcas comerciales protegidas por derechos de autor que puedan poner al usuario en riesgo legal.
5. **Mensajes de Commit:**
   - Si existe o se genera un archivo `commit_message.txt`, su contenido debe estar redactado en español y no debe ser modificado a menos que el usuario lo solicite explícitamente.
6. **Entorno del Usuario:**
   - Tener siempre presente que el usuario opera desde un teléfono móvil y que el APK final será distribuido en tiendas como Uptodown o instalación directa.
