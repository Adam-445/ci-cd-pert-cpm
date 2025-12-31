import networkx as nx


class CalculateurPERT:
    """
    Classe pour effectur les calculs PERT/CPm
    """

    def __init__(self, graphe_pert):
        """
        Args:
            graphe_pert: Instance de GraphePERT
        """
        self.graphe_pert = graphe_pert
        self.graphe = graphe_pert.graphe
        self.dates_tot = {}
        self.dates_tard = {}
        self.marges = {}
        self.marges_libres = {}
        self.chemin_critique = []
        self.duree_totale = 0

    def calculer_dates_au_plus_tot(self) -> dict[str, dict[str, int]]:
        """
        Calcul les dates de debut (ES) et fin (EF) au plus tot

        Returns:
            Dictionnaire {code_tache: {'ES': val, 'EF': val}}
        """
        # Tri topologique pour traiter les taches dans l'ordre
        ordre_topo = list(nx.topological_sort(self.graphe))

        for tache in ordre_topo:
            duree = self.graphe.nodes[tache]["duree"]

            # Predecesseurs de la tache
            predecesseurs = list(self.graphe.predecessors(tache))

            if not predecesseurs:
                # Tache initiale
                es = 0
            else:
                # ES = max des EF des predecesseurs
                es = max(self.dates_tot[pred]["EF"] for pred in predecesseurs)

            ef = es + duree

            self.dates_tot[tache] = {"ES": es, "EF": ef}

        # La duree totale est le max des EF
        self.duree_totale = max(data["EF"] for data in self.dates_tot.values())

        return self.dates_tot

    def calculer_dates_au_plus_tard(self) -> dict[str, dict[str, int]]:
        """
        Calcule les dates de debut (LS) et fin (LF) au plus tard

        Returns:
            Dictionnaire {code_tache: {'LS': val, 'LF': val}}
        """
        # Tri topologique inverse
        ordre_topo_inverse = list(reversed(list(nx.topological_sort(self.graphe))))

        for tache in ordre_topo_inverse:
            duree = self.graphe.nodes[tache]["duree"]

            # Successeurs de la tache
            successeurs = list(self.graphe.successors(tache))

            if not successeurs:
                # Tache finale
                lf = self.duree_totale
            else:
                # LF = min des LS des successeurs
                lf = min(self.dates_tard[succ]["LS"] for succ in successeurs)

            ls = lf - duree

            self.dates_tard[tache] = {"LS": ls, "LF": lf}

        return self.dates_tard

    def calculer_marges(self) -> dict[str, int]:
        """
        Calcule la marge pour chaque tache
        Marge = LS - ES = LF - EF

        Returns:
            Dictionnaire {code_tache: marge}
        """
        for tache in self.graphe.nodes():
            marge = self.dates_tard[tache]["LS"] - self.dates_tot[tache]["ES"]
            self.marges[tache] = marge

        return self.marges

    def calculer_marges_libres(self) -> dict[str, int]:
        """
        Calcule la marge libre pour chaque tache
        Marge libre = min(ES des successeurs) - EF de la tache

        Returns:
            Dictionnaire {code_tache: marge_libre}
        """
        for tache in self.graphe.nodes():
            successeurs = list(self.graphe.successors(tache))

            if not successeurs:
                # Tache finale: FF = TF (pas de successeurs a retarder)
                ff = self.marges[tache]
            else:
                # FF = min des ES des successeurs - EF de cette tache
                min_es_successeurs = min(
                    self.dates_tot[succ]["ES"] for succ in successeurs
                )
                ff = min_es_successeurs - self.dates_tot[tache]["EF"]

            self.marges_libres[tache] = ff

        return self.marges_libres

    def identifier_chemin_critique(self) -> list[str]:
        """
        Identifie le chemin critique (taches avec marge = 0)

        Returns:
            Liste ordonnee des taches du chemin critique
        """
        # Taches critiques sont celles avec marge = 0
        taches_critiques = [tache for tache, marge in self.marges.items() if marge == 0]

        # Construire le sous-graphe des taches critiques
        sous_graphe = self.graphe.subgraph(taches_critiques)

        # Trouver un chemin du debut a la fin
        taches_initiales = self.graphe_pert.obtenir_taches_initiales()
        taches_finales = self.graphe_pert.obtenir_taches_finales()

        for debut in taches_initiales:
            for fin in taches_finales:
                if debut in sous_graphe and fin in sous_graphe:
                    try:
                        chemin = nx.shortest_path(sous_graphe, debut, fin)
                        if chemin:
                            self.chemin_critique = chemin
                            return chemin
                    except nx.NetworkXNoPath:
                        continue

        return []

    def executer_analyse_complete(self) -> dict:
        """
        Execute l'analyse PERT complete

        Returns:
            Dictionnaire avec tous les resultats
        """
        # Etape 1: Dates au plus tot
        self.calculer_dates_au_plus_tot()

        # Etape 2: Dates au plus tard
        self.calculer_dates_au_plus_tard()

        # Etape 3: Marges Totales
        self.calculer_marges()

        # Etape 4: Marges Libres
        self.calculer_marges_libres()

        # Etape 5: Chemin critique
        self.identifier_chemin_critique()

        return {
            "duree_totale": self.duree_totale,
            "dates_tot": self.dates_tot,
            "dates_tard": self.dates_tard,
            "marges": self.marges,
            "marges_libres": self.marges_libres,
            "chemin_critique": self.chemin_critique,
        }

    def generer_tableau_resultats(self) -> list[dict]:
        """
        Genere un tableau des resultats

        Returns:
            Liste de dictionnaires pour chaque tache
        """
        resultats = []

        for tache in nx.topological_sort(self.graphe):
            info = self.graphe_pert.obtenir_info_tache(tache)

            ligne = {
                "Code": tache,
                "Nom": info["nom"],
                "Duree": info["duree"],
                "ES": self.dates_tot[tache]["ES"],
                "EF": self.dates_tot[tache]["EF"],
                "LS": self.dates_tard[tache]["LS"],
                "LF": self.dates_tard[tache]["LF"],
                "Marge": self.marges[tache],
                "Marge_Libre": self.marges_libres[tache],
                "Critique": "Oui" if self.marges[tache] == 0 else "Non",
            }

            resultats.append(ligne)

        return resultats

    def afficher_resume(self):
        """
        Affiche un resume des resultats
        """
        print(f"Duree totale du projet: {self.duree_totale} minutes")
        print(f"Chemin critique: {' -> '.join(self.chemin_critique)}")
        print(f"Nombre de taches critiques: {len(self.chemin_critique)}")

        print("\nTaches non-critiques (avec marge):")
        for tache, marge in self.marges.items():
            if marge > 0:
                nom = self.graphe_pert.obtenir_info_tache(tache)["nom"]
                marge_libre = self.marges_libres[tache]
                print(
                    f"  {tache} ({nom}): {marge} minutes de marge, "
                    f"{marge_libre} min marge libre"
                )
