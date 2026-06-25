(define (problem move_to_countertop_problem)
  (:domain robot1)
  (:objects
    robot1 - robot
    counterTop - object
    sink - object
  )
  (:init
    (at robot1 sink)
    (not (inaction robot1))
  )
  (:goal
    (and
      (at robot1 counterTop)
    )
  )
)