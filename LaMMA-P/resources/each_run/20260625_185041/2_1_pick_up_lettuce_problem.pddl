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
    (inaction robot1)
  )
  (:goal
    (and
      (holding robot1 lettuce)
    )
  )
)