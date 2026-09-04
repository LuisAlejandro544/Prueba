#include <jni.h>
#include <string>
#include <sstream>
#include <android/log.h>

#define LOG_TAG "StrategyNativeEngine"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Raw Official Lua 5.4.6 ANSI C Engine
extern "C" {
#include "lua/lua.h"
#include "lua/lauxlib.h"
#include "lua/lualib.h"
}

// Rust Core Simulation Engine (FFI C Linkage)
extern "C" {
    int rust_strategy_core_version();
    bool rust_strategy_core_init();
    int64_t rust_strategy_core_calculate_combat(int64_t attacker, int64_t defender, int32_t bonus);
    int32_t rust_strategy_core_evaluate_ai_threat(int64_t player_army, int64_t neighbor_army, int32_t relations);
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_engine_NativeEngineBridge_getEngineInfo(
        JNIEnv* env,
        jobject /* this */) {
    std::ostringstream ss;
    ss << "Native Engine: C++20 + Lua " << LUA_RELEASE 
       << " + Rust Core v" << rust_strategy_core_version();
    return env->NewStringUTF(ss.str().c_str());
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_engine_NativeEngineBridge_runLuaScript(
        JNIEnv* env,
        jobject /* this */,
        jstring script) {
    const char* scriptChars = env->GetStringUTFChars(script, nullptr);
    if (!scriptChars) {
        return env->NewStringUTF("Error: null script passed");
    }

    // Initialize clean official Lua 5.4 state
    lua_State* L = luaL_newstate();
    if (!L) {
        env->ReleaseStringUTFChars(script, scriptChars);
        return env->NewStringUTF("Error: failed to initialize Lua state");
    }

    // Open standard Lua libraries
    luaL_openlibs(L);

    // Register custom native helper into Lua environment
    lua_pushcfunction(L, [](lua_State* state) -> int {
        int n = lua_gettop(state);
        std::string msg;
        for (int i = 1; i <= n; i++) {
            if (i > 1) msg += "\t";
            if (lua_isstring(state, i)) {
                msg += lua_tostring(state, i);
            }
        }
        LOGI("[Lua Log] %s", msg.c_str());
        return 0;
    });
    lua_setglobal(L, "native_print");

    std::string resultStr;
    int status = luaL_dostring(L, scriptChars);
    if (status != LUA_OK) {
        const char* err = lua_tostring(L, -1);
        resultStr = std::string("Lua Error: ") + (err ? err : "Unknown error");
        LOGE("%s", resultStr.c_str());
    } else {
        // If script left a return value on top of stack
        if (lua_gettop(L) > 0 && lua_isstring(L, -1)) {
            resultStr = lua_tostring(L, -1);
        } else {
            resultStr = "Lua OK: Execution successful";
        }
    }

    lua_close(L);
    env->ReleaseStringUTFChars(script, scriptChars);
    return env->NewStringUTF(resultStr.c_str());
}

extern "C" JNIEXPORT jlong JNICALL
Java_com_example_engine_NativeEngineBridge_calculateCombatNative(
        JNIEnv* /* env */,
        jobject /* this */,
        jlong attacker,
        jlong defender,
        jint bonus) {
    return rust_strategy_core_calculate_combat(attacker, defender, bonus);
}

extern "C" JNIEXPORT jint JNICALL
Java_com_example_engine_NativeEngineBridge_evaluateAiThreatNative(
        JNIEnv* /* env */,
        jobject /* this */,
        jlong playerArmy,
        jlong neighborArmy,
        jint relations) {
    return rust_strategy_core_evaluate_ai_threat(playerArmy, neighborArmy, relations);
}
