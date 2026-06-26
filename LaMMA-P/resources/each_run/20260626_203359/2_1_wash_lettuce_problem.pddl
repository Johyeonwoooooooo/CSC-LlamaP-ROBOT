(define (problem wash_lettuce_problem)
  (:domain robot2)
  (:objects
    robot2 - robot
    lettuce - object
    sink - object
    counterTop - object
  )
  (:init
    (at robot2 counterTop)
    (at-location lettuce counterTop)
    (at-location sink counterTop)
    (inaction robot2)
  )
  (:goal
    (and
      (cleaned robot2 lettuce)
      (at-location lettuce counterTop)
    )
  )
)