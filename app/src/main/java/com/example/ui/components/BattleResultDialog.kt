package com.example.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import com.example.data.model.BattleReport
import com.example.ui.theme.MilitaryGreen
import com.example.ui.theme.StrategyGold
import com.example.ui.theme.StrategySurface
import com.example.ui.theme.StrategySurfaceElevated
import com.example.ui.theme.WarRed

@Composable
fun BattleResultDialog(
    report: BattleReport,
    onDismiss: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp)),
            color = StrategySurface,
            tonalElevation = 16.dp
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Battle header banner
                Text(
                    text = if (report.attackerWon) "⚔️ VICTORIA DEL ATACANTE" else "🛡️ DEFENSA EXITOSA",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = if (report.attackerWon) StrategyGold else MilitaryGreen
                )

                Text(
                    text = "Batalla por ${report.provinceName}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Spacer(modifier = Modifier.height(16.dp))

                // Stats Comparison Table
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    // Attacker column
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(10.dp))
                            .background(StrategySurfaceElevated)
                            .padding(10.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = report.attackerCountryName,
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            color = StrategyGold
                        )
                        Text(text = "Atacante", fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "Tropas: ${formatNumber(report.attackerSoldiers)}",
                            fontSize = 11.sp,
                            color = Color.White
                        )
                        Text(
                            text = "Bajas: -${formatNumber(report.attackerLosses)}",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = WarRed
                        )
                    }

                    Spacer(modifier = Modifier.size(10.dp))

                    // Defender column
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(10.dp))
                            .background(StrategySurfaceElevated)
                            .padding(10.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = report.defenderCountryName,
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            color = MilitaryGreen
                        )
                        Text(text = "Defensor", fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "Tropas: ${formatNumber(report.defenderSoldiers)}",
                            fontSize = 11.sp,
                            color = Color.White
                        )
                        Text(
                            text = "Bajas: -${formatNumber(report.defenderLosses)}",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = WarRed
                        )
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Territorial result note
                if (report.provinceCaptured) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(StrategyGold.copy(alpha = 0.15f))
                            .padding(8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "🚩 ¡${report.provinceName} ha sido conquistada por ${report.attackerCountryName}!",
                            style = MaterialTheme.typography.bodySmall,
                            fontWeight = FontWeight.Bold,
                            color = StrategyGold
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                Button(
                    onClick = onDismiss,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = StrategyGold),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Text(text = "Entendido", color = Color.Black, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

private fun formatNumber(num: Long): String {
    return when {
        num >= 1_000_000 -> String.format("%.1fM", num / 1_000_000.0)
        num >= 1_000 -> String.format("%.1fK", num / 1_000.0)
        else -> num.toString()
    }
}
