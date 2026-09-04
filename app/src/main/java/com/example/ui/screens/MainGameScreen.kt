package com.example.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.data.model.GameScreenState
import com.example.ui.components.BattleResultDialog
import com.example.ui.components.CountrySelectionScreen
import com.example.ui.components.DiplomacyDialog
import com.example.ui.components.EventTickerBar
import com.example.ui.components.FullMapViewerDialog
import com.example.ui.components.ProvinceActionSheet
import com.example.ui.components.TopHudBar
import com.example.ui.map.StrategyMapCanvas
import com.example.ui.theme.StrategyDarkBg
import com.example.viewmodel.GameViewModel

@Composable
fun MainGameScreen(
    viewModel: GameViewModel,
    modifier: Modifier = Modifier
) {
    val screenState by viewModel.screenState.collectAsState()
    val countries by viewModel.countries.collectAsState()
    val provinces by viewModel.provinces.collectAsState()
    val activeMarches by viewModel.activeMarches.collectAsState()
    val selectedPlayerCountry by viewModel.selectedPlayerCountry.collectAsState()
    val selectedProvince by viewModel.selectedProvince.collectAsState()
    val gameSpeed by viewModel.gameSpeed.collectAsState()
    val currentDateString by viewModel.currentDateString.collectAsState()
    val eventLogs by viewModel.eventLogs.collectAsState()
    val battleReport by viewModel.battleReport.collectAsState()
    val diplomacyTarget by viewModel.diplomacyTargetCountry.collectAsState()

    var showFullMapViewer by remember { mutableStateOf(false) }

    val ownedProvincesCount = provinces.count { it.ownerCountryId == selectedPlayerCountry?.id }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(StrategyDarkBg)
    ) {
        when (screenState) {
            GameScreenState.COUNTRY_SELECTION -> {
                CountrySelectionScreen(
                    countries = countries,
                    provinces = provinces,
                    onCountrySelected = { countryId ->
                        viewModel.selectPlayerCountry(countryId)
                    },
                    onOpenFullMapViewer = { showFullMapViewer = true },
                    modifier = Modifier
                        .fillMaxSize()
                        .statusBarsPadding()
                        .navigationBarsPadding()
                )
            }

            GameScreenState.PLAYING, GameScreenState.GAME_OVER -> {
                // 1. Full-screen Real-time Strategy Map with Blank_province_map.png
                StrategyMapCanvas(
                    countries = countries,
                    provinces = provinces,
                    activeMarches = activeMarches,
                    selectedProvince = selectedProvince,
                    playerCountry = selectedPlayerCountry,
                    onProvinceSelected = { prov ->
                        viewModel.selectProvince(prov)
                    },
                    onOpenFullMapViewer = { showFullMapViewer = true },
                    modifier = Modifier.fillMaxSize()
                )

                // 2. Top HUD Controls & Info Bar (Horizontal single row)
                Column(
                    modifier = Modifier
                        .align(Alignment.TopCenter)
                        .fillMaxWidth()
                        .statusBarsPadding()
                ) {
                    TopHudBar(
                        playerCountry = selectedPlayerCountry,
                        dateString = currentDateString,
                        gameSpeed = gameSpeed,
                        ownedProvincesCount = ownedProvincesCount,
                        onSpeedChange = { speed -> viewModel.setGameSpeed(speed) },
                        onManualTick = { viewModel.manualTick() },
                        onChangeCountry = { viewModel.backToCountrySelection() },
                        onOpenFullMapViewer = { showFullMapViewer = true }
                    )

                    // Event Ticker Bar floating under top HUD
                    EventTickerBar(
                        eventLogs = eventLogs,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 12.dp, vertical = 4.dp)
                    )
                }

                // 3. Right-Side Province Action Sheet in Landscape
                AnimatedVisibility(
                    visible = selectedProvince != null,
                    enter = slideInHorizontally(initialOffsetX = { it }),
                    exit = slideOutHorizontally(targetOffsetX = { it }),
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(top = 54.dp, end = 12.dp, bottom = 12.dp)
                        .fillMaxHeight()
                ) {
                    selectedProvince?.let { prov ->
                        ProvinceActionSheet(
                            province = prov,
                            allProvinces = provinces,
                            allCountries = countries,
                            playerCountry = selectedPlayerCountry,
                            onRecruit = { amount -> viewModel.recruitTroops(prov.id, amount) },
                            onInvestEconomy = { viewModel.investInEconomy(prov.id) },
                            onBuildFortification = { viewModel.buildFortification(prov.id) },
                            onOrderMovement = { targetProvId, amount ->
                                viewModel.orderArmyMovement(prov.id, targetProvId, amount)
                            },
                            onOpenDiplomacy = { countryId -> viewModel.openDiplomacy(countryId) },
                            onClose = { viewModel.selectProvince(null) }
                        )
                    }
                }

                // 4. Diplomacy Dialog
                diplomacyTarget?.let { target ->
                    DiplomacyDialog(
                        targetCountry = target,
                        playerCountry = selectedPlayerCountry,
                        onDeclareWar = { viewModel.declareWar(it) },
                        onMakePeace = { viewModel.makePeace(it) },
                        onImproveRelations = { viewModel.improveRelations(it) },
                        onSignNonAggression = { viewModel.signNonAggressionPact(it) },
                        onDismiss = { viewModel.closeDiplomacy() }
                    )
                }

                // 5. Battle Result Dialog
                battleReport?.let { report ->
                    BattleResultDialog(
                        report = report,
                        onDismiss = { viewModel.dismissBattleReport() }
                    )
                }
            }
        }

        // 6. Full Map Viewer Dialog for Blank_province_map.png
        if (showFullMapViewer) {
            FullMapViewerDialog(
                provinces = provinces,
                countries = countries,
                onDismiss = { showFullMapViewer = false }
            )
        }
    }
}
