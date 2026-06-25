(define (problem pick_up_lettuce_problem)
  (:domain robot1)
  (:objects
    robot1 - robot
    lettuce - object
    counterTop - object
  )
  (:init
    (at robot1 counterTop)
    (at-location lettuce counterTop)
    ;; Removed (inaction robot1) to allow actions to be performed.
  )
  (:goal
    (and
      (holding robot1 lettuce)
    )
  )
)