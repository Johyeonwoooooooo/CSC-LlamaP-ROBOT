(define (problem wash_lettuce_problem)
  (:domain robot2)
  (:objects
    robot2 - robot
    lettuce - object
    sink - object
    counterTop - object
  )
  (:init
    (at robot2 counterTop)
    (at-location lettuce counterTop)
    ; Assuming sink is a location, not an object on top of another.
    ; Remove or adjust this line if sink should be treated differently.
    ; (at-location sink counterTop) 
  )
  (:goal
    (and
      (cleaned robot2 lettuce)
      (at-location lettuce counterTop)
    )
  )
)