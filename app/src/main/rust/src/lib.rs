// Native Simulation Engine Core written in Rust
// High-performance numerical computing for combat, economy, and geopolitical AI.

#[no_mangle]
pub extern "C" fn rust_strategy_core_version() -> i32 {
    100
}

#[no_mangle]
pub extern "C" fn rust_strategy_core_init() -> bool {
    true
}

#[no_mangle]
pub extern "C" fn rust_strategy_core_calculate_combat(
    attacker_army: i64,
    defender_army: i64,
    terrain_defense_bonus_pct: i32,
) -> i64 {
    if attacker_army <= 0 || defender_army <= 0 {
        return 0;
    }
    let defense_mult = 1.0 + (terrain_defense_bonus_pct.max(0) as f64 / 100.0);
    let effective_def = defender_army as f64 * defense_mult;
    let ratio = attacker_army as f64 / (attacker_army as f64 + effective_def);
    let casualties = (defender_army as f64 * ratio * 0.45).round() as i64;
    casualties.max(1).min(defender_army)
}

#[no_mangle]
pub extern "C" fn rust_strategy_core_evaluate_ai_threat(
    player_army: i64,
    neighbor_army: i64,
    diplomatic_relations: i32,
) -> i32 {
    let power_ratio = if neighbor_army > 0 {
        (player_army as f64 / neighbor_army as f64) * 50.0
    } else {
        100.0
    };
    let relation_factor = (100 - diplomatic_relations.clamp(-100, 100)) as f64 * 0.5;
    let threat = (power_ratio + relation_factor).round() as i32;
    threat.clamp(0, 100)
}
