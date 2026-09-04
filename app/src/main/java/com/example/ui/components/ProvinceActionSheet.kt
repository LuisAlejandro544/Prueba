package com.example.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Castle
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Forward
import androidx.compose.material.icons.filled.Handshake
import androidx.compose.material.icons.filled.MonetizationOn
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.model.Country
import com.example.data.model.Province
import com.example.ui.theme.DiplomacyBlue
import com.example.ui.theme.EconomyAmber
import com.example.ui.theme.MilitaryGreen
import com.example.ui.theme.StrategyBorder
import com.example.ui.theme.StrategyDarkBg
import com.example.ui.theme.StrategyGold
import com.example.ui.theme.StrategyGoldContainer
import com.example.ui.theme.StrategySurface
import com.example.ui.theme.StrategySurfaceElevated
import com.example.ui.theme.WarRed
import kotlin.math.max
import kotlin.math.min

enum class ActionTab {
    OVERVIEW,
    RECRUIT,
    MOVE
}

@Composable
fun ProvinceActionSheet(
    province: Province,
    allProvinces: List<Province>,
    allCountries: List<Country>,
    playerCountry: Country?,
    onRecruit: (Long) -> Unit,
    onInvestEconomy: () -> Unit,
    onBuildFortification: () -> Unit,
    onOrderMovement: (toProvinceId: String, amount: Long) -> Unit,
    onOpenDiplomacy: (countryId: String) -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier
) {
    val ownerCountry = allCountries.find { it.id == province.ownerCountryId }
    val isPlayerOwned = province.ownerCountryId == playerCountry?.id

    var selectedTab by remember(province.id) { mutableStateOf(ActionTab.OVERVIEW) }
    var recruitAmount by remember(province.id) { mutableFloatStateOf(5000f) }

    // Troop movement state
    var selectedTargetProvinceId by remember(province.id) { mutableStateOf<String?>(null) }
    var moveFraction by remember(province.id) { mutableFloatStateOf(0.5f) }

    val scrollState = rememberScrollState()

    Surface(
        modifier = modifier
            .widthIn(max = 370.dp)
            .clip(RoundedCornerShape(16.dp))
            .border(1.dp, StrategyBorder, RoundedCornerShape(16.dp)),
        color = StrategySurface,
        shadowElevation = 16.dp,
        tonalElevation = 8.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(scrollState)
                .padding(14.dp)
        ) {
            // Header: Province name, capital star, close button
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = ownerCountry?.flagEmoji ?: "🚩",
                        fontSize = 22.sp,
                        modifier = Modifier.padding(end = 8.dp)
                    )
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = province.name,
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            if (province.isCapital) {
                                Spacer(modifier = Modifier.width(6.dp))
                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(4.dp))
                                        .background(StrategyGold.copy(alpha = 0.2f))
                                        .padding(horizontal = 6.dp, vertical = 2.dp)
                                ) {
                                    Text(
                                        text = "CAPITAL",
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = StrategyGold
                                    )
                                }
                            }
                        }
                        Text(
                            text = "Soberanía: ${ownerCountry?.name ?: ""}",
                            style = MaterialTheme.typography.labelSmall,
                            color = if (isPlayerOwned) MilitaryGreen else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                IconButton(
                    onClick = onClose,
                    modifier = Modifier.size(32.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Cerrar",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Province Stats Row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(10.dp))
                    .background(StrategySurfaceElevated)
                    .padding(8.dp),
                horizontalArrangement = Arrangement.SpaceAround,
                verticalAlignment = Alignment.CenterVertically
            ) {
                StatItem(
                    icon = Icons.Default.Security,
                    label = "Tropas",
                    value = formatTroopNumber(province.army),
                    color = if (isPlayerOwned) MilitaryGreen else WarRed
                )
                StatItem(
                    icon = Icons.Default.People,
                    label = "Población",
                    value = formatTroopNumber(province.population),
                    color = DiplomacyBlue
                )
                StatItem(
                    icon = Icons.Default.TrendingUp,
                    label = "Economía",
                    value = "${province.economy}",
                    color = EconomyAmber
                )
                StatItem(
                    icon = Icons.Default.Castle,
                    label = "Fuerte",
                    value = "Nv. ${province.fortificationLevel}",
                    color = StrategyGold
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            if (isPlayerOwned) {
                // Own Territory Action Tabs
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(StrategySurfaceElevated)
                        .padding(3.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    TabButton(
                        text = "Acciones",
                        isSelected = selectedTab == ActionTab.OVERVIEW,
                        onClick = { selectedTab = ActionTab.OVERVIEW },
                        modifier = Modifier.weight(1f)
                    )
                    TabButton(
                        text = "Reclutar",
                        isSelected = selectedTab == ActionTab.RECRUIT,
                        onClick = { selectedTab = ActionTab.RECRUIT },
                        modifier = Modifier.weight(1f)
                    )
                    TabButton(
                        text = "Mover Ejército",
                        isSelected = selectedTab == ActionTab.MOVE,
                        onClick = { selectedTab = ActionTab.MOVE },
                        modifier = Modifier.weight(1f)
                    )
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Tab Content
                when (selectedTab) {
                    ActionTab.OVERVIEW -> {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(
                                onClick = onInvestEconomy,
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = StrategySurfaceElevated),
                                shape = RoundedCornerShape(10.dp)
                            ) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Icon(
                                        imageVector = Icons.Default.MonetizationOn,
                                        contentDescription = "Invertir",
                                        tint = EconomyAmber,
                                        modifier = Modifier.size(18.dp)
                                    )
                                    Text("Desarrollar (+15)", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                    Text("Coste: 2,500 💰", fontSize = 9.sp, color = StrategyGold)
                                }
                            }

                            Button(
                                onClick = onBuildFortification,
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = StrategySurfaceElevated),
                                shape = RoundedCornerShape(10.dp)
                            ) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Icon(
                                        imageVector = Icons.Default.Castle,
                                        contentDescription = "Fortificar",
                                        tint = StrategyGold,
                                        modifier = Modifier.size(18.dp)
                                    )
                                    Text("Fortificar (+25% Def)", fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                    Text("Coste: 4,000 💰", fontSize = 9.sp, color = StrategyGold)
                                }
                            }
                        }
                    }

                    ActionTab.RECRUIT -> {
                        val maxAffordable = min(
                            (playerCountry?.treasury ?: 0) / 2L,
                            playerCountry?.manpower ?: 0
                        ).coerceAtLeast(0L)

                        Column(modifier = Modifier.fillMaxWidth()) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "Reclutas a entrenar: ${formatTroopNumber(recruitAmount.toLong())}",
                                    style = MaterialTheme.typography.bodySmall,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                                Text(
                                    text = "Coste: ${(recruitAmount * 2).toLong()} 💰",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = StrategyGold
                                )
                            }

                            Slider(
                                value = recruitAmount,
                                onValueChange = { recruitAmount = it },
                                valueRange = 1000f..max(1000f, maxAffordable.toFloat()),
                                steps = 9,
                                colors = SliderDefaults.colors(
                                    thumbColor = StrategyGold,
                                    activeTrackColor = StrategyGold,
                                    inactiveTrackColor = StrategyBorder
                                )
                            )

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                QuickAmountChip("+2K") { recruitAmount = min(recruitAmount + 2000f, maxAffordable.toFloat()) }
                                QuickAmountChip("+5K") { recruitAmount = min(recruitAmount + 5000f, maxAffordable.toFloat()) }
                                QuickAmountChip("+10K") { recruitAmount = min(recruitAmount + 10000f, maxAffordable.toFloat()) }
                                QuickAmountChip("Máx") { recruitAmount = max(1000f, maxAffordable.toFloat()) }
                            }

                            Spacer(modifier = Modifier.height(8.dp))

                            Button(
                                onClick = { onRecruit(recruitAmount.toLong()) },
                                modifier = Modifier.fillMaxWidth(),
                                enabled = maxAffordable >= 1000L,
                                colors = ButtonDefaults.buttonColors(containerColor = MilitaryGreen),
                                shape = RoundedCornerShape(10.dp)
                            ) {
                                Text(
                                    text = "Reclutar ${formatTroopNumber(recruitAmount.toLong())} Soldados",
                                    fontWeight = FontWeight.Bold,
                                    color = Color.Black
                                )
                            }
                        }
                    }

                    ActionTab.MOVE -> {
                        val availableToMove = max(0L, province.army - 1000L)
                        val adjacentProvinces = allProvinces.filter { province.adjacentProvinceIds.contains(it.id) }

                        Column(modifier = Modifier.fillMaxWidth()) {
                            Text(
                                text = "Selecciona destino limítrofe:",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )

                            Spacer(modifier = Modifier.height(6.dp))

                            LazyRow(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                items(adjacentProvinces) { adjProv ->
                                    val isTarget = selectedTargetProvinceId == adjProv.id
                                    val adjOwner = allCountries.find { it.id == adjProv.ownerCountryId }
                                    val isEnemy = adjProv.ownerCountryId != playerCountry?.id

                                    Box(
                                        modifier = Modifier
                                            .clip(RoundedCornerShape(8.dp))
                                            .background(if (isTarget) StrategyGoldContainer else StrategySurfaceElevated)
                                            .border(
                                                width = if (isTarget) 1.5.dp else 0.5.dp,
                                                color = if (isTarget) StrategyGold else StrategyBorder,
                                                shape = RoundedCornerShape(8.dp)
                                            )
                                            .clickable { selectedTargetProvinceId = adjProv.id }
                                            .padding(horizontal = 10.dp, vertical = 8.dp)
                                    ) {
                                        Column {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                Text(adjOwner?.flagEmoji ?: "🚩", fontSize = 14.sp)
                                                Spacer(modifier = Modifier.width(4.dp))
                                                Text(
                                                    text = adjProv.name,
                                                    style = MaterialTheme.typography.labelSmall,
                                                    fontWeight = FontWeight.Bold,
                                                    color = if (isEnemy) WarRed else Color.White
                                                )
                                            }
                                            Text(
                                                text = if (isEnemy) "⚔️ ${formatTroopNumber(adjProv.army)}"
                                                else "🛡️ ${formatTroopNumber(adjProv.army)}",
                                                fontSize = 10.sp,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant
                                            )
                                        }
                                    }
                                }
                            }

                            Spacer(modifier = Modifier.height(8.dp))

                            // Troop amount slider
                            val troopsToSend = (availableToMove * moveFraction).toLong()
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = "Tropas a marchar: ${formatTroopNumber(troopsToSend)}",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                                Text(
                                    text = "${(moveFraction * 100).toInt()}% del ejército",
                                    fontSize = 11.sp,
                                    color = StrategyGold
                                )
                            }

                            Slider(
                                value = moveFraction,
                                onValueChange = { moveFraction = it },
                                valueRange = 0.1f..1.0f,
                                colors = SliderDefaults.colors(
                                    thumbColor = StrategyGold,
                                    activeTrackColor = StrategyGold
                                )
                            )

                            Button(
                                onClick = {
                                    val targetId = selectedTargetProvinceId
                                    if (targetId != null && troopsToSend > 0) {
                                        onOrderMovement(targetId, troopsToSend)
                                    }
                                },
                                modifier = Modifier.fillMaxWidth(),
                                enabled = selectedTargetProvinceId != null && troopsToSend >= 1000L,
                                colors = ButtonDefaults.buttonColors(containerColor = StrategyGold),
                                shape = RoundedCornerShape(10.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Forward,
                                    contentDescription = "Marchar",
                                    tint = Color.Black,
                                    modifier = Modifier.size(16.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = "Desplegar Tropas",
                                    color = Color.Black,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    }
                }
            } else {
                // Foreign Territory: Diplomacy or declare war
                val isAtWar = playerCountry?.atWarWith?.contains(province.ownerCountryId) == true
                Column(modifier = Modifier.fillMaxWidth()) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(10.dp))
                            .background(if (isAtWar) WarRed.copy(alpha = 0.15f) else DiplomacyBlue.copy(alpha = 0.15f))
                            .border(
                                1.dp,
                                if (isAtWar) WarRed else DiplomacyBlue,
                                RoundedCornerShape(10.dp)
                            )
                            .padding(12.dp)
                    ) {
                        Column {
                            Text(
                                text = if (isAtWar) "⚔️ ESTADO DE GUERRA ACTIVO" else "🕊️ ESTADO DE PAZ",
                                style = MaterialTheme.typography.labelMedium,
                                fontWeight = FontWeight.Bold,
                                color = if (isAtWar) WarRed else DiplomacyBlue
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Este territorio pertenece a ${ownerCountry?.officialName}. Puedes entablar relaciones diplomáticas o enviar tus tropas.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    Button(
                        onClick = { onOpenDiplomacy(province.ownerCountryId) },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (isAtWar) WarRed else DiplomacyBlue
                        ),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Handshake,
                            contentDescription = "Diplomacia",
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Diplomacia con ${ownerCountry?.name}",
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun StatItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    value: String,
    color: Color
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = color,
            modifier = Modifier.size(16.dp)
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = value,
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onSurface
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            fontSize = 9.sp
        )
    }
}

@Composable
private fun TabButton(
    text: String,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(if (isSelected) StrategyGold else Color.Transparent)
            .clickable(onClick = onClick)
            .padding(vertical = 6.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = if (isSelected) Color.Black else MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun QuickAmountChip(
    text: String,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(StrategySurfaceElevated)
            .clickable(onClick = onClick)
            .padding(horizontal = 10.dp, vertical = 4.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            fontSize = 11.sp,
            fontWeight = FontWeight.SemiBold,
            color = StrategyGold
        )
    }
}

private fun formatTroopNumber(count: Long): String {
    return when {
        count >= 1_000_000 -> String.format("%.1fM", count / 1_000_000.0)
        count >= 1_000 -> String.format("%.1fK", count / 1_000.0)
        else -> count.toString()
    }
}
