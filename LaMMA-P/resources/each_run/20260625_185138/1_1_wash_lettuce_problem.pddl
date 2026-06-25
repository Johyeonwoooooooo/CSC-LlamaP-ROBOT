(define (problem wash_lettuce_problem)
  (:domain robot1)
  (:objects
    robot1 - robot
    lettuce - object
    sink - object
    counterTop - object
  )
  (:init
    (at robot1 counterTop)
    (at-location lettuce counterTop)
    ;; Removed (inaction robot1) because it contradicts action preconditions.
  )
  (:goal
    (and
      (cleaned robot1 lettuce)
    )
  )
)