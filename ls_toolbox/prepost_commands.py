import os, sys
import numpy as np
import subprocess


NCPU = os.cpu_count() - 1  # Number of CPUs to use for LS-Dyna
VERBOSE = False  # If True, the LS-PrePost and LS-Dyna output will be displayed in the console

LS_PREPOST_PATH = None  # Path to the LS-PrePost executable
LS_DYNA_PATH = None  # Path to the LS-Dyna executable

# Get the LS-PrePost and LS-Dyna paths from the environment variables
try:
    LS_PREPOST_PATH = os.environ["LSPREPOST_PATH"]
    LS_DYNA_PATH = os.environ["LSDYNA_PATH"]
except:
    pass

if LS_PREPOST_PATH is None:
    print("Please set the LSPREPOST_PATH variable to the path of the LS-PrePost executable.")
    print("Command: setx LSPREPOST_PATH \"path_to_lsprepost\"   (Don't forget the \"\" around the path)")
    sys.exit(1)

if LS_DYNA_PATH is None:
    print("Please set the LSDYNA_PATH variable to the path of the LS-Dyna executable.")
    print("Command: setx LSDYNA_PATH \"path_to_lsdyna\"   (Don't forget the \"\" around the path)")
    sys.exit(1)



fringe_nb_dict = {
    "max principal strain": 73,
    "strain energy": 529
}

def run_prepost(commands_path, clean_generated_files=True, verbose=VERBOSE):
    """
    Run LS-PrePost with the given commands file.
    :param commands_path: Path to the commands file.
    :param ls_prepost_path: Path to the LS-PrePost executable.
    :param clean_generated_files: If True, the ls prepost generated files will be deleted after the execution.
    :param verbose: If True, the LS-PrePost output will be displayed in the console.
    :return: None
    """
    try:
        if verbose:
            subprocess.check_call(f"\"{LS_PREPOST_PATH}\" -nographics c={commands_path}", shell=True)
        else:
            with open(os.devnull, 'w') as devnull:
                subprocess.check_call(f"\"{LS_PREPOST_PATH}\" -nographics c={commands_path}", shell=True, stdout=devnull, stderr=devnull)

    except:
        pass
    if clean_generated_files:
        try:
            os.remove("lspost.cfile")
        except:
            pass
        try:
            os.remove("lspost.msg")
        except:
            pass

def extract_nodalcoords_from_file(file_path):
    """

    Extract nodal value (strain, stress, etc.) from text file.
    :param file_path: Path to the file containing the nodes' ids and value.
    :param time: if not None, returns only the value at the specified time (nearest time available in file).
    :return: Dictionary {time: {node_id: value}}
    """
    node_id_len = 8  # Number of characters for the node id in the file
    coord_len = 16  # Number of characters for the coordinates in the file
    node_dict_values = {}
    with open(file_path, 'r') as f:
        is_node = False
        while True:
            line = f.readline()
            if not line:
                break

            if "TIME_VALUE" in line:
                time = float(line.split("=")[-1])
                node_dict_values[time] = {}
                line = f.readline()
                while line[0] == "$":
                    line = f.readline()
                is_node = True

            if is_node:
                if "NODE" in line:
                    continue
                if "*END" in line:
                    is_node = False
                    continue
                try:
                    node_id = int(line[:node_id_len])
                    x = float(line[node_id_len:node_id_len + coord_len])
                    y = float(line[node_id_len + coord_len:node_id_len + 2 * coord_len])
                    z = float(line[node_id_len + 2 * coord_len:node_id_len + 3 * coord_len])
                    node_dict_values[time][node_id] = [x, y, z]
                except:
                    print(f"Error while reading line: {line}")
                    continue

    return node_dict_values

def extract_nodalvalue_from_file(file_path, variable_length=10):
    """

    Extract nodal value (strain, stress, etc.) from text file.
    :param file_path: Path to the file containing the nodes' ids and value.
    :param time: if not None, returns only the value at the specified time (nearest time available in file).
    :return: Dictionary {time: {node_id: value}}
    """
    variable_length = 10  # Character length of variables
    node_dict_values = {}
    with open(file_path, 'r') as f:
        is_node = False
        while True:
            line = f.readline()
            if not line:
                break

            if "TIME_VALUE" in line:
                time = float(line.split("=")[-1])
                node_dict_values[time] = {}
                line = f.readline()
                while line[0] == "$":
                    line = f.readline()
                is_node = True

            if is_node:
                if "*END" in line:
                    is_node = False
                    continue
                try:
                    node_id = int(line[:variable_length])
                    value = float(line[variable_length:2*variable_length])
                    node_dict_values[time][node_id] = value
                except:
                    print(f"Error while reading line: {line}")
                    continue

    return node_dict_values

def get_nodal_results(d3plot_path, part_id=1400021, fringe_nb=73):
    """
    Get the nodal results of a part in a d3plot file.
    :param d3plot_path: Path to the d3plot file.
    :param part_id: Part id.
    :param fringe_nb: Fringe number corresponding to the desired results.
    :return: Dictionary {time: {node_id: value}}
    """
    text = f"""
    open d3plot "{d3plot_path}"
    genselect target part
    selectpart select 1
    selectpart on {part_id}
    selectpart select 0
    range avgfrng node
    fringe {fringe_nb}
    pfringe
    output "max_principal_strain_{part_id}_nodal.txt" 1:9999 1 0 1 0 0 0 0 0 1 0 0 0 0 0 1.000000 0 0
    """
    with open("commands_temp.txt", "w") as file:
        file.write(text)

    run_prepost("commands_temp.txt")
    os.remove("commands_temp.txt")

    values = extract_nodalvalue_from_file(f"max_principal_strain_{part_id}_nodal.txt")
    os.remove(f"max_principal_strain_{part_id}_nodal.txt")

    return values

def get_nodes_coords(d3plot_path, part_id=1400021, state="1:9999"):
    text = f"""
open d3plot "{d3plot_path}"
genselect target part
selectpart select 1
selectpart on {part_id}
selectpart select 0
output "node_coords_{part_id}.txt" {state} 1 0 1 0 1 0 0 0 0 0 0 0 0 0 1.000000 0 0
"""
    with open("commands_temp.txt", "w") as file:
        file.write(text)

    run_prepost("commands_temp.txt")
    os.remove("commands_temp.txt")

    node_coords = extract_nodalcoords_from_file(f"node_coords_{part_id}.txt")
    os.remove(f"node_coords_{part_id}.txt")
    # Array [[node_id, x, y, z]] for a specific state:
    # ref_coords = np.array([(k, sum(v)) for k, v in node_coords[state].items()])

    return node_coords

def create_node_set(command_file, node_ids, set_id):
    """
    Create a node set.
    :param command_file: Path to the command file.
    :param node_ids: List of node ids.
    :param set_id: Set id.
    """
    with open(command_file, "w+") as file:
        file.write("genselect clear\n")
        for node_id in node_ids:
            file.write(f"genselect node add node {node_id}\n")
        file.write(f"setnode createset {set_id} 1 0 0 0 0\n")

def run_lsdyna(dyna_file, ncpu=NCPU, verbose=VERBOSE):
    """
    Run LS-Dyna.
    :param dyna_file: Path to the LS-Dyna file.
    :param ncpu: Number of CPUs to use.
    :param verbose: If True, the LS-Dyna output will be displayed in the console.
    :return: None
    """
    memory="415m"
    if verbose:
        subprocess.check_call(f"{LS_DYNA_PATH} i={dyna_file} ncpu={ncpu} memory={memory}", shell=True, cwd=os.path.dirname(dyna_file))
    else:
        with open(os.devnull, 'w') as devnull:
            subprocess.check_call(f"{LS_DYNA_PATH} i={dyna_file} ncpu={ncpu} memory={memory}", shell=True, cwd=os.path.dirname(dyna_file), stdout=devnull, stderr=devnull)
