# frozen_string_literal: true

require "minitest/autorun"

MASK = (1 << 64) - 1
class RpsRandom
  def initialize(seed); @state = seed & MASK; end
  def next_uint64
    @state = (@state + 0x9e3779b97f4a7c15) & MASK
    value = @state
    value = ((value ^ (value >> 30)) * 0xbf58476d1ce4e5b9) & MASK
    value = ((value ^ (value >> 27)) * 0x94d049bb133111eb) & MASK
    (value ^ (value >> 31)) & MASK
  end
  def next_int(limit); next_uint64 % limit; end
end

require_relative "../team_source/strategy"

class StrategyTest < Minitest::Test
  def test_starter_returns_only_legal_moves
    rng = RpsRandom.new(42)
    100.times { |turn| assert_includes %w[R P S], choose_move(turn, "", "", rng) }
  end

  def test_same_seed_produces_the_same_moves
    first = RpsRandom.new(MASK)
    second = RpsRandom.new(MASK)
    100.times { |turn| assert_equal choose_move(turn, "R", "P", first), choose_move(turn, "R", "P", second) }
  end

  def test_seed_adapter_matches_the_published_golden_vector
    rng = RpsRandom.new(0)
    assert_equal [16_294_208_416_658_607_535, 7_960_286_522_194_355_700, 487_617_019_471_545_679], [rng.next_uint64, rng.next_uint64, rng.next_uint64]
  end
end
