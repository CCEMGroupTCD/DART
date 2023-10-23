"""
This module reads in a ligand db from file and saves a .csv file with an overview of the ligands.
"""
from typing import Union
from pathlib import Path
from DARTassembler.src.ligand_extraction.DataBase import LigandDB

def get_ligand_csv_output_path(output_path: Union[str, Path], input_path: Union[str, Path]):
    """
    Save to csv. If no output path is specified, save to the same directory as the input file with the same name but with the .csv extension.
    """
    if output_path is None:
        if str(input_path).endswith('.csv'):
            raise ValueError(f"Input path {input_path} ends with .csv. Please specify an output path explicitly.")
        else:
            output_path = Path(input_path).with_suffix('.csv')

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    return output_path

def make_ligand_db_csv(input_path: Union[str, Path], output_path: Union[str, Path, None] = None, nmax: Union[int, None] = None):
    """
    Reads in the given ligand database and saves a .csv file with the most important information about all ligands in the database.
    :param input_path: Path to the ligand database
    :param output_path: Path to the output .csv file. If None, the output file will be saved in the same directory as the input file with the same name as the input file but with the .csv extension.
    :param nmax: Maximum number of ligands to be read in from the initial full ligand database. If None, all ligands are read in. This is useful for testing purposes.
    :return: LigandDB object
    """
    db = LigandDB.load_from_json(input_path, n_max=nmax)

    output_path = get_ligand_csv_output_path(output_path, input_path)
    db.save_reduced_csv(output_path)

    return db