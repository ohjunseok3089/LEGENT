from legent import Environment, Action, generate_scene, ResetInfo, save_image
import keyboard
import time

env = Environment(env_path="auto")
scene = generate_scene(room_num=1)
try:
    obs = env.reset(ResetInfo(scene))

    for i in range(6):
        action = Action(rotate_right=60)
        obs = env.step(action)
        print(obs)
        save_image(obs.image, f"agent_views/image_{i}.png")

    while True:
        # Simulate pressing 'w' key
        action = Action()  # Empty action since we're using keyboard simulation
        obs = env.step(action)
finally:
    env.close()