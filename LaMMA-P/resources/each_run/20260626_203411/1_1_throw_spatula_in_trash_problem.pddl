(define (problem throw_spatula_in_trash_problem)
  (:domain robot1)
  (:objects
    robot1 - robot
    spatula - object
    garbageCan - object
    counterTop - object
    floor - object
  )
  (:init
    (at robot1 counterTop)
    (at-location spatula counterTop)
    (at-location garbageCan floor)
  )
  (:goal
    (and
      (at-location spatula garbageCan)
    )
  )
)