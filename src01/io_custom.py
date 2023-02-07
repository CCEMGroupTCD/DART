"""
Utility functions for input and output.
"""
import json
from src01.Molecule import RCA_Molecule, RCA_Ligand, RCA_Complex
from tqdm import tqdm
import numpy as np
from typing import Union
from pathlib import Path
class NumpyEncoder(json.JSONEncoder):
    """Special json encoder for numpy types. This is important to use in json.dump so that if json encounters a np.array, it converts it to a list automatically, otherwise errors arise. Use like this:
    dumped = json.dump(dic, cls=NumpyEncoder)
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def load_json(path: Union[str, Path]) -> dict:
    with open(path, 'r') as file:
        db = json.load(file)

    return db


def save_json(db: dict, path: Union[str, Path], **kwargs):
    with open(path, 'w') as file:
        json.dump(db, file, cls=NumpyEncoder, **kwargs)

    return


def check_molecule_value(output: str):
    possible_values = ['dict', 'class']
    if not output in possible_values:
        raise ValueError(f'Unknown value for `output`: {output}')

    return


def load_complex_db(path: Union[str, Path], molecule: str='dict', n_max=None) -> dict:

    check_molecule_value(molecule)
    db = load_json(path)

    if not n_max is None:
        db = {key: val for key, val in db.items()}

    if molecule == 'class':
        db = {name: RCA_Complex.read_from_mol_dict(mol) for name, mol in db.items()}
    return db


def load_full_ligand_db(path: Union[str, Path], molecule: str = 'dict') -> dict:
    check_molecule_value(molecule)
    db = load_json(path)
    if molecule == 'class':
        db = {name: RCA_Ligand.read_from_mol_dict(mol) for name, mol in db.items()}
    return db


def load_unique_ligand_db(path: Union[str, Path]) -> dict:
    return load_json(path)


def save_complex_db(db: dict, path: Union[str, Path]):
    save_json(db, path)


def save_full_ligand_db(db: dict, path: Union[str, Path]):
    save_json(db, path)


def save_unique_ligand_db(db: dict, path: Union[str, Path]):
    save_json(db, path)
