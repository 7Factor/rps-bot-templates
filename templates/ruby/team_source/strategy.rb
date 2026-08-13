# frozen_string_literal: true

def choose_move(turn, my_history, opponent_history, rng)
  moves = %w[R P S]
  moves[rng.next_int(moves.length)]
end
