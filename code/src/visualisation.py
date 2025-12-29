import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Patch


def creer_graphe_pert(graphe, resultats, fichier_sortie=None):
    """
    Cree un graphe PERT hierarchique avec chemin critique
    """
    fig, ax = plt.subplots(figsize=(18, 10))

    chemin = resultats["chemin_critique"]
    dates_tot = resultats["dates_tot"]

    # Calculer positions
    pos = _calculer_positions(graphe.graphe, dates_tot)

    # Arcs normaux (gris)
    arcs_normaux = [
        (u, v)
        for u, v in graphe.graphe.edges()
        if not (u in chemin and v in chemin and chemin.index(v) == chemin.index(u) + 1)
    ]
    nx.draw_networkx_edges(
        graphe.graphe,
        pos,
        edgelist=arcs_normaux,
        edge_color="gray",
        width=2,
        arrows=True,
        arrowsize=15,
        node_size=3500,
        ax=ax,
        alpha=0.5,
    )

    # Arcs critiques (rouge)
    arcs_critiques = [(chemin[i], chemin[i + 1]) for i in range(len(chemin) - 1)]
    nx.draw_networkx_edges(
        graphe.graphe,
        pos,
        edgelist=arcs_critiques,
        edge_color="red",
        width=4,
        arrows=True,
        arrowsize=20,
        node_size=3500,
        ax=ax,
    )

    # Noeuds
    couleurs_noeuds = [
        "lightcoral" if n in chemin else "lightblue" for n in graphe.graphe.nodes()
    ]
    couleurs_bordures = [
        "darkred" if n in chemin else "darkblue" for n in graphe.graphe.nodes()
    ]

    nx.draw_networkx_nodes(
        graphe.graphe,
        pos,
        node_color=couleurs_noeuds,
        edgecolors=couleurs_bordures,
        linewidths=3,
        node_size=3500,
        ax=ax,
    )

    # Labels
    labels = {
        n: f"{n}\n{graphe.graphe.nodes[n]['duree']}min\n[{dates_tot[n]['ES']}-{dates_tot[n]['EF']}]"
        for n in graphe.graphe.nodes()
    }
    nx.draw_networkx_labels(
        graphe.graphe, pos, labels, font_size=9, font_weight="bold", ax=ax
    )

    # Grille temporelle
    duree_max = int(resultats["duree_totale"])
    for t in range(0, duree_max + 1, 10):
        ax.axvline(x=t, color="lightgray", linestyle="--", alpha=0.4, zorder=0)

    # Titre et axes
    ax.set_title(
        "Graphe PERT - Chemin Critique en Rouge", fontsize=15, fontweight="bold", pad=15
    )
    ax.set_xlabel("Temps (minutes)", fontsize=12)
    ax.set_xlim(-5, duree_max + 5)
    ax.axis("off")

    # Legende simple
    legende = [
        Patch(facecolor="lightcoral", edgecolor="darkred", label="Critique"),
        Patch(facecolor="lightblue", edgecolor="darkblue", label="Non-critique"),
    ]
    ax.legend(handles=legende, loc="upper left", fontsize=10)

    plt.tight_layout()

    if fichier_sortie:
        plt.savefig(fichier_sortie, dpi=300, bbox_inches="tight", facecolor="white")
        print(f"Graphe sauvegarde: {fichier_sortie}")

    return fig, ax


def creer_diagramme_gantt(graphe, resultats, fichier_sortie=None):
    """
    Cree un diagramme de Gantt
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    taches = list(nx.topological_sort(graphe.graphe))
    chemin = resultats["chemin_critique"]

    for i, tache in enumerate(taches):
        es = resultats["dates_tot"][tache]["ES"]
        duree = graphe.graphe.nodes[tache]["duree"]
        couleur = "red" if tache in chemin else "blue"

        ax.barh(i, duree, left=es, height=0.6, color=couleur, alpha=0.7)
        ax.text(
            es + duree / 2,
            i,
            tache,
            ha="center",
            va="center",
            fontweight="bold",
            color="white",
        )

    ax.set_yticks(range(len(taches)))
    ax.set_yticklabels([graphe.graphe.nodes[t]["nom"] for t in taches])
    ax.set_xlabel("Temps (minutes)", fontsize=12)
    ax.set_title("Diagramme de Gantt", fontsize=14, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()

    if fichier_sortie:
        plt.savefig(fichier_sortie, dpi=300, bbox_inches="tight")
        print(f"Gantt sauvegarde: {fichier_sortie}")

    return fig, ax


# Fonctions utilitaires


def _calculer_positions(graphe, dates_tot):
    """Calcule les positions hierarchiques basees sur le temps"""
    # Calculer niveaux
    niveaux = {}
    for node in nx.topological_sort(graphe):
        preds = list(graphe.predecessors(node))
        niveaux[node] = max([niveaux[p] for p in preds], default=-1) + 1

    # Grouper par niveau
    noeuds_par_niveau = {}
    for node, niveau in niveaux.items():
        noeuds_par_niveau.setdefault(niveau, []).append(node)

    # Positionner
    pos = {}
    for niveau, noeuds in noeuds_par_niveau.items():
        for i, node in enumerate(sorted(noeuds)):
            x = (dates_tot[node]["ES"] + dates_tot[node]["EF"]) / 2
            y = (i - (len(noeuds) - 1) / 2) * 2.5
            pos[node] = (x, y)

    return pos
