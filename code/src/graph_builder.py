import networkx as nx
import pandas as pd


class GraphePERT:
    """
    Classe pour construire et manipuler un graphe PERT/CPM
    """

    def __init__(self, fichier_csv: str | None = None):
        """
        Args:
            fichier_csv: Chemin vers le fichier CSV des taches
        """
        self.graphe = nx.DiGraph()
        self.taches = {}

        if fichier_csv:
            self.charger_donnees(fichier_csv)

    def charger_donnees(self, fichier_csv: str):
        """
        Charge le donnees depuis un fichier csv

        Args:
            fichier_csv: Chemin vers le fichier CSV des taches
        """
        df = pd.read_csv(fichier_csv)
        df.columns = df.columns.str.strip()

        for _, row in df.iterrows():
            code = str(row["code"]).strip()
            nom = str(row["nom"])
            duree = int(row["duree"])

            # Traiter les predecesseurs
            pred_str = str(row["predecesseurs"])
            if pred_str and pred_str != "nan":
                predecesseurs = [p.strip() for p in pred_str.split(",")]
            else:
                predecesseurs = []

            self.ajouter_tache(code, nom, duree, predecesseurs)

    def ajouter_tache(
        self, code: str, nom: str, duree: int, predecesseurs: list[str] | None = None
    ):
        """
        Ajoute une tache au graphe

        Args:
            code: Code de la tache (ex: 'A')
            nom: Nom descriptif de la tache
            duree: Duree en minutes
            predecesseurs: Liste des codes des taches predecesseurs
        """
        if predecesseurs is None:
            predecesseurs = []

        # Stocker les informations de la tache
        self.taches[code] = {"nom": nom, "duree": duree, "predecesseurs": predecesseurs}

        # Ajouter le noeud au graphe
        self.graphe.add_node(code, duree=duree, nom=nom)

        # Ajouter les arcs depuis le predecesseurs
        for pred in predecesseurs:
            self.graphe.add_edge(pred, code)

    def obtenir_taches_initiales(self) -> list[str]:
        """
        Retourne les taches sans predecesseurs

        Returns:
            Liste des codes des taches initiales
        """
        return [code for code, data in self.taches.items() if not data["predecesseurs"]]

    def obtenir_taches_finales(self) -> list[str]:
        """
        Retourne les taches sans successeurs

        Returns:
            Liste des codes des taches finales
        """
        return [
            node for node in self.graphe.nodes() if self.graphe.out_degree(node) == 0
        ]

    def valider_graphe(self) -> tuple[bool, str]:
        """
        Valide que le graphe est un DAG sans cycles

        Returns:
            Tuple (est_valide, message)
        """
        if not nx.is_directed_acyclic_graph(self.graphe):
            return False, "Le graphe contient des cylces"

        if not nx.is_weakly_connected(self.graphe):
            return False, "Le graphe n'est pas connexe"

        return True, "Graphe Valide"

    def obtenir_info_tache(self, code: str) -> dict:
        """
        Retourne les informations d'une tache

        Args:
            code: Code de la tache

        Returns:
            Dictionnaire avec les informations de la tache
        """
        return self.taches.get(code, {})

    def afficher_resume(self):
        """
        Affiche un resume du graphe
        """
        print(f"Nombre de taches: {len(self.taches)}")
        print(f"Nombre d'arcs: {self.graphe.number_of_edges()}")
        print(f"\nTaches initiales: {', '.join(self.obtenir_taches_initiales())}")
        print(f"Taches finales: {', '.join(self.obtenir_taches_finales())}")

        _, message = self.valider_graphe()
        print(f"\nValidation: {message}")
