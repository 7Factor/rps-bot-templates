(ns strategy)

(defn choose-move [turn my-history opponent-history rng]
  (let [moves ["R" "P" "S"]]
    (nth moves (.nextInt rng (count moves)))))
