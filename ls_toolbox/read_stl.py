import stl
import numpy as np
import json


def read_stl(file_path: str) -> stl.mesh.Mesh:
    """
    Read an stl file and return the mesh.
    :param file_path: Path to the stl file.
    :return: Mesh.
    """
    return stl.mesh.Mesh.from_file(file_path)

def read_obj(file_path: str) -> np.ndarray:
    """
    Read an obj file and return the vertices.
    :param file_path: Path to the obj file.
    :return: Vertices.
    """
    vertices = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('v '):
                vertex = line.split()
                vertices.append([float(vertex[1]), float(vertex[2]), float(vertex[3])])
    return np.array(vertices)

def get_id_from_coords(coords, nodes):
    """
    Get the id of the closest node to the given coordinates.
    :param coords: Coordinates.
    :param nodes: Nodes.
    :return: Node id.
    """
    min_dist = float('inf')
    node_id = None
    for i, node in enumerate(nodes):
        dist = np.linalg.norm(np.array(node) - np.array(coords))
        if dist < min_dist:
            min_dist = dist
            node_id = i
    return node_id


def read_json_landmarks(landmark_file_path: str) -> dict:
    """
    Read a json file containing landmarks and return the landmarks.
    :param landmark_file_path: Path to the json file.
    :return: Landmarks.
    """
    return json.load(open(landmark_file_path))


def read_sml(sml_file_path: str) -> list:
    """
    Read an sml file and return the data.
    :param sml_file_path: Path to the sml file.
    :return: data.
    """
    with open(sml_file_path, 'r') as f:
        data = f.readlines()
    return data

def modify_sml_by_landmark_index(sml_data: list, landmark_name: str, index: int) -> list:
    """
    Modify the landmark's index in the sml data.
    :param sml_data: Sml data.
    :param landmark_name: Landmark name.
    :param index: Index.
    :return: Modified sml data.
    """
    is_landmark = False
    for i, line in enumerate(sml_data):
        if landmark_name in line:
            is_landmark = True
        if is_landmark and "<index>" in line:
            sml_data[i] = f"{sml_data[i].split('<')[0]}<index>{index}</index>\n"
            print(sml_data[i])
            is_landmark = False
            break
    return sml_data
