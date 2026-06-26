def slice_tomato(robots):
    # Task description
    GoToObject(robots[0], 'Tomato')
    PickupObject(robots[0], 'Tomato')
    GoToObject(robots[0], 'CounterTop')
    PutObject(robots[0], 'Tomato', 'CounterTop')
    SwitchOn(robots[0], 'Knife')
    time.sleep(2)
    PickupObject(robots[0], 'Knife')
    GoToObject(robots[0], 'Tomato')
    # Replace this placeholder action with the actual AI2-THOR function for slicing
    PutObject(robots[0], 'Tomato', 'CounterTop')  # This is a placeholder action for slicing. You may need to use a different AI2-THOR function or modify this line based on your actual task requirements
    SwitchOff(robots[0], 'Knife')

# Threading setup
task5_thread = threading.Thread(target=slice_tomato, args=(robots,))
task5_thread.start()

# Action queue and completion
action_queue.append({'action':'Done'})
task_over = True
time.sleep(5)
