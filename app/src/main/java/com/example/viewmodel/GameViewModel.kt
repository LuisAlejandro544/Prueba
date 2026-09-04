package com.example.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.data.model.ArmyMarch
import com.example.data.model.BattleReport
import com.example.data.model.Country
import com.example.data.model.GameEventLog
import com.example.data.model.GameScreenState
import com.example.data.model.GameSpeed
import com.example.data.model.Province
import com.example.data.repository.GameDataRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.math.max
import kotlin.math.min
import kotlin.random.Random

class GameViewModel : ViewModel() {

    private val _countries = MutableStateFlow<List<Country>>(emptyList())
    val countries: StateFlow<List<Country>> = _countries.asStateFlow()

    private val _provinces = MutableStateFlow<List<Province>>(emptyList())
    val provinces: StateFlow<List<Province>> = _provinces.asStateFlow()

    private val _activeMarches = MutableStateFlow<List<ArmyMarch>>(emptyList())
    val activeMarches: StateFlow<List<ArmyMarch>> = _activeMarches.asStateFlow()

    private val _selectedPlayerCountry = MutableStateFlow<Country?>(null)
    val selectedPlayerCountry: StateFlow<Country?> = _selectedPlayerCountry.asStateFlow()

    private val _selectedProvince = MutableStateFlow<Province?>(null)
    val selectedProvince: StateFlow<Province?> = _selectedProvince.asStateFlow()

    private val _gameSpeed = MutableStateFlow(GameSpeed.NORMAL)
    val gameSpeed: StateFlow<GameSpeed> = _gameSpeed.asStateFlow()

    private val _screenState = MutableStateFlow(GameScreenState.COUNTRY_SELECTION)
    val screenState: StateFlow<GameScreenState> = _screenState.asStateFlow()

    private val _eventLogs = MutableStateFlow<List<GameEventLog>>(emptyList())
    val eventLogs: StateFlow<List<GameEventLog>> = _eventLogs.asStateFlow()

    private val _battleReport = MutableStateFlow<BattleReport?>(null)
    val battleReport: StateFlow<BattleReport?> = _battleReport.asStateFlow()

    private val _diplomacyTargetCountry = MutableStateFlow<Country?>(null)
    val diplomacyTargetCountry: StateFlow<Country?> = _diplomacyTargetCountry.asStateFlow()

    // Calendar state
    private var day = 1
    private var month = 3
    private var year = 2026
    private val monthNames = listOf(
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    )

    private val _currentDateString = MutableStateFlow("1 de Marzo, 2026")
    val currentDateString: StateFlow<String> = _currentDateString.asStateFlow()

    private var simulationJob: Job? = null
    private var eventIdCounter = 1L

    init {
        loadInitialGameData()
    }

    fun loadInitialGameData() {
        val initialCountries = GameDataRepository.getInitialCountries()
        val initialProvinces = GameDataRepository.getInitialProvinces()
        _countries.value = initialCountries
        _provinces.value = initialProvinces
        _activeMarches.value = emptyList()
        _selectedProvince.value = null
        _battleReport.value = null
        day = 1
        month = 3
        year = 2026
        _currentDateString.value = "$day de ${monthNames[month - 1]}, $year"
        _eventLogs.value = listOf(
            GameEventLog(
                id = eventIdCounter++,
                timestamp = _currentDateString.value,
                message = "Elige una nación de Latinoamérica para iniciar tu campaña de estrategia histórica.",
                icon = "🌎",
                isImportant = true
            )
        )
    }

    fun selectPlayerCountry(countryId: String) {
        val selected = _countries.value.find { it.id == countryId } ?: return
        val updatedCountries = _countries.value.map {
            if (it.id == countryId) it.copy(isPlayer = true) else it.copy(isPlayer = false)
        }
        _countries.value = updatedCountries
        _selectedPlayerCountry.value = updatedCountries.find { it.id == countryId }
        _screenState.value = GameScreenState.PLAYING

        // Select their capital by default
        val capital = _provinces.value.find { it.ownerCountryId == countryId && it.isCapital }
            ?: _provinces.value.find { it.ownerCountryId == countryId }
        _selectedProvince.value = capital

        addEventLog(
            message = "¡Has asumido el mando de ${selected.name}! Lidera tu nación hacia la hegemonía regional.",
            icon = selected.flagEmoji,
            isImportant = true
        )

        startSimulationLoop()
    }

    fun backToCountrySelection() {
        simulationJob?.cancel()
        _gameSpeed.value = GameSpeed.PAUSED
        _screenState.value = GameScreenState.COUNTRY_SELECTION
    }

    fun setGameSpeed(speed: GameSpeed) {
        _gameSpeed.value = speed
        startSimulationLoop()
    }

    fun selectProvince(province: Province?) {
        _selectedProvince.value = province
    }

    fun openDiplomacy(countryId: String) {
        val country = _countries.value.find { it.id == countryId }
        _diplomacyTargetCountry.value = country
    }

    fun closeDiplomacy() {
        _diplomacyTargetCountry.value = null
    }

    fun dismissBattleReport() {
        _battleReport.value = null
    }

    private fun startSimulationLoop() {
        simulationJob?.cancel()
        val speed = _gameSpeed.value
        if (speed == GameSpeed.PAUSED) return

        simulationJob = viewModelScope.launch {
            while (isActive) {
                delay(speed.intervalMs)
                executeGameTick()
            }
        }
    }

    fun manualTick() {
        viewModelScope.launch {
            executeGameTick()
        }
    }

    private fun executeGameTick() {
        advanceDate()
        processEconomyAndManpower()
        processArmyMarches()
        processAiTurn()
        updateSelectedReferences()
    }

    private fun advanceDate() {
        day += 2
        if (day > 30) {
            day = 1
            month++
            if (month > 12) {
                month = 1
                year++
            }
        }
        _currentDateString.value = "$day de ${monthNames[month - 1]}, $year"
    }

    private fun processEconomyAndManpower() {
        val provs = _provinces.value
        _countries.update { currentCountries ->
            currentCountries.map { country ->
                val ownedProvinces = provs.filter { it.ownerCountryId == country.id }
                val totalEconomy = ownedProvinces.sumOf { it.economy }
                val totalArmy = ownedProvinces.sumOf { it.army }

                // Income: economy * 3, Upkeep: army * 0.04
                val grossIncome = (totalEconomy * 3.5).toLong()
                val armyUpkeep = (totalArmy * 0.035).toLong()
                val netIncome = grossIncome - armyUpkeep
                val newTreasury = max(0L, country.treasury + netIncome)

                // Manpower regeneration based on total population
                val totalPopulation = ownedProvinces.sumOf { it.population }
                val manpowerGrowth = max(500L, (totalPopulation * 0.0004).toLong())
                val newManpower = country.manpower + manpowerGrowth

                country.copy(
                    treasury = newTreasury,
                    manpower = newManpower
                )
            }
        }
    }

    private fun processArmyMarches() {
        val currentMarches = _activeMarches.value
        if (currentMarches.isEmpty()) return

        val remainingMarches = mutableListOf<ArmyMarch>()

        for (march in currentMarches) {
            val newProgress = march.progress + march.speedPerTick
            if (newProgress >= 1.0f) {
                resolveMarchArrival(march)
            } else {
                remainingMarches.add(march.copy(progress = newProgress))
            }
        }

        _activeMarches.value = remainingMarches
    }

    private fun resolveMarchArrival(march: ArmyMarch) {
        val targetProvince = _provinces.value.find { it.id == march.toProvinceId } ?: return
        val marchingCountry = _countries.value.find { it.id == march.ownerCountryId } ?: return
        val defenderCountry = _countries.value.find { it.id == targetProvince.ownerCountryId } ?: return

        if (targetProvince.ownerCountryId == march.ownerCountryId) {
            // Friendly reinforcement
            _provinces.update { list ->
                list.map {
                    if (it.id == targetProvince.id) {
                        it.copy(army = it.army + march.soldiers)
                    } else it
                }
            }
            if (march.ownerCountryId == _selectedPlayerCountry.value?.id) {
                addEventLog(
                    message = "${march.soldiers} soldados llegaron como refuerzo a ${targetProvince.name}.",
                    icon = "🛡️"
                )
            }
        } else {
            // Combat resolution! Attacker vs Defender
            val isAtWar = marchingCountry.atWarWith.contains(defenderCountry.id)
            if (!isAtWar) {
                // Auto-declare war if attacking
                declareWarBetween(marchingCountry.id, defenderCountry.id)
            }

            // Calculate battle results with defense bonus & tactical dice
            val defenseMultiplier = 1.0f + (targetProvince.fortificationLevel * 0.25f)
            val defenderEffective = (targetProvince.army * defenseMultiplier).toLong()

            val attackerRoll = Random.nextDouble(0.85, 1.25)
            val defenderRoll = Random.nextDouble(0.90, 1.30)

            val attackerPower = (march.soldiers * attackerRoll).toLong()
            val defenderPower = (defenderEffective * defenderRoll).toLong()

            val attackerWon = attackerPower > defenderPower

            val attackerLosses: Long
            val defenderLosses: Long
            val provinceCaptured: Boolean

            if (attackerWon) {
                provinceCaptured = true
                defenderLosses = targetProvince.army
                val remainingAttacker = max(1000L, (march.soldiers - (defenderEffective * 0.75).toLong()))
                attackerLosses = march.soldiers - remainingAttacker

                _provinces.update { list ->
                    list.map {
                        if (it.id == targetProvince.id) {
                            it.copy(
                                ownerCountryId = march.ownerCountryId,
                                army = remainingAttacker,
                                fortificationLevel = max(0, it.fortificationLevel - 1)
                            )
                        } else it
                    }
                }

                addEventLog(
                    message = "⚔️ ¡${marchingCountry.name} conquistó ${targetProvince.name} derrotando a ${defenderCountry.name}!",
                    icon = "🚩",
                    isImportant = true
                )
            } else {
                provinceCaptured = false
                attackerLosses = march.soldiers
                val remainingDefender = max(500L, (targetProvince.army - (march.soldiers * 0.6).toLong()))
                defenderLosses = targetProvince.army - remainingDefender

                _provinces.update { list ->
                    list.map {
                        if (it.id == targetProvince.id) {
                            it.copy(army = remainingDefender)
                        } else it
                    }
                }

                addEventLog(
                    message = "🛡️ ${defenderCountry.name} defendió con éxito ${targetProvince.name} frente a ${marchingCountry.name}.",
                    icon = "⚔️"
                )
            }

            // If player was involved, show battle report modal!
            val playerCountryId = _selectedPlayerCountry.value?.id
            if (march.ownerCountryId == playerCountryId || defenderCountry.id == playerCountryId) {
                _battleReport.value = BattleReport(
                    provinceName = targetProvince.name,
                    attackerCountryName = marchingCountry.name,
                    defenderCountryName = defenderCountry.name,
                    attackerSoldiers = march.soldiers,
                    defenderSoldiers = targetProvince.army,
                    attackerLosses = attackerLosses,
                    defenderLosses = defenderLosses,
                    attackerWon = attackerWon,
                    provinceCaptured = provinceCaptured
                )
            }
        }
    }

    private fun processAiTurn() {
        // AI makes opportunistic decisions every few ticks
        if (Random.nextInt(100) > 35) return

        val playerCountryId = _selectedPlayerCountry.value?.id ?: return
        val aiCountries = _countries.value.filter { it.id != playerCountryId }
        if (aiCountries.isEmpty()) return

        val randomAi = aiCountries.random()
        val aiProvinces = _provinces.value.filter { it.ownerCountryId == randomAi.id }
        if (aiProvinces.isEmpty()) return

        // 1. If high treasury, invest in economy or fortify
        if (randomAi.treasury > 8000) {
            val provToBoost = aiProvinces.minByOrNull { it.economy }
            if (provToBoost != null) {
                _provinces.update { list ->
                    list.map {
                        if (it.id == provToBoost.id) it.copy(economy = it.economy + 10) else it
                    }
                }
                _countries.update { list ->
                    list.map {
                        if (it.id == randomAi.id) it.copy(treasury = it.treasury - 3000) else it
                    }
                }
            }
        }

        // 2. If at war, send troops to attack enemy province
        if (randomAi.atWarWith.isNotEmpty()) {
            val enemyId = randomAi.atWarWith.random()
            for (myProv in aiProvinces.filter { it.army > 12000 }) {
                val adjacentEnemyProv = _provinces.value.find {
                    myProv.adjacentProvinceIds.contains(it.id) && it.ownerCountryId == enemyId
                }
                if (adjacentEnemyProv != null) {
                    val troopsToSend = (myProv.army * 0.65).toLong()
                    startMarch(
                        fromProvinceId = myProv.id,
                        toProvinceId = adjacentEnemyProv.id,
                        ownerCountryId = randomAi.id,
                        soldiers = troopsToSend
                    )
                    break
                }
            }
        }
    }

    private fun updateSelectedReferences() {
        val currentSelected = _selectedProvince.value
        if (currentSelected != null) {
            _selectedProvince.value = _provinces.value.find { it.id == currentSelected.id }
        }
        val currentPlayer = _selectedPlayerCountry.value
        if (currentPlayer != null) {
            _selectedPlayerCountry.value = _countries.value.find { it.id == currentPlayer.id }
        }
    }

    // --- PLAYER COMMANDS ---

    fun recruitTroops(provinceId: String, amount: Long) {
        val player = _selectedPlayerCountry.value ?: return
        val province = _provinces.value.find { it.id == provinceId && it.ownerCountryId == player.id } ?: return

        val costPerTroop = 2L
        val totalCost = amount * costPerTroop

        if (player.treasury < totalCost) {
            addEventLog(
                message = "Fondos insuficientes para reclutar $amount tropas (requiere $totalCost 💰).",
                icon = "⚠️"
            )
            return
        }

        if (player.manpower < amount) {
            addEventLog(
                message = "Reclutas insuficientes (requiere $amount de mano de obra).",
                icon = "⚠️"
            )
            return
        }

        // Deduct and add
        _countries.update { list ->
            list.map {
                if (it.id == player.id) {
                    it.copy(
                        treasury = it.treasury - totalCost,
                        manpower = it.manpower - amount
                    )
                } else it
            }
        }

        _provinces.update { list ->
            list.map {
                if (it.id == provinceId) {
                    it.copy(army = it.army + amount)
                } else it
            }
        }

        addEventLog(
            message = "Reclutaste $amount soldados en ${province.name} por $totalCost oro.",
            icon = "🪖"
        )
        updateSelectedReferences()
    }

    fun investInEconomy(provinceId: String) {
        val player = _selectedPlayerCountry.value ?: return
        val province = _provinces.value.find { it.id == provinceId && it.ownerCountryId == player.id } ?: return

        val cost = 2500L
        if (player.treasury < cost) {
            addEventLog(
                message = "Se necesitan $cost 💰 para invertir en el desarrollo económico de ${province.name}.",
                icon = "⚠️"
            )
            return
        }

        _countries.update { list ->
            list.map {
                if (it.id == player.id) it.copy(treasury = it.treasury - cost) else it
            }
        }

        _provinces.update { list ->
            list.map {
                if (it.id == provinceId) it.copy(economy = it.economy + 15) else it
            }
        }

        addEventLog(
            message = "Inversión realizada en ${province.name}: +15 de desarrollo económico.",
            icon = "📈"
        )
        updateSelectedReferences()
    }

    fun buildFortification(provinceId: String) {
        val player = _selectedPlayerCountry.value ?: return
        val province = _provinces.value.find { it.id == provinceId && it.ownerCountryId == player.id } ?: return

        if (province.fortificationLevel >= 3) {
            addEventLog(
                message = "${province.name} ya cuenta con el nivel máximo de fortificación (Nivel 3).",
                icon = "🏰"
            )
            return
        }

        val cost = 4000L
        if (player.treasury < cost) {
            addEventLog(
                message = "Se necesitan $cost 💰 para construir fortificaciones en ${province.name}.",
                icon = "⚠️"
            )
            return
        }

        _countries.update { list ->
            list.map {
                if (it.id == player.id) it.copy(treasury = it.treasury - cost) else it
            }
        }

        _provinces.update { list ->
            list.map {
                if (it.id == provinceId) it.copy(fortificationLevel = it.fortificationLevel + 1) else it
            }
        }

        addEventLog(
            message = "Fortificación erigida en ${province.name} (Nivel ${province.fortificationLevel + 1}). +25% defensa.",
            icon = "🏰"
        )
        updateSelectedReferences()
    }

    fun orderArmyMovement(fromProvinceId: String, toProvinceId: String, soldiers: Long) {
        val player = _selectedPlayerCountry.value ?: return
        val fromProv = _provinces.value.find { it.id == fromProvinceId && it.ownerCountryId == player.id } ?: return
        val toProv = _provinces.value.find { it.id == toProvinceId } ?: return

        if (!fromProv.adjacentProvinceIds.contains(toProvinceId)) {
            addEventLog(
                message = "Las provincias no son limítrofes. Solo puedes mover tropas a regiones adyacentes.",
                icon = "⚠️"
            )
            return
        }

        val availableTroops = fromProv.army - 1000 // Keep minimal garrison
        if (soldiers > availableTroops) {
            addEventLog(
                message = "Tropas insuficientes. Debes mantener al menos 1,000 soldados en la guarnición.",
                icon = "⚠️"
            )
            return
        }

        // If target is foreign and not at war, automatically declare war
        if (toProv.ownerCountryId != player.id) {
            val targetCountry = _countries.value.find { it.id == toProv.ownerCountryId }
            if (targetCountry != null && !player.atWarWith.contains(targetCountry.id)) {
                declareWarBetween(player.id, targetCountry.id)
            }
        }

        startMarch(
            fromProvinceId = fromProvinceId,
            toProvinceId = toProvinceId,
            ownerCountryId = player.id,
            soldiers = soldiers
        )

        addEventLog(
            message = "Un regimiento de $soldiers soldados marcha desde ${fromProv.name} hacia ${toProv.name}.",
            icon = "🪖"
        )
        updateSelectedReferences()
    }

    private fun startMarch(fromProvinceId: String, toProvinceId: String, ownerCountryId: String, soldiers: Long) {
        // Deduct soldiers from origin province
        _provinces.update { list ->
            list.map {
                if (it.id == fromProvinceId) {
                    it.copy(army = max(1000L, it.army - soldiers))
                } else it
            }
        }

        val march = ArmyMarch(
            id = "march_${System.currentTimeMillis()}_${Random.nextInt(1000)}",
            fromProvinceId = fromProvinceId,
            toProvinceId = toProvinceId,
            ownerCountryId = ownerCountryId,
            soldiers = soldiers,
            progress = 0f,
            speedPerTick = 0.25f
        )

        _activeMarches.update { it + march }
    }

    // --- DIPLOMACY ---

    fun declareWar(targetCountryId: String) {
        val player = _selectedPlayerCountry.value ?: return
        declareWarBetween(player.id, targetCountryId)
        closeDiplomacy()
    }

    private fun declareWarBetween(countryAId: String, countryBId: String) {
        val countryA = _countries.value.find { it.id == countryAId } ?: return
        val countryB = _countries.value.find { it.id == countryBId } ?: return

        _countries.update { list ->
            list.map { country ->
                when (country.id) {
                    countryAId -> {
                        val newWars = country.atWarWith.toMutableSet().apply { add(countryBId) }
                        val newAllies = country.allies.toMutableSet().apply { remove(countryBId) }
                        val newNaps = country.nonAggressionWith.toMutableSet().apply { remove(countryBId) }
                        country.copy(
                            atWarWith = newWars,
                            allies = newAllies,
                            nonAggressionWith = newNaps,
                            stability = max(30, country.stability - 5)
                        )
                    }
                    countryBId -> {
                        val newWars = country.atWarWith.toMutableSet().apply { add(countryAId) }
                        val newAllies = country.allies.toMutableSet().apply { remove(countryAId) }
                        val newNaps = country.nonAggressionWith.toMutableSet().apply { remove(countryAId) }
                        country.copy(
                            atWarWith = newWars,
                            allies = newAllies,
                            nonAggressionWith = newNaps
                        )
                    }
                    else -> country
                }
            }
        }

        addEventLog(
            message = "🚨 ¡ESTADO DE GUERRA declarado entre ${countryA.name} y ${countryB.name}!",
            icon = "⚔️",
            isImportant = true
        )
    }

    fun makePeace(targetCountryId: String) {
        val player = _selectedPlayerCountry.value ?: return
        val target = _countries.value.find { it.id == targetCountryId } ?: return

        _countries.update { list ->
            list.map { country ->
                when (country.id) {
                    player.id -> {
                        val newWars = country.atWarWith.toMutableSet().apply { remove(targetCountryId) }
                        country.copy(atWarWith = newWars)
                    }
                    targetCountryId -> {
                        val newWars = country.atWarWith.toMutableSet().apply { remove(player.id) }
                        country.copy(atWarWith = newWars)
                    }
                    else -> country
                }
            }
        }

        addEventLog(
            message = "🕊️ Tratado de Paz firmado entre ${player.name} y ${target.name}.",
            icon = "🕊️",
            isImportant = true
        )
        closeDiplomacy()
    }

    fun improveRelations(targetCountryId: String) {
        val player = _selectedPlayerCountry.value ?: return
        val target = _countries.value.find { it.id == targetCountryId } ?: return

        val cost = 1200L
        if (player.treasury < cost) {
            addEventLog(
                message = "Se necesitan $cost 💰 en la tesorería para enviar delegación diplomática.",
                icon = "⚠️"
            )
            return
        }

        _countries.update { list ->
            list.map {
                if (it.id == player.id) {
                    val currentRel = it.relations[targetCountryId] ?: 0
                    val updatedRel = it.relations.toMutableMap().apply { put(targetCountryId, min(100, currentRel + 25)) }
                    it.copy(treasury = it.treasury - cost, relations = updatedRel)
                } else it
            }
        }

        addEventLog(
            message = "Delegación diplomática enviada a ${target.name}: Relaciones mejoradas (+25).",
            icon = "🤝"
        )
    }

    fun signNonAggressionPact(targetCountryId: String) {
        val player = _selectedPlayerCountry.value ?: return
        val target = _countries.value.find { it.id == targetCountryId } ?: return

        if (player.atWarWith.contains(targetCountryId)) {
            addEventLog(
                message = "No puedes firmar un pacto de no agresión estando en guerra activa.",
                icon = "⚠️"
            )
            return
        }

        _countries.update { list ->
            list.map { country ->
                when (country.id) {
                    player.id -> {
                        val naps = country.nonAggressionWith.toMutableSet().apply { add(targetCountryId) }
                        country.copy(nonAggressionWith = naps)
                    }
                    targetCountryId -> {
                        val naps = country.nonAggressionWith.toMutableSet().apply { add(player.id) }
                        country.copy(nonAggressionWith = naps)
                    }
                    else -> country
                }
            }
        }

        addEventLog(
            message = "📜 Pacto de No Agresión sellado con ${target.name}.",
            icon = "📜"
        )
    }

    private fun addEventLog(message: String, icon: String, isImportant: Boolean = false) {
        val log = GameEventLog(
            id = eventIdCounter++,
            timestamp = _currentDateString.value,
            message = message,
            icon = icon,
            isImportant = isImportant
        )
        _eventLogs.update { (listOf(log) + it).take(50) }
    }
}
