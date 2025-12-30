from src.graph_builder import GraphePERT
from src.pert_calculator import CalculateurPERT
import pandas as pd


def main():
    # Charger et analyser
    graphe = GraphePERT("./data/taches.csv")
    calculateur = CalculateurPERT(graphe)
    calculateur.executer_analyse_complete()

    # Afficher resultats
    calculateur.afficher_resume()

    # Tableau detaille
    df = pd.DataFrame(calculateur.generer_tableau_resultats())
    print("\n" + df.to_string(index=False))


if __name__ == "__main__":
    main()
