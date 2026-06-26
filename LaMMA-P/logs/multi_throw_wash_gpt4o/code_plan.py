import threading
import time

# Define the robots
robots = ['robot1', 'robot2']

# Action queue and task_over flag
action_queue = []
task_over = False

def throw_spatula_in_trash(robots):
    # Task: Throw the Spatula in the Trash
    GoToObject(robots[0], 'Spatula')
    PickupObject(robots[0], 'Spatula')
    GoToObject(robots[0], 'GarbageCan')
    PutObject(robots[0], 'Spatula', 'GarbageCan')

def wash_lettuce_and_place_on_countertop(robots):
    # Task: Wash the Lettuce and Place it on the CounterTop
    GoToObject(robots[1], 'Lettuce')
    PickupObject(robots[1], 'Lettuce')
    GoToObject(robots[1], 'Sink')
    PutObject(robots[1], 'Lettuce', 'Sink')
    SwitchOn(robots[1], 'Faucet')
    time.sleep(5)  # Wait for a while to let the Lettuce wash.
    SwitchOff(robots[1], 'Faucet')
    PickupObject(robots[1], 'Lettuce')
    GoToObject(robots[1], 'CounterTop')
    PutObject(robots[1], 'Lettuce', 'CounterTop')

# Create threads for parallel execution
task1_thread = threading.Thread(target=throw_spatula_in_trash, args=(robots,))
task2_thread = threading.Thread(target=wash_lettuce_and_place_on_countertop, args=(robots,))

# Start executing both tasks in parallel
task1_thread.start()
task2_thread.start()

# Wait for both tasks to finish
task1_thread.join()
task2_thread.join()

# Action queue and completion
action_queue.append({'action': 'Done'})
task_over = True
time.sleep(5)