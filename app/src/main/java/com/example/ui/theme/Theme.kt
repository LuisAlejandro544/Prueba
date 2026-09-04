package com.example.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val StrategyColorScheme = darkColorScheme(
    primary = StrategyGold,
    onPrimary = StrategyDarkBg,
    primaryContainer = StrategyGoldContainer,
    onPrimaryContainer = StrategyGold,
    secondary = DiplomacyBlue,
    onSecondary = StrategyDarkBg,
    background = StrategyDarkBg,
    onBackground = StrategyTextPrimary,
    surface = StrategySurface,
    onSurface = StrategyTextPrimary,
    surfaceVariant = StrategySurfaceElevated,
    onSurfaceVariant = StrategyTextSecondary,
    outline = StrategyBorder,
    error = WarRed
)

@Composable
fun MyApplicationTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = StrategyColorScheme,
        typography = Typography,
        content = content
    )
}

