(define (problem wash_lettuce_problem)
  (:domain robot3)
  (:objects
    robot3 - robot
    lettuce - object
    sink - object
    counterTop - object
  )
  (:init
    (at robot3 counterTop)
    (at-location lettuce counterTop)
    (holding robot3 lettuce)
    (inaction robot3)
  )
  (:goal
    (and
      (cleaned robot3 lettuce)
    )
  )
)