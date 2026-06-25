(define (problem go_to_lettuce_problem)
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
      (at robot1 lettuce)
    )
  )
)