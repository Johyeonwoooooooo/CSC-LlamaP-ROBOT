(define (problem pick_up_lettuce_problem)
  (:domain robot3)
  (:objects
    robot3 - robot
    lettuce - object
    counterTop - object
  )
  (:init
    (at robot3 counterTop)
    (at-location lettuce counterTop)
    (inaction robot3)
  )
  (:goal
    (and
      (holding robot3 lettuce)
    )
  )
)