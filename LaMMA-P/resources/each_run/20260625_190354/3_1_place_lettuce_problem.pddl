(define (problem place_lettuce_problem)
  (:domain robot3)
  (:objects
    robot3 - robot
    lettuce - object
    countertop - object
  )
  (:init
    (at robot3 floor) ; Assuming initial location is floor, as it's not specified.
    (holding robot3 lettuce)
    (cleaned robot3 lettuce)
    (inaction robot3)
  )
  (:goal
    (and
      (at-location lettuce countertop)
    )
  )
)