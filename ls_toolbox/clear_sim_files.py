import os
import re


sim_files_names_all = ("d3dump", "d3hsp", "d3plot+", "messag", "bndout", "glstat", "spcforc", "elout", "nodout",
                       "part_des", r"status\.out", "d3dump+", "adptmp", "bg_switch", "binout+", "cont_profile.+",
                       "dyna.inc", "group_file", "kill_by_pid", "load_profile.+", "lspost.+", "mes+", "nodelist.+",
                       "process.log")

def clear_sim_files(sim_dir_path: str, sim_files_names: list = sim_files_names_all, verbose: bool = False):
    """
    Clear simulation files in the given directory.
    :param sim_dir_path: Path to the simulation directory.
    """
    for sim_file_name in sim_files_names:
        for file in os.listdir(sim_dir_path):
            try:
                if os.path.isdir(os.path.join(sim_dir_path, file)):
                    continue
                elif re.match(sim_file_name, file):
                    if verbose:
                        print(f"Removing {file}")
                    os.remove(os.path.join(sim_dir_path, file))
            except:
                print(f"Failed to remove {file}")
                pass