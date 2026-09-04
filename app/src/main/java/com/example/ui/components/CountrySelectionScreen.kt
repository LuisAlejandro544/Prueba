package com.example.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Flag
import androidx.compose.material.icons.filled.Layers
import androidx.compose.material.icons.filled.MonetizationOn
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Public
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Security
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.model.Country
import com.example.data.model.LatinRegion
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

@Composable
fun CountrySelectionScreen(
    countries: List<Country>,
    provinces: List<Province>,
    onCountrySelected: (String) -> Unit,
    onOpenFullMapViewer: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    var selectedCountryId by remember { mutableStateOf(countries.firstOrNull()?.id ?: "MX") }
    var selectedRegionFilter by remember { mutableStateOf<LatinRegion?>(null) }
    var searchQuery by remember { mutableStateOf("") }

    val filteredCountries = remember(countries, selectedRegionFilter, searchQuery) {
        countries.filter { country ->
            val matchesRegion = selectedRegionFilter == null || country.region == selectedRegionFilter
            val matchesSearch = searchQuery.isBlank() ||
                    country.name.contains(searchQuery, ignoreCase = true) ||
                    country.capitalName.contains(searchQuery, ignoreCase = true)
            matchesRegion && matchesSearch
        }
    }

    val selectedCountry = countries.find { it.id == selectedCountryId } ?: countries.firstOrNull()
    val startingProvinces = provinces.filter { it.ownerCountryId == selectedCountry?.id }
    val initialTroops = startingProvinces.sumOf { it.army }
    val initialPop = startingProvinces.sumOf { it.population }

    Surface(
        modifier = modifier
            .fillMaxSize()
            .background(StrategyDarkBg),
        color = StrategyDarkBg
    ) {
        // Landscape Split Screen Layout
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp)
        ) {
            // LEFT COLUMN (42%): Countries Catalog & Filter
            Column(
                modifier = Modifier
                    .weight(0.42f)
                    .fillMaxHeight()
                    .padding(end = 8.dp)
            ) {
                // Header Bar
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(34.dp)
                            .clip(RoundedCornerShape(8.dp))
                            .background(StrategyGoldContainer),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.Public,
                            contentDescription = null,
                            tint = StrategyGold,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column {
                        Text(
                            text = "ESTRATEGIA LATINOAMÉRICA",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Black,
                            letterSpacing = 0.8.sp,
                            color = StrategyGold
                        )
                        Text(
                            text = "Elige tu nación para gobernar",
                            style = MaterialTheme.typography.bodySmall,
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Search Box
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    placeholder = { Text("Buscar país o capital...", fontSize = 12.sp) },
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Default.Search,
                            contentDescription = "Buscar",
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.size(16.dp)
                        )
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(46.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = StrategyGold,
                        unfocusedBorderColor = StrategyBorder,
                        focusedContainerColor = StrategySurface,
                        unfocusedContainerColor = StrategySurface
                    ),
                    shape = RoundedCornerShape(8.dp),
                    singleLine = true
                )

                Spacer(modifier = Modifier.height(6.dp))

                // Region Filter Chips
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    contentPadding = PaddingValues(vertical = 2.dp)
                ) {
                    item {
                        FilterChip(
                            selected = selectedRegionFilter == null,
                            onClick = { selectedRegionFilter = null },
                            label = { Text("Todos (${countries.size})", fontSize = 11.sp) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = StrategyGold.copy(alpha = 0.25f),
                                selectedLabelColor = StrategyGold
                            )
                        )
                    }
                    items(LatinRegion.values()) { region ->
                        val count = countries.count { it.region == region }
                        FilterChip(
                            selected = selectedRegionFilter == region,
                            onClick = { selectedRegionFilter = region },
                            label = { Text("${region.label} ($count)", fontSize = 11.sp) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = StrategyGold.copy(alpha = 0.25f),
                                selectedLabelColor = StrategyGold
                            )
                        )
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))

                // Scrollable List of Latin American Countries
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    items(filteredCountries, key = { it.id }) { country ->
                        val isSelected = country.id == selectedCountryId
                        CountryListItemCompact(
                            country = country,
                            isSelected = isSelected,
                            provincesCount = provinces.count { it.ownerCountryId == country.id },
                            onClick = { selectedCountryId = country.id }
                        )
                    }
                }
            }

            // RIGHT COLUMN (58%): Selected Country Dossier & Action
            selectedCountry?.let { country ->
                Surface(
                    modifier = Modifier
                        .weight(0.58f)
                        .fillMaxHeight()
                        .clip(RoundedCornerShape(12.dp))
                        .border(1.dp, StrategyBorder, RoundedCornerShape(12.dp)),
                    color = StrategySurface
                ) {
                    val rightScrollState = rememberScrollState()

                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .verticalScroll(rightScrollState)
                            .padding(14.dp)
                    ) {
                        // Title Header
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = country.flagEmoji,
                                    fontSize = 32.sp,
                                    modifier = Modifier.padding(end = 10.dp)
                                )
                                Column {
                                    Text(
                                        text = country.name,
                                        style = MaterialTheme.typography.titleLarge,
                                        fontWeight = FontWeight.Bold,
                                        color = Color.White
                                    )
                                    Text(
                                        text = country.officialName,
                                        fontSize = 11.sp,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                }
                            }

                            // Region badge
                            Box(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(StrategySurfaceElevated)
                                    .border(1.dp, StrategyBorder, RoundedCornerShape(6.dp))
                                    .padding(horizontal = 8.dp, vertical = 4.dp)
                            ) {
                                Text(
                                    text = country.region.label,
                                    fontSize = 11.sp,
                                    color = StrategyGold,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        // Stats Grid in Landscape
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            StatBox(
                                icon = Icons.Default.MonetizationOn,
                                iconTint = EconomyAmber,
                                label = "Tesoro",
                                value = "$${country.treasury}",
                                modifier = Modifier.weight(1f)
                            )
                            StatBox(
                                icon = Icons.Default.Security,
                                iconTint = MilitaryGreen,
                                label = "Ejército",
                                value = formatTroops(initialTroops),
                                modifier = Modifier.weight(1f)
                            )
                            StatBox(
                                icon = Icons.Default.People,
                                iconTint = DiplomacyBlue,
                                label = "Población",
                                value = formatPopulation(initialPop),
                                modifier = Modifier.weight(1f)
                            )
                            StatBox(
                                icon = Icons.Default.Flag,
                                iconTint = StrategyGold,
                                label = "Provincias",
                                value = "${startingProvinces.size}",
                                modifier = Modifier.weight(1f)
                            )
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        // Description
                        Text(
                            text = "PERFIL HISTÓRICO Y GEOPOLÍTICO",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = StrategyGold,
                            letterSpacing = 1.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = country.description,
                            style = MaterialTheme.typography.bodyMedium,
                            fontSize = 12.sp,
                            lineHeight = 17.sp,
                            color = MaterialTheme.colorScheme.onSurface
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        // Starting Provinces Tag List
                        Text(
                            text = "TERRITORIOS INICIALES",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = StrategyGold,
                            letterSpacing = 1.sp
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        LazyRow(
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            items(startingProvinces) { prov ->
                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(6.dp))
                                        .background(country.primaryColor.copy(alpha = 0.25f))
                                        .border(1.dp, country.primaryColor.copy(alpha = 0.6f), RoundedCornerShape(6.dp))
                                        .padding(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    Text(
                                        text = if (prov.isCapital) "★ ${prov.name}" else prov.name,
                                        fontSize = 11.sp,
                                        color = Color.White,
                                        fontWeight = if (prov.isCapital) FontWeight.Bold else FontWeight.Normal
                                    )
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(14.dp))

                        // Bottom Action Buttons
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(10.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            OutlinedButton(
                                onClick = onOpenFullMapViewer,
                                shape = RoundedCornerShape(8.dp),
                                colors = ButtonDefaults.outlinedButtonColors(
                                    contentColor = Color(0xFF93C5FD)
                                ),
                                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF3B82F6)),
                                modifier = Modifier.height(48.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Layers,
                                    contentDescription = null,
                                    modifier = Modifier.size(18.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = "Ver Mapa Base",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold
                                )
                            }

                            Button(
                                onClick = { onCountrySelected(country.id) },
                                shape = RoundedCornerShape(8.dp),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = StrategyGold,
                                    contentColor = Color(0xFF0F172A)
                                ),
                                modifier = Modifier
                                    .weight(1f)
                                    .height(48.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.PlayArrow,
                                    contentDescription = null,
                                    modifier = Modifier.size(20.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = "JUGAR CON ${country.name.uppercase()}",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 13.sp,
                                    letterSpacing = 0.5.sp
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun CountryListItemCompact(
    country: Country,
    isSelected: Boolean,
    provincesCount: Int,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .clickable(onClick = onClick)
            .border(
                width = if (isSelected) 1.5.dp else 1.dp,
                color = if (isSelected) StrategyGold else StrategyBorder,
                shape = RoundedCornerShape(8.dp)
            ),
        color = if (isSelected) StrategySurfaceElevated else StrategySurface
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = country.flagEmoji,
                    fontSize = 20.sp,
                    modifier = Modifier.padding(end = 8.dp)
                )
                Column {
                    Text(
                        text = country.name,
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold,
                        color = if (isSelected) StrategyGold else Color.White
                    )
                    Text(
                        text = "${country.capitalName} • $provincesCount prov.",
                        style = MaterialTheme.typography.bodySmall,
                        fontSize = 10.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(country.primaryColor)
            )
        }
    }
}

@Composable
private fun StatBox(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    iconTint: Color,
    label: String,
    value: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .border(1.dp, StrategyBorder, RoundedCornerShape(8.dp)),
        color = StrategySurfaceElevated
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = iconTint,
                modifier = Modifier.size(16.dp)
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = value,
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp,
                color = Color.White
            )
            Text(
                text = label,
                fontSize = 9.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

private fun formatTroops(troops: Long): String {
    return when {
        troops >= 1_000_000 -> String.format("%.1fM", troops / 1_000_000.0)
        troops >= 1_000 -> String.format("%.1fK", troops / 1_000.0)
        else -> troops.toString()
    }
}

private fun formatPopulation(pop: Long): String {
    return when {
        pop >= 1_000_000 -> String.format("%.1fM", pop / 1_000_000.0)
        pop >= 1_000 -> String.format("%.1fK", pop / 1_000.0)
        else -> pop.toString()
    }
}
