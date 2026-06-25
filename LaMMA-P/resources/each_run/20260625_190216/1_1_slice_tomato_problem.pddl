(define (problem slice_tomato_problem)
  (:domain robot1)
  (:objects
    robot1 - robot
    tomato - object
    knife - object
    counterTop - object
  )
  (:init
    (at robot1 counterTop)
    (at-location tomato counterTop)
    (at-location knife counterTop)
    ;; Removed (inaction robot1) to allow actions to be performed.
  )
  (:goal
    (and
      (sliced tomato)
    )
  )
)