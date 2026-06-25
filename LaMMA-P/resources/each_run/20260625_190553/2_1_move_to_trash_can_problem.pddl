(define (problem move_to_trash_can_problem)
  (:domain robot2)
  (:objects
    robot2 - robot
    GarbageCan - object
    Floor - object
  )
  (:init
    (at robot2 Floor)
    (at-location GarbageCan Floor)
    (inaction robot2)
  )
  (:goal
    (and
      (at robot2 GarbageCan)
    )
  )
)