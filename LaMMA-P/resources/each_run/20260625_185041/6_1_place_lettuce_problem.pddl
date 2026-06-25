(define (problem place_lettuce_problem)
  (:domain robot1)
  (:objects
    robot1 - robot
    lettuce - object
    countertop - object
  )
  (:init
    (at robot1 countertop)
    (holding robot1 lettuce)
    (not (inaction robot1))
  )
  (:goal
    (and
      (at-location lettuce countertop)
    )
  )
)