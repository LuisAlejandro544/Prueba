package com.example.data.model

import androidx.compose.ui.graphics.Color

data class Country(
    val id: String,
    val name: String,
    val officialName: String,
    val flagEmoji: String,
    val capitalName: String,
    val region: LatinRegion,
    val primaryColor: Color,
    val secondaryColor: Color,
    val description: String,
    var treasury: Long,
    var manpower: Long,
    var stability: Int = 85, // 0 - 100%
    val isPlayer: Boolean = false,
    val atWarWith: MutableSet<String> = mutableSetOf(),
    val allies: MutableSet<String> = mutableSetOf(),
    val nonAggressionWith: MutableSet<String> = mutableSetOf(),
    val relations: MutableMap<String, Int> = mutableMapOf() // CountryId -> -100 to +100
)

enum class LatinRegion(val label: String) {
    SUDAMERICA("Sudamérica"),
    CENTROAMERICA("Centroamérica"),
    CARIBE("Caribe"),
    NORTEAMERICA("Norteamérica")
}

data class Province(
    val id: String,
    val name: String,
    var ownerCountryId: String,
    val isCapital: Boolean,
    var army: Long,
    var population: Long,
    var economy: Long, // Producción económica
    var fortificationLevel: Int = 0, // 0 to 3
    val centerNormalizedX: Float, // 0.0f - 1.0f on map
    val centerNormalizedY: Float, // 0.0f - 1.0f on map
    val adjacentProvinceIds: List<String>,
    // Relative polygon points (0..100 scale offset from center or global normalized)
    val boundaryPointsNormalized: List<Pair<Float, Float>>
)

data class ArmyMarch(
    val id: String,
    val fromProvinceId: String,
    val toProvinceId: String,
    val ownerCountryId: String,
    val soldiers: Long,
    var progress: Float = 0f, // 0.0 to 1.0
    val speedPerTick: Float = 0.25f // Completes in 4 ticks
)

data class BattleReport(
    val provinceName: String,
    val attackerCountryName: String,
    val defenderCountryName: String,
    val attackerSoldiers: Long,
    val defenderSoldiers: Long,
    val attackerLosses: Long,
    val defenderLosses: Long,
    val attackerWon: Boolean,
    val provinceCaptured: Boolean
)

enum class GameSpeed(val label: String, val intervalMs: Long) {
    PAUSED("Pausa", 0L),
    NORMAL("1x", 1400L),
    FAST("2x", 750L),
    VERY_FAST("3x", 350L)
}

data class GameEventLog(
    val id: Long,
    val timestamp: String,
    val message: String,
    val icon: String,
    val isImportant: Boolean = false
)

enum class GameScreenState {
    COUNTRY_SELECTION,
    PLAYING,
    GAME_OVER
}
