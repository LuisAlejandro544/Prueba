package com.example.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Handshake
import androidx.compose.material.icons.filled.MilitaryTech
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.VolunteerActivism
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import androidx.compose.ui.window.Dialog
import com.example.data.model.Country
import com.example.ui.theme.DiplomacyBlue
import com.example.ui.theme.MilitaryGreen
import com.example.ui.theme.StrategyBorder
import com.example.ui.theme.StrategyGold
import com.example.ui.theme.StrategySurface
import com.example.ui.theme.StrategySurfaceElevated
import com.example.ui.theme.WarRed

@Composable
fun DiplomacyDialog(
    targetCountry: Country,
    playerCountry: Country?,
    onDeclareWar: (String) -> Unit,
    onMakePeace: (String) -> Unit,
    onImproveRelations: (String) -> Unit,
    onSignNonAggression: (String) -> Unit,
    onDismiss: () -> Unit
) {
    val isAtWar = playerCountry?.atWarWith?.contains(targetCountry.id) == true
    val hasNonAggression = playerCountry?.nonAggressionWith?.contains(targetCountry.id) == true
    val relations = playerCountry?.relations?.get(targetCountry.id) ?: 10

    Dialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp)),
            color = StrategySurface,
            tonalElevation = 12.dp
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp)
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(text = targetCountry.flagEmoji, fontSize = 28.sp)
                        Spacer(modifier = Modifier.width(10.dp))
                        Column {
                            Text(
                                text = targetCountry.name,
                                style = MaterialTheme.typography.titleLarge,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Text(
                                text = targetCountry.officialName,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                fontSize = 10.sp
                            )
                        }
                    }

                    IconButton(onClick = onDismiss, modifier = Modifier.size(32.dp)) {
                        Icon(
                            imageVector = Icons.Default.Close,
                            contentDescription = "Cerrar",
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Relations status badge & meter
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(StrategySurfaceElevated)
                        .padding(12.dp)
                ) {
                    Column {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "Estado Diplomático",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )

                            val statusText = when {
                                isAtWar -> "⚔️ GUERRA ABIERTA"
                                hasNonAggression -> "📜 PACTO DE NO AGRESIÓN"
                                else -> "🕊️ PAZ Y NEUTRALIDAD"
                            }
                            val statusColor = when {
                                isAtWar -> WarRed
                                hasNonAggression -> StrategyGold
                                else -> MilitaryGreen
                            }

                            Text(
                                text = statusText,
                                style = MaterialTheme.typography.labelMedium,
                                fontWeight = FontWeight.Bold,
                                color = statusColor
                            )
                        }

                        Spacer(modifier = Modifier.height(8.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = "Opinión hacia ti: $relations / 100",
                                style = MaterialTheme.typography.bodySmall,
                                color = if (relations >= 0) MilitaryGreen else WarRed
                            )
                            Text(
                                text = "Capital: ${targetCountry.capitalName}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Diplomatic Actions list
                Text(
                    text = "ACCIONES DIPLOMÁTICAS",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = StrategyGold
                )

                Spacer(modifier = Modifier.height(8.dp))

                if (isAtWar) {
                    Button(
                        onClick = { onMakePeace(targetCountry.id) },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = MilitaryGreen),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Icon(Icons.Default.VolunteerActivism, contentDescription = null, tint = Color.Black)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Negociar Tratado de Paz", color = Color.Black, fontWeight = FontWeight.Bold)
                    }
                } else {
                    Button(
                        onClick = { onDeclareWar(targetCountry.id) },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = WarRed),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Icon(Icons.Default.MilitaryTech, contentDescription = null, tint = Color.White)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Declarar Guerra Total", color = Color.White, fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Button(
                    onClick = { onImproveRelations(targetCountry.id) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = StrategySurfaceElevated),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Icon(Icons.Default.Handshake, contentDescription = null, tint = DiplomacyBlue)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Mejorar Relaciones (+25) [1,200 💰]", color = Color.White, fontWeight = FontWeight.SemiBold)
                }

                if (!hasNonAggression && !isAtWar) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Button(
                        onClick = { onSignNonAggression(targetCountry.id) },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = StrategySurfaceElevated),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Icon(Icons.Default.Description, contentDescription = null, tint = StrategyGold)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Pacto de No Agresión", color = StrategyGold, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}
