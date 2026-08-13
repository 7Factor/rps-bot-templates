(ns strategy-test
  (:require [clojure.test :refer [deftest is run-tests]]
            [strategy :as strategy]))

(definterface RpsRandomApi
  (^long nextInt [^long upper-exclusive]))

(deftype TestRandom [^java.util.Random delegate]
  RpsRandomApi
  (nextInt [_ upper-exclusive]
    (.nextInt delegate upper-exclusive)))

(deftest starter-returns-only-legal-moves
  (let [rng (TestRandom. (java.util.Random. 42))]
    (doseq [turn (range 100)]
      (is (contains? #{"R" "P" "S"}
                     (strategy/choose-move turn "" "" rng))))))

(deftest same-seed-produces-the-same-moves
  (let [first-rng (TestRandom. (java.util.Random. -1))
        second-rng (TestRandom. (java.util.Random. -1))]
    (doseq [turn (range 100)]
      (is (= (strategy/choose-move turn "R" "P" first-rng)
             (strategy/choose-move turn "R" "P" second-rng))))))

(let [result (run-tests 'strategy-test)]
  (when (pos? (+ (:fail result) (:error result)))
    (System/exit 1)))
