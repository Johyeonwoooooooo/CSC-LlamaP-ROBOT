(define (problem go_to_sink_problem)
  (:domain robot1)
  (:objects
    robot1 - robot
    sink - object
    counterTop - object
    lettuce - object
  )
  (:init
    (at robot1 counterTop)
    (at-location lettuce counterTop)
    (holding robot1 lettuce)
  )
  (:goal
    (and
      (at robot1 sink)
    )
  )
)