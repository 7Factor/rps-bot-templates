pub struct RpsRandom {
    state: u64,
}

impl RpsRandom {
    pub fn new(seed: u64) -> Self {
        Self { state: seed }
    }

    pub fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9e3779b97f4a7c15);
        let mut value = self.state;
        value = (value ^ (value >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
        value = (value ^ (value >> 27)).wrapping_mul(0x94d049bb133111eb);
        value ^ (value >> 31)
    }

    pub fn next_usize(&mut self, upper_exclusive: usize) -> usize {
        assert!(upper_exclusive > 0);
        let bound = upper_exclusive as u64;
        let threshold = bound.wrapping_neg() % bound;
        loop {
            let value = self.next_u64();
            if value >= threshold {
                return (value % bound) as usize;
            }
        }
    }
}

include!("../team_source/strategy.rs");

#[test]
fn starter_returns_only_legal_moves() {
    let mut rng = RpsRandom::new(42);
    for turn in 0..100 {
        assert!(matches!(choose_move(turn, "", "", &mut rng), "R" | "P" | "S"));
    }
}

#[test]
fn same_seed_produces_the_same_moves() {
    let mut first = RpsRandom::new(u64::MAX);
    let mut second = RpsRandom::new(u64::MAX);
    for turn in 0..100 {
        assert_eq!(
            choose_move(turn, "R", "P", &mut first),
            choose_move(turn, "R", "P", &mut second)
        );
    }
}

#[test]
fn seed_adapter_matches_the_published_golden_vector() {
    let mut rng = RpsRandom::new(0);
    assert_eq!(rng.next_u64(), 16_294_208_416_658_607_535);
    assert_eq!(rng.next_u64(), 7_960_286_522_194_355_700);
    assert_eq!(rng.next_u64(), 487_617_019_471_545_679);
}
