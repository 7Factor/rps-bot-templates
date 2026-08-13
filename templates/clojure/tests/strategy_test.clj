(ns strategy-test
  (:require [clojure.test :refer [deftest is run-tests]]
            [strategy :as strategy]))

(definterface RpsRandomApi
  (^long nextLong [])
  (^long nextInt [^long upper-exclusive]))

(deftype RpsRandom [^:unsynchronized-mutable ^long state]
  RpsRandomApi
  (nextLong [_]
    (set! state (unchecked-add state -7046029254386353131))
    (let [mixed-1 (unchecked-multiply
                    (bit-xor state (unsigned-bit-shift-right state 30))
                    -4658895280553007687)
          mixed-2 (unchecked-multiply
                    (bit-xor mixed-1 (unsigned-bit-shift-right mixed-1 27))
                    -7723592293110705685)]
      (bit-xor mixed-2 (unsigned-bit-shift-right mixed-2 31))))
  (nextInt [this upper-exclusive]
    (let [threshold (Long/remainderUnsigned (- upper-exclusive) upper-exclusive)]
      (loop []
        (let [value (.nextLong this)]
          (if (not (neg? (Long/compareUnsigned value threshold)))
            (Long/remainderUnsigned value upper-exclusive)
            (recur)))))))

(deftest starter-returns-only-legal-moves
  (let [rng (RpsRandom. 42)]
    (doseq [turn (range 100)]
      (is (contains? #{"R" "P" "S"}
                     (strategy/choose-move turn "" "" rng))))))

(deftest same-seed-produces-the-same-moves
  (let [first-rng (RpsRandom. -1)
        second-rng (RpsRandom. -1)]
    (doseq [turn (range 100)]
      (is (= (strategy/choose-move turn "R" "P" first-rng)
             (strategy/choose-move turn "R" "P" second-rng))))))

(deftest seed-adapter-matches-the-published-golden-vector
  (let [rng (RpsRandom. 0)]
    (is (= [-2152535657050944081 7960286522194355700 487617019471545679]
           [(.nextLong rng) (.nextLong rng) (.nextLong rng)]))))

(let [result (run-tests 'strategy-test)]
  (when (pos? (+ (:fail result) (:error result)))
    (System/exit 1)))
