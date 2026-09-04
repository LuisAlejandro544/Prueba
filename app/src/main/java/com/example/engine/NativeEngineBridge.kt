package com.example.engine

import android.util.Log

/**
 * High-performance Native Strategy Engine Bridge.
 * Links Kotlin and Jetpack Compose with the native C++20 engine,
 * raw Lua 5.4.6 runtime, and Rust simulation core.
 */
object NativeEngineBridge {

    private const val TAG = "NativeEngineBridge"
    private var isLoaded = false

    init {
        try {
            System.loadLibrary("native-strategy-engine")
            isLoaded = true
            Log.i(TAG, "Native Strategy Engine loaded successfully!")
        } catch (e: UnsatisfiedLinkError) {
            Log.e(TAG, "Failed to load native-strategy-engine", e)
            isLoaded = false
        }
    }

    fun isNativeEngineAvailable(): Boolean = isLoaded

    external fun getEngineInfo(): String

    external fun runLuaScript(script: String): String

    external fun calculateCombatNative(
        attacker: Long,
        defender: Long,
        bonus: Int
    ): Long

    external fun evaluateAiThreatNative(
        playerArmy: Long,
        neighborArmy: Long,
        relations: Int
    ): Int
}
