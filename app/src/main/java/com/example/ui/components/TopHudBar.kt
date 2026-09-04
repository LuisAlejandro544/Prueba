package com.example.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.FastForward
import androidx.compose.material.icons.filled.Flag
import androidx.compose.material.icons.filled.Layers
import androidx.compose.material.icons.filled.MonetizationOn
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.model.Country
import com.example.data.model.GameSpeed
import com.example.ui.theme.DiplomacyBlue
import com.example.ui.theme.MilitaryGreen
import com.example.ui.theme.StrategyBorder
import com.example.ui.theme.StrategyGold
import com.example.ui.theme.StrategySurface
import com.example.ui.theme.StrategySurfaceElevated

/**
 * HUD Superior en una sola fila panorámica ultra-eficiente para modo horizontal.
 */
@Composable
fun TopHudBar(
    playerCountry: Country?,
    dateString: String,
    gameSpeed: GameSpeed,
    ownedProvincesCount: Int,
    onSpeedChange: (GameSpeed) -> Unit,
    onManualTick: () -> Unit,
    onChangeCountry: () -> Unit,
    onOpenFullMapViewer: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .height(48.dp),
        color = StrategySurface,
        tonalElevation = 6.dp,
        shadowElevation = 8.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            // 1. Country Identifier Pill
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .clip(RoundedCornerShape(6.dp))
                    .background(StrategySurfaceElevated)
                    .border(1.dp, StrategyBorder, RoundedCornerShape(6.dp))
                    .padding(horizontal = 8.dp, vertical = 4.dp)
            ) {
                Text(
                    text = playerCountry?.flagEmoji ?: "🌎",
                    fontSize = 16.sp,
                    modifier = Modifier.padding(end = 5.dp)
                )
                Text(
                    text = playerCountry?.name ?: "Nación",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    color = StrategyGold
                )
                Spacer(modifier = Modifier.width(6.dp))
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(4.dp))
                        .background(playerCountry?.primaryColor ?: Color.Gray)
                        .padding(horizontal = 5.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = "$ownedProvincesCount prov.",
                        fontSize = 10.sp,
                        color = Color.White,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }

            // 2. Resource Badges (Treasury, Manpower, Stability)
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                ResourceBadge(
                    icon = Icons.Default.MonetizationOn,
                    value = "$${formatNumber(playerCountry?.treasury ?: 0)}",
                    color = StrategyGold
                )
                ResourceBadge(
                    icon = Icons.Default.Shield,
                    value = formatNumber(playerCountry?.manpower ?: 0),
                    color = DiplomacyBlue
                )
                ResourceBadge(
                    icon = Icons.Default.Flag,
                    value = "${playerCountry?.stability ?: 80}% Est.",
                    color = MilitaryGreen
                )
            }

            // 3. Date & Game Speed Controls
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Date Display
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(6.dp))
                        .border(1.dp, StrategyBorder, RoundedCornerShape(6.dp))
                        .background(StrategySurfaceElevated)
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = dateString,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFFF1F5F9)
                    )
                }

                // Speed buttons
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier
                        .clip(RoundedCornerShape(16.dp))
                        .background(StrategySurfaceElevated)
                        .border(1.dp, StrategyBorder, RoundedCornerShape(16.dp))
                        .padding(2.dp)
                ) {
                    SpeedButton(
                        icon = Icons.Default.Pause,
                        isSelected = gameSpeed == GameSpeed.PAUSED,
                        onClick = { onSpeedChange(GameSpeed.PAUSED) },
                        contentDescription = "Pausar tiempo"
                    )
                    SpeedButton(
                        icon = Icons.Default.PlayArrow,
                        isSelected = gameSpeed == GameSpeed.NORMAL,
                        onClick = { onSpeedChange(GameSpeed.NORMAL) },
                        contentDescription = "Velocidad normal"
                    )
                    SpeedButton(
                        icon = Icons.Default.FastForward,
                        isSelected = gameSpeed == GameSpeed.FAST || gameSpeed == GameSpeed.VERY_FAST,
                        onClick = {
                            if (gameSpeed == GameSpeed.FAST) onSpeedChange(GameSpeed.VERY_FAST)
                            else onSpeedChange(GameSpeed.FAST)
                        },
                        contentDescription = "Acelerar"
                    )
                    SpeedButton(
                        icon = Icons.Default.SkipNext,
                        isSelected = false,
                        onClick = onManualTick,
                        contentDescription = "+1 Día"
                    )
                }
            }

            // 4. Utility Actions: Full Map Viewer + Switch Country
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                // Button to inspect Blank_province_map.png
                IconButton(
                    onClick = onOpenFullMapViewer,
                    modifier = Modifier.size(34.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Layers,
                        contentDescription = "Ver Mapa Base",
                        tint = Color(0xFF60A5FA),
                        modifier = Modifier.size(18.dp)
                    )
                }

                // Change country
                IconButton(
                    onClick = onChangeCountry,
                    modifier = Modifier.size(34.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Refresh,
                        contentDescription = "Cambiar país",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun ResourceBadge(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    value: String,
    color: Color
) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(StrategySurfaceElevated.copy(alpha = 0.6f))
            .border(1.dp, StrategyBorder, RoundedCornerShape(6.dp))
            .padding(horizontal = 6.dp, vertical = 3.dp)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = color,
            modifier = Modifier.size(14.dp)
        )
        Spacer(modifier = Modifier.width(4.dp))
        Text(
            text = value,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            color = Color.White
        )
    }
}

@Composable
private fun SpeedButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    isSelected: Boolean,
    onClick: () -> Unit,
    contentDescription: String
) {
    Box(
        modifier = Modifier
            .size(24.dp)
            .clip(CircleShape)
            .background(if (isSelected) StrategyGold else Color.Transparent)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = icon,
            contentDescription = contentDescription,
            tint = if (isSelected) Color.Black else Color.White,
            modifier = Modifier.size(14.dp)
        )
    }
}

private fun formatNumber(num: Long): String {
    return when {
        num >= 1_000_000 -> String.format("%.1fM", num / 1_000_000.0)
        num >= 1_000 -> String.format("%.1fK", num / 1_000.0)
        else -> num.toString()
    }
}
