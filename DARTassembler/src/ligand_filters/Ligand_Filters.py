from tqdm import tqdm

from DARTassembler.src.ligand_extraction.DataBase import LigandDB
from DARTassembler.src.constants.Paths import project_path
from DARTassembler.src.ligand_filters.FilteringStage import FilterStage
from dev.test.Integration_Test import IntegrationTest
from pathlib import Path
import pandas as pd
pd.options.mode.chained_assignment = None   # silence pandas SettingWithCopyWarning
from typing import Union
from DARTassembler.src.assembly.Assembly_Input import LigandFilterInput, _mw, _filter, _ligand_charges, _ligcomp, _coords, \
    _metals_of_interest, _denticities_of_interest, _remove_ligands_with_neighboring_coordinating_atoms, \
    _remove_ligands_with_beta_hydrogens, _strict_box_filter, _acount, _acount_min, _acount_max, _denticities, \
    _ligcomp_atoms_of_interest, _ligcomp_instruction, _mw_min, _mw_max, _graph_hash_wm, _stoichiometry, _min, _max, \
    _md_bond_length, _interatomic_distances, _occurrences, _planarity, _remove_missing_bond_orders, _atm_neighbors, \
    _atom, _neighbors, _smarts_filter, _smarts, _should_be_present





class LigandFilters(object):

    def __init__(self, filepath: Union[str, Path], max_number: Union[int, None] = None):
        self.filepath = filepath
        self.max_number = max_number
        self.input = LigandFilterInput(path=self.filepath)

        self.ligand_db_path = self.input.ligand_db_path
        self.output_ligand_db_path = self.input.output_ligand_db_path
        self.output_info = self.input.output_filtered_ligands
        self.filters = self.input.filters

        # Make a directory for the output if specified
        if self.output_info:
            outdirname = f'info_{self.output_ligand_db_path.with_suffix("").name}'
            self.outdir = Path(self.output_ligand_db_path.parent, outdirname)   # directory for full output
            self.outdir.mkdir(parents=True, exist_ok=True)
            self.xyz_outdir = Path(self.outdir, 'concat_xyz')                   # directory for concatenated xyz files
            self.xyz_outdir.mkdir(parents=True, exist_ok=True)

        self.filter_tracking = []

    def get_filtered_db(self) -> LigandDB:
        print(f"Filtering ligand database: {self.ligand_db_path} --> {self.output_ligand_db_path}...")
        db = LigandDB.load_from_json(
            self.ligand_db_path,
            n_max=self.max_number,
        )

        self.Filter = FilterStage(db)
        self.n_ligands_before = len(self.Filter.database.db)
        self.df_all_ligands = self.get_ligand_df()
        self.df_all_ligands['Filter'] = None    # initialize column for filter tracking
        if self.output_info:
            self.all_xyz_strings = {ligand_id: ligand.get_xyz_file_format_string(comment='placeholder', with_metal=True) for ligand_id, ligand in self.Filter.database.db.items()}   # save xyz strings for outputting later and keep a placeholder comment for replacing later

        # mandatory filters
        self.Filter.filter_charge_confidence(filter_for="confident")
        self.Filter.filter_unconnected_ligands()

        for idx, filter in tqdm(enumerate(self.filters), desc="Applying filters", unit=" filters"):
            filtername = filter[_filter]
            unique_filtername = f"Filter {idx+1:02d}: {filtername}"    # name for printing filters for the user
            n_ligands_before = len(self.Filter.database.db)

            if filtername == _stoichiometry:
                self.Filter.stoichiometry_filter(stoichiometry=filter[_stoichiometry], denticities=filter[_denticities])

            if filtername == _denticities_of_interest:
                self.Filter.denticity_of_interest_filter(denticity_of_interest=filter[_denticities_of_interest])

            elif filtername == _graph_hash_wm:
                self.Filter.graph_hash_with_metal_filter(graph_hashes_with_metal=filter[_graph_hash_wm])

            elif filtername == _remove_ligands_with_neighboring_coordinating_atoms:
                if filter[_remove_ligands_with_neighboring_coordinating_atoms]:
                    self.Filter.filter_neighbouring_coordinating_atoms()

            elif filtername == _remove_ligands_with_beta_hydrogens:
                if filter[_remove_ligands_with_beta_hydrogens]:
                    self.Filter.filter_betaHs()

            elif filtername == _strict_box_filter:
                if filter[_strict_box_filter]:
                    self.Filter.box_excluder_filter()

            # Denticity dependent filters
            elif filtername == _acount:
                self.Filter.filter_atom_count(min=filter[_acount_min], max=filter[_acount_max], denticities=filter[_denticities])

            elif filtername == _ligcomp:
                self.Filter.filter_ligand_atoms(
                    denticity=filter[_denticities],
                    atoms_of_interest=filter[_ligcomp_atoms_of_interest],
                    instruction=filter[_ligcomp_instruction])

            elif filtername == _metals_of_interest:
                self.Filter.metals_of_interest_filter(
                    denticity=filter[_denticities],
                    metals_of_interest=filter[_metals_of_interest])

            elif filtername == _ligand_charges:
                self.Filter.filter_ligand_charges(
                    denticity=filter[_denticities],
                    charge=filter[_ligand_charges])

            elif filtername == _coords:
                self.Filter.filter_coordinating_group_atoms(
                    denticity=filter[_denticities],
                    atoms_of_interest=filter[_ligcomp_atoms_of_interest],
                    instruction=filter[_ligcomp_instruction])

            elif filtername == _mw:
                self.Filter.filter_molecular_weight(
                    min=filter[_mw_min],
                    max=filter[_mw_max],
                    denticities=filter[_denticities]
                )
            elif filtername == _occurrences:
                self.Filter.filter_occurrences(
                    min=filter[_min],
                    max=filter[_max],
                    denticities=filter[_denticities]
                )
            elif filtername == _md_bond_length:
                self.Filter.filter_metal_donor_bond_lengths(
                    min=filter[_min],
                    max=filter[_max],
                    denticities=filter[_denticities]
                )
            elif filtername == _interatomic_distances:
                self.Filter.filter_interatomic_distances(
                    min=filter[_min],
                    max=filter[_max],
                    denticities=filter[_denticities]
                )
            elif filtername == _planarity:
                self.Filter.filter_planarity(
                    min=filter[_min],
                    max=filter[_max],
                    denticities=filter[_denticities]
                )
            elif filtername == _stoichiometry:
                self.Filter.stoichiometry_filter(
                    stoichiometry=filter[_stoichiometry],
                    denticities=filter[_denticities]
                )
            elif filtername == _remove_missing_bond_orders:
                self.Filter.filter_missing_bond_orders(
                    denticities=filter[_denticities]
                )
            elif filtername == _atm_neighbors:
                self.Filter.filter_atomic_neighbors(
                    atom=filter[_atom],
                    neighbors=filter[_neighbors],
                    denticities=filter[_denticities]
                )
            elif filtername == _smarts_filter:
                self.Filter.filter_smarts_substructure_search(
                    smarts=filter[_smarts],
                    should_be_present=filter[_should_be_present],
                    denticities=filter[_denticities]
                )
            else:
                raise ValueError(f"Unknown filter: {filtername}")

            # To the dataframe with all ligands, add a column specifying which filter was applied to filter this ligand. This is important for outputting a csv with all filtered out ligands later.
            ligand_was_filtered = ~self.df_all_ligands.index.isin(self.Filter.database.db.keys()) & (self.df_all_ligands['Filter'].isna())
            self.df_all_ligands['Filter'].loc[ligand_was_filtered] = unique_filtername

            # If specified, save concatenated xyz files of all filtered out ligands
            if self.output_info:
                filtered_ligand_ids = self.df_all_ligands.index[ligand_was_filtered]
                self.save_filtered_ligands_xyz_files(filtered_ligand_ids, unique_filtername)

            n_ligands_after = len(self.Filter.database.db)
            self.filter_tracking.append({
                "filter": filtername,
                "unique_filtername": unique_filtername,
                "n_ligands_before": n_ligands_before,
                "n_ligands_after": n_ligands_after,
                "n_ligands_removed": n_ligands_before - n_ligands_after,
                "full_filter_options": {name: option for name, option in filter.items() if name != _filter}
            })

        self.n_ligands_after = len(self.Filter.database.db)

        # Nicen up the ligand df
        self.df_all_ligands['Filter'].fillna('Passed', inplace=True)      # fill in 'Passed' for ligands that were not filtered out
        self.df_all_ligands.set_index('Ligand ID', inplace=True)    # set index to ligand ID, making sure that the column in the csv is named 'Ligand ID'
        columns = ['Filter'] + [col for col in self.df_all_ligands.columns if col != 'Filter']
        self.df_all_ligands = self.df_all_ligands[columns]                # move 'Filter' column to the front
        self.df_all_ligands = self.df_all_ligands.sort_values(by='Filter')# sort by filter name

        return self.Filter.database

    def save_filtered_ligands_xyz_files(self, filtered_ligand_ids: list, unique_filtername: str):
        """
        Save concatenated xyz files of all filtered out ligands for each filter.
        """
        xyz_filename = f"concat_{unique_filtername.replace(' ', '')}.xyz"
        xyz_filepath = Path(self.xyz_outdir, xyz_filename)
        with open(xyz_filepath, 'w') as f:
            for ligand_id in filtered_ligand_ids:
                xyz_string = self.all_xyz_strings[ligand_id]
                comment = f"Ligand ID: {ligand_id}. Filtered out by {unique_filtername}."
                xyz_string = xyz_string.replace('placeholder', comment)  # replace placeholder comment with actual comment
                f.write(xyz_string)

        return

    def get_filter_tracking_string(self) -> str:
        output= "==================================== FILTERS OVERVIEW ====================================\n"
        df_filters = pd.DataFrame(self.filter_tracking)
        df_filters = df_filters[['unique_filtername', 'n_ligands_removed', 'n_ligands_after', 'full_filter_options']]
        df_filters = df_filters.rename(columns={'n_ligands_removed': 'Ligands removed', 'n_ligands_after': 'Ligands passed', 'unique_filtername': 'Filters', 'full_filter_options': 'Filter options'})

        df_filters = df_filters.set_index('Filters')
        output += df_filters.to_string(justify='center', index_names=False) + '\n\n'

        # Count denticities of all passed ligands
        denticity_count = pd.Series(
            [lig.denticity for lig in self.Filter.database.db.values()]).value_counts().to_dict()
        dent_output = ', '.join(sorted([f'{dent}: {count}' for dent, count in denticity_count.items()]))

        output += "===========   Total   ===========\n"
        output += f"Before filtering:  {self.n_ligands_before} ligands\n"
        output += f"Filtered out:      {self.n_ligands_before - self.n_ligands_after} ligands\n"
        output += f"Passed:            {self.n_ligands_after} ligands\n"
        output += f"Denticities:       {dent_output}\n"

        # If the number of ligands after filtering is small, print them explicitly
        if self.n_ligands_after <= 10:
            stoichiometries = ','.join([ligand.stoichiometry for ligand in self.Filter.database.db.values()])
            output += f'Passed ligands:    {stoichiometries}\n'

        output += "\nDone filtering!\n"
        output += f"Filtered ligand database with {self.n_ligands_after} entries was saved to `{self.output_ligand_db_path.name}`."

        return output

    def save_filtered_ligand_db(self):
        filtered_db = self.get_filtered_db()

        if not self.output_ligand_db_path.parent.exists():
            self.output_ligand_db_path.parent.mkdir(parents=True)
        filtered_db.to_json(self.output_ligand_db_path, json_lines=True)

        self.output = self.get_filter_tracking_string()

        # Optionally output filtered ligands info
        if self.output_info:
            self.save_filtered_ligands_output()

        print(self.output)

        return

    def save_filtered_ligands_output(self):

        # Save stdout output of filtering to info directory
        with open(Path(self.outdir, "filters.txt"), 'w') as f:
            f.write(self.get_filter_tracking_string())

        # Save a csv with an overview of all ligands to info directory
        self.df_all_ligands.to_csv(Path(self.outdir, "ligands_overview.csv"), index=True)

        # Save concatenated xyz files
        modes = ['Passed'] + [filter['unique_filtername'] for filter in self.filter_tracking]
        for mode in modes:
            filtered_ligand_ids = self.df_all_ligands.index[self.df_all_ligands['Filter'] == mode]
            xyz_filename = f"concat_{mode.replace(' ', '')}.xyz"
            xyz_filepath = Path(self.xyz_outdir, xyz_filename)
            with open(xyz_filepath, 'w') as f:
                for ligand_id in filtered_ligand_ids:
                    xyz_string = self.all_xyz_strings[ligand_id]
                    comment = f"Ligand ID: {ligand_id}. {mode}."
                    xyz_string = xyz_string.replace('placeholder', comment)  # replace placeholder comment with actual comment
                    f.write(xyz_string)

    def get_ligand_df(self):
        db = self.Filter.database
        ligands = {uname: ligand.get_ligand_output_info(max_entries=5) for uname, ligand in db.db.items()}
        return pd.DataFrame.from_dict(ligands, orient='index')

    def save_ligand_info_csv(self):
        self.df_ligand_info = self.get_ligand_df()
        outpath = Path(self.output_ligand_db_path.parent, "ligand_info.csv")
        self.df_ligand_info.to_csv(outpath, index=False)

        return



if __name__ == "__main__":
    ligand_filter_path = project_path().extend(*'testing/integration_tests/ligand_filters/data_input/ligandfilters.yml'.split('/'))
    max_number = 1000


    filter = LigandFilters(filepath=ligand_filter_path, max_number=max_number)
    filter.save_filtered_ligand_db()

