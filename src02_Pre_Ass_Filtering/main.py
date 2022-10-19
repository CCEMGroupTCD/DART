from src.process import LigandDatabase
from src02_Pre_Ass_Filtering.FilteringStage import FilterHandler
import pickle


if __name__ == "__main__":

    # Load DB
    with open("../data/LigandDatabases/ligand_db.pickle", "rb") as handle:
        ligand_db = pickle.load(handle)
    print("Database loaded")

    #
    # Init FilterStage
    Filter = FilterHandler(ligand_db)
    print("Filter initialized")

    #
    # Run the filtering
    Filter.filter_N_and_O_functional_groups()
    Filter.filter_betaHs()
    Filter.filter_duplicates()
    print("All filters applied")

    #
    # Safe the progress
    Filter.safe(safe_path="../data/LigandDatabases/ligand_db_w_filters.pickle")
    print("Filtered and safed")
