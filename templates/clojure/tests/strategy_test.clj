(ns strategy-test
  (:require [clojure.test :refer [deftest is run-tests]]
            [strategy :as strategy]))

(definterface RpsRandomApi
  (^long nextInt [^long upper-exclusive]))

(deftype RpsRandom [^java.util.SplittableRandom delegate]
  RpsRandomApi
  (nextInt [_ upper-exclusive]
    (.nextInt delegate upper-exclusive)))

(deftest starter-returns-only-legal-moves
  (let [rng (RpsRandom. (java.util.SplittableRandom. 42))]
    (doseq [turn (range 100)]
      (is (contains? #{"R" "P" "S"}
                     (strategy/choose-move turn "" "" rng))))))

(deftest same-seed-produces-the-same-moves
  (let [first-rng (RpsRandom. (java.util.SplittableRandom. -1))
        second-rng (RpsRandom. (java.util.SplittableRandom. -1))]
    (doseq [turn (range 100)]
      (is (= (strategy/choose-move turn "R" "P" first-rng)
             (strategy/choose-move turn "R" "P" second-rng))))))

(deftest seed-adapter-matches-the-published-golden-vector
  (let [rng (java.util.SplittableRandom. 0)]
    (is (= [-2152535657050944081 7960286522194355700 487617019471545679]
           [(.nextLong rng) (.nextLong rng) (.nextLong rng)]))))

(let [result (run-tests 'strategy-test)]
  (when (pos? (+ (:fail result) (:error result)))
    (System/exit 1)))
