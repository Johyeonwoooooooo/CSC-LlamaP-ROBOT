(define (problem locate_pickup_spatula_problem)
  (:domain robot2)
  (:objects
    robot2 - robot
    spatula - object
    counterTop - object
  )
  (:init
    (at robot2 counterTop)
    (at-location spatula counterTop)
    (inaction robot2)
  )
  (:goal
    (and
      (holding robot2 spatula)
    )
  )
)