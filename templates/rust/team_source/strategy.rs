pub fn choose_move(
    _turn: usize,
    _my_history: &str,
    _opponent_history: &str,
    rng: &mut RpsRandom
) -> &'static str {
    let moves = ["R", "P", "S"];
    moves[rng.next_usize(moves.len())]
}
