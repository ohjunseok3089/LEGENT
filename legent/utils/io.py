import logging
import json
from colorama import Fore, Style
from datetime import datetime
import os
import zipfile


def log(*args):
    logging.basicConfig(format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger("LEGENT")
    logger.error(*args)


def log_green(arg: str):
    if "<g>" in arg:
        log(arg.replace("<g>", Fore.GREEN).replace("<g/>", Style.RESET_ALL))
    else:
        log(Fore.GREEN + arg + Style.RESET_ALL)


def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_line(file):
    with open(file, "r", encoding="utf-8") as f:
        return f.readline().strip()


def store_json(obj, file):
    with open(file, "w", encoding="utf-8") as f:
        return json.dump(obj, f, ensure_ascii=False, indent=4)


def save_image(image, file, center_mark=False):
    from skimage.io import imsave
    import numpy as np

    if center_mark:
        marked_image = np.copy(image)

        # Define the range of the center mark
        mark_size = 8
        center = (image.shape[0] // 2, image.shape[1] // 2)
        x_start = max(center[0] - mark_size // 2, 0)
        x_end = min(center[0] + mark_size // 2, image.shape[0])
        y_start = max(center[1] - mark_size // 2, 0)
        y_end = min(center[1] + mark_size // 2, image.shape[1])

        # Set the marked area to red
        marked_image[x_start:x_end, y_start:y_end] = [255, 0, 0]
        imsave(file, marked_image, check_contrast=False)
    else:
        imsave(file, image, check_contrast=False)


def load_json_from_toolkit(file):
    import pkg_resources

    # Specify the relative path to the JSON file within the package
    file = pkg_resources.resource_filename("legent", file)
    return load_json(file)


def time_string():
    now = datetime.now()
    formatted_now = now.strftime(r"%Y%m%d-%H%M%S-%f")
    return formatted_now


def scene_string(scene):  # to save tokens or print neatly
    objects_string = ["object_id\tname\tposition_x\tposition_y(vertical distance from ground)\tposition_z"]
    for i, instance in enumerate(scene["instances"]):
        name = instance["prefab"].split("_")[1]
        position = "\t".join([f"{v:.2f}" for v in instance["position"]])
        objects_string.append(f"{i}\t{name}\t{position}")
    return "\n".join(objects_string)


def pack_scene(scene):
    files_to_zip = {}

    store_json(scene, "pack_scene_temp.json")

    for instance in scene["instances"]:
        if os.path.exists(instance["prefab"]):
            files_to_zip.add(instance["prefab"])
    for instance in scene["floors"] + scene["walls"]:
        if "material" in instance and os.path.exists(instance["material"]):
            files_to_zip.add(instance["material"])
        if "material" in instance and os.path.exists(instance["material"]):
            files_to_zip.add(instance["material"])

    output_zip = "packed_scene.zip"

    with zipfile.ZipFile(output_zip, "w") as zipf:
        zipf.write(file, arcname="scene.json")
        for file in files_to_zip:
            zipf.write(file, arcname=file.split("/")[-1])

    os.remove("pack_scene_temp.json")

    log_green(f"created packed scene at <g>{output_zip}</g>")


def unpack_scene(input_file: str):
    dir = input_file.rsplit(".", maxsplit=1)[0]
    if not os.path.exists(dir):
        os.makedirs(dir)
        with zipfile.ZipFile(input_file, "r") as zip_ref:
            zip_ref.extractall(dir)

    scene = load_json(os.path.join(dir, "scene.json"))

    for instance in scene["instances"]:
        new_path = f"{dir}/{instance['prefab'].split('/')[-1]}"
        print(new_path)
        if os.path.exists(new_path):
            instance["prefab"] = new_path
    for instance in scene["floors"] + scene["walls"]:
        if "material" in instance:
            print(new_path)
            new_path = f"{dir}/{instance['material'].split('/')[-1]}"
            if os.path.exists(new_path):
                instance["material"] = new_path
    scene = store_json(scene, os.path.join(dir, "new_scene.json"))
    return scene


def get_latest_folder(root_folder):
    folders = [os.path.join(root_folder, d) for d in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, d))]
    folder = sorted(folders, reverse=True)[0]
    return folder


def get_latest_folder_with_suffix(root_folder, suffix):
    folders = [os.path.join(root_folder, d) for d in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, d)) and d.endswith(suffix)]
    folder = sorted(folders, reverse=True)[0]
    return folder

def find_files_by_extension(directory, extension):
    matching_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                matching_files.append(os.path.join(root, file))
    return matching_files

def parse_ssh(ssh: str):
    ssh_parts = ssh.rsplit(",", maxsplit=1)
    if len(ssh_parts) == 2:
        ssh, password = ssh_parts
    else:
        password = None
    ssh_parts = ssh.rsplit(":", maxsplit=1)
    if len(ssh_parts) == 2:
        ssh, port = ssh_parts
        port = int(port)
    else:
        port = 22
    username, host = ssh.rsplit("@", maxsplit=1)
    return host, port, username, password


class SSHTunnel:
    def __init__(self, remote_host, ssh_port, ssh_username, ssh_password, local_port, remote_port) -> None:
        import paramiko
        from sshtunnel import SSHTunnelForwarder

        # set ssh parameters
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # connect ssh server
        log(f"Connect to {ssh_username}@{remote_host}:{ssh_port}" + f" with password {ssh_password}" if ssh_password else "")
        ssh_client.connect(hostname=remote_host, username=ssh_username, password=ssh_password, port=ssh_port)

        # build ssh tunnel
        tunnel = SSHTunnelForwarder((remote_host, ssh_port), ssh_username=ssh_username, ssh_password=ssh_password, remote_bind_address=("127.0.0.1", remote_port), local_bind_address=("0.0.0.0", local_port))

        tunnel.start()
        log(f"The tunnel has been established: local {tunnel.local_bind_port} <==> remote {remote_port}")
        self.ssh_client = ssh_client
        self.tunnel = tunnel

    def close(self):
        self.tunnel.stop()
        self.ssh_client.close()
