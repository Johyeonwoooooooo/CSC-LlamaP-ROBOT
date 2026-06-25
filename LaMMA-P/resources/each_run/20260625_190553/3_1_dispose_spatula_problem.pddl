(define (problem dispose_spatula_problem)
  (:domain robot2)
  (:objects
    robot2 - robot
    spatula - object
    garbageCan - object
    counterTop - object
    floor - object
  )
  (:init
    (at robot2 counterTop)
    (at-location spatula counterTop)
    (at-location garbageCan floor)
    (inaction robot2)
  )
  (:goal
    (and
      (at-location spatula garbageCan)
    )
  )
)