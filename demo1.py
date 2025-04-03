from legent import Environment, Action, generate_scene, ResetInfo, save_image
from legent.dataset.controller import PathToUser, PathFollower
import keyboard
import time
from legent.utils.math import vec_xz, distance

env = Environment(env_path="auto")
scene = generate_scene(room_num=1)
try:
    obs = env.reset(ResetInfo(scene))

    api_call = PathToUser()
    obs = env.step(Action(api_calls=[api_call]))
    if "corners" in obs.api_returns:
        corners = obs.api_returns["corners"]
        print(f"{corners}")
        
        # Create a custom PathFollower that stops one step before reaching the final destination
        class CustomPathFollower(PathFollower):
            def _get_next_action(self, position, forward):
                position_xz = vec_xz(position)
                
                # If we have no more corners, we're done
                if not self.corners:
                    return None
                
                # Get the last corner (destination)
                final_corner = self.corners[-1]
                final_corner_xz = vec_xz(final_corner)
                
                # If we're on the last corner and close enough, we're done
                if len(self.corners) == 1:
                    # Stop one step back (adjust this distance as needed)
                    STOP_DISTANCE = 20.0  # One unit away
                    
                    if distance(position_xz, final_corner_xz) < STOP_DISTANCE:
                        return None
                
                # Use the original method for all other cases
                return super()._get_next_action(position, forward)
        
        # Use our custom path follower
        path_follower = CustomPathFollower(use_teleport=True)
        path_follower.corners = corners
        
        # Follow the path until we reach near the final corner
        while True:
            agent_info = obs.game_states["agent"]
            camera = obs.game_states["agent_camera"]
            
            action = path_follower._get_next_action(
                agent_info["position"], 
                camera["forward"]
            )
            
            if action is None:
                print("Stopped one step before the final destination!")
                break
                
            obs = env.step(action)
            save_image(obs.image, f"agent_views/path_{len(corners)}.png")
            
    for i in range(6):
        action = Action(rotate_right=60)
        obs = env.step(action)
        print(obs)
        save_image(obs.image, f"agent_views/image_{i}.png")

    while True:
        # Simulate pressing 'w' key
        action = Action(api_calls=["goto_user()"])
        obs = env.step(action)
finally:
    env.close()