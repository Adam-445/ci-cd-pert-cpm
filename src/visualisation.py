import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Patch


from graph_builder import GraphePERT
from pert_calculator import CalculateurPERT

class VisualisateurPERT:
    def __init__(self, calculateur):
        self.calc = calculateur
        self.graphe = calculateur.graphe
        self.gp = calculateur.graphe_pert

    def _calculer_positions(self):
        """Calcule les positions hierarchiques basees sur le temps"""
        # Calculer niveaux
        niveaux = {}
        for node in nx.topological_sort(self.graphe):
            preds = list(self.graphe.predecessors(node))
            niveaux[node] = max([niveaux[p] for p in preds], default=-1) + 1

        # Grouper par niveau
        noeuds_par_niveau = {}
        for node, niveau in niveaux.items():
            noeuds_par_niveau.setdefault(niveau, []).append(node)

        # Positionner
        resultats = self.calc.executer_analyse_complete()
        dates_tot = resultats["dates_tot"]
        pos = {}
        for niveau, noeuds in noeuds_par_niveau.items():
            for i, node in enumerate(sorted(noeuds)):
                x = (dates_tot[node]["ES"] + dates_tot[node]["EF"]) / 2
                y = (i - (len(noeuds) - 1) / 2) * 2.5
                pos[node] = (x, y)

        return pos

    def dessiner_pert(self, fichier_sortie="./rapport/figures/graphe_pert.png"):
        """Génère le graphe PERT circulaire avec chemin critique et labels [ES-EF]."""
        fig, ax = plt.subplots(figsize=(16, 9))
        chemin = self.calc.chemin_critique
        dates_tot = self.calc.dates_tot
        pos = self._calculer_positions()

        # Dessin des Arcs
        arcs_critiques = [(chemin[i], chemin[i + 1]) for i in range(len(chemin) - 1)]
        nx.draw_networkx_edges(self.graphe, pos, edgelist=[e for e in self.graphe.edges() if e not in arcs_critiques],
                               edge_color="gray", width=1.5, alpha=0.5, ax=ax, node_size=3500)
        nx.draw_networkx_edges(self.graphe, pos, edgelist=arcs_critiques,
                               edge_color="red", width=4, ax=ax, node_size=3500)

        # Dessin des Noeuds
        couleurs = ["lightcoral" if n in chemin else "lightblue" for n in self.graphe.nodes()]
        bordures = ["darkred" if n in chemin else "darkblue" for n in self.graphe.nodes()]
        nx.draw_networkx_nodes(self.graphe, pos, node_color=couleurs, edgecolors=bordures, 
                               linewidths=2.5, node_size=3500, ax=ax)

        # Labels formatés : Nom, Durée et Intervalle [ES-EF]
        labels = {n: f"{n}\n{self.graphe.nodes[n]['duree']}min\n[{dates_tot[n]['ES']}-{dates_tot[n]['EF']}]" 
                  for n in self.graphe.nodes()}
        nx.draw_networkx_labels(self.graphe, pos, labels, font_size=8, font_weight="bold", ax=ax)

        # Grille temporelle
        for t in range(0, int(self.calc.duree_totale) + 1, 10):
            ax.axvline(x=t, color="lightgray", linestyle="--", alpha=0.3, zorder=0)
        
        ax.set_title("Réseau PERT - Analyse du Chemin Critique", fontsize=15, fontweight="bold", pad=20)
        ax.set_xlabel("Temps (minutes)", fontsize=12)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.get_yaxis().set_visible(False)

        # Légende
        legende = [Patch(facecolor="lightcoral", edgecolor="darkred", label="Critique"),
                   Patch(facecolor="lightblue", edgecolor="darkblue", label="Avec Marge")]
        ax.legend(handles=legende, loc="upper left")

        plt.tight_layout()
        if fichier_sortie: plt.savefig(fichier_sortie, dpi=300)
        plt.show()

    def dessiner_gantt(self, fichier_sortie="./rapport/figures/graphe_gantt.png"):
        """Génère le diagramme de Gantt avec les marges hachurées."""
        fig, ax = plt.subplots(figsize=(14, 8))
        taches = list(nx.topological_sort(self.graphe))
        taches.reverse()
        
        for i, code in enumerate(taches):
            es = self.calc.dates_tot[code]['ES']
            ef = self.calc.dates_tot[code]['EF']
            marge = self.calc.marges[code]
            est_critique = (marge == 0)

            # Barre de la tâche
            ax.barh(i, self.graphe.nodes[code]['duree'], left=es, 
                    color="lightcoral" if est_critique else "lightblue", 
                    edgecolor="darkred" if est_critique else "darkblue", linewidth=1.2)

            # Barre de la marge
            if marge > 0:
                ax.barh(i, marge, left=ef, color='white', edgecolor='gray', hatch='///', alpha=0.4)
                ax.text(ef + marge + 0.5, i, f"marge: {marge}m", va='center', fontsize=9, color='gray')

            ax.text(es - 0.5, i, f"{code} ", va='center', ha='right', fontweight='bold')

        ax.set_yticks(range(len(taches)))
        ax.set_yticklabels([self.gp.obtenir_info_tache(t)['nom'] for t in taches])
        ax.set_xlabel("Temps (minutes)")
        ax.set_title(f"Diagramme de Gantt - Fin de projet : {self.calc.duree_totale} min", fontweight='bold')
        ax.grid(axis='x', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        if fichier_sortie: plt.savefig(fichier_sortie, dpi=300)
        plt.show()

if __name__ == "__main__":
    try:
        # Remplace "donnees_pipeline.csv" par le nom de ton fichier réel
        gp = GraphePERT("./data/taches.csv")
        
        # 2. Calculs PERT 
        calculateur = CalculateurPERT(gp)
        calculateur.executer_analyse_complete()
        
        # 3. Visualisation
        visu = VisualisateurPERT(calculateur)
        
        print("--- Analyse terminée ---")
        print(f"Durée totale du projet : {calculateur.duree_totale} minutes")
        print(f"Chemin critique : {' -> '.join(calculateur.chemin_critique)}")
        
        # Lancement des dessins
        visu.dessiner_pert()
        visu.dessiner_gantt()
        
    except FileNotFoundError:
        print("Erreur : Le fichier CSV est introuvable. Vérifiez le nom du fichier.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")