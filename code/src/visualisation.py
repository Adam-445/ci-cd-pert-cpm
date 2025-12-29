import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Patch


def creer_graphe_pert(graphe, resultats, fichier_sortie=None):
    """
    Cree un graphe PERT hierarchique avec chemin critique

    Args:
        graphe: Instance de GraphePERT
        resultats: Dictionnaire des resultats PERT
        fichier_sortie: Chemin pour sauvegarder (optionnel)
    """
    fig, ax = plt.subplots(figsize=(20, 10))

    dates_tot = resultats["dates_tot"]
    chemin = resultats["chemin_critique"]

    # Calculer positions hierarchiques
    pos = _calculer_positions(graphe.graphe, dates_tot)

    # Dessiner arcs normaux
    arcs_normaux = _obtenir_arcs_normaux(graphe.graphe, chemin)
    nx.draw_networkx_edges(
        graphe.graphe,
        pos,
        edgelist=arcs_normaux,
        edge_color="#94a3b8",
        width=2.5,
        arrows=True,
        arrowsize=18,
        arrowstyle="-|>",
        connectionstyle="arc3,rad=0.1",
        node_size=4000,
        ax=ax,
        alpha=0.6,
    )

    # Dessiner arcs critiques
    arcs_critiques = [(chemin[i], chemin[i + 1]) for i in range(len(chemin) - 1)]
    nx.draw_networkx_edges(
        graphe.graphe,
        pos,
        edgelist=arcs_critiques,
        edge_color="#dc2626",
        width=5,
        arrows=True,
        arrowsize=25,
        arrowstyle="-|>",
        connectionstyle="arc3,rad=0.1",
        node_size=4000,
        ax=ax,
    )

    # Dessiner noeuds
    couleurs = ["#fca5a5" if n in chemin else "#93c5fd" for n in graphe.graphe.nodes()]
    bordures = ["#991b1b" if n in chemin else "#1e3a8a" for n in graphe.graphe.nodes()]

    nx.draw_networkx_nodes(
        graphe.graphe,
        pos,
        node_color=couleurs,
        edgecolors=bordures,
        linewidths=4,
        node_size=4000,
        ax=ax,
    )

    # Dessiner labels
    labels = _creer_labels(graphe, dates_tot)
    nx.draw_networkx_labels(
        graphe.graphe,
        pos,
        labels,
        font_size=10,
        font_weight="bold",
        font_color="#0f172a",
        ax=ax,
    )

    # Grille temporelle
    for t in range(0, int(resultats["duree_totale"]) + 1, 10):
        ax.axvline(x=t, color="#e2e8f0", linestyle="--", alpha=0.3, zorder=0)

    # Titre et legende
    ax.set_title(
        "Graphe PERT - Pipeline CI/CD\nRouge = Chemin Critique",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Temps (minutes)", fontsize=13, fontweight="bold")
    ax.set_xlim(-5, resultats["duree_totale"] + 5)

    legende = [
        Patch(facecolor="#fca5a5", edgecolor="#991b1b", linewidth=2, label="Critique"),
        Patch(
            facecolor="#93c5fd", edgecolor="#1e3a8a", linewidth=2, label="Non-critique"
        ),
    ]
    ax.legend(handles=legende, loc="upper left", fontsize=11, framealpha=0.9)

    # Nettoyage
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_yticks([])

    plt.tight_layout()

    if fichier_sortie:
        plt.savefig(fichier_sortie, dpi=300, bbox_inches="tight", facecolor="white")
        print(f"Graphe sauvegarde: {fichier_sortie}")

    return fig, ax


def creer_diagramme_gantt(graphe, resultats, fichier_sortie=None):
    """
    Cree un diagramme de Gantt simple
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    taches = list(nx.topological_sort(graphe.graphe))
    y_pos = {t: i for i, t in enumerate(taches)}
    chemin = resultats["chemin_critique"]

    for tache in taches:
        es = resultats["dates_tot"][tache]["ES"]
        duree = graphe.graphe.nodes[tache]["duree"]
        couleur = "red" if tache in chemin else "blue"

        ax.barh(y_pos[tache], duree, left=es, height=0.6, color=couleur, alpha=0.7)
        ax.text(
            es + duree / 2,
            y_pos[tache],
            tache,
            ha="center",
            va="center",
            fontweight="bold",
            color="white",
        )

    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels([graphe.graphe.nodes[t]["nom"] for t in taches])
    ax.set_xlabel("Temps (minutes)", fontsize=12)
    ax.set_title("Diagramme de Gantt", fontsize=14, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()

    if fichier_sortie:
        plt.savefig(fichier_sortie, dpi=300, bbox_inches="tight")
        print(f"Gantt sauvegarde: {fichier_sortie}")

    return fig, ax


# Fonction utilitaires


def _calculer_positions(graphe, dates_tot):
    """Calcule les positions hierarchiques des noeuds"""
    niveaux = {}
    for node in nx.topological_sort(graphe):
        preds = list(graphe.predecessors(node))
        niveaux[node] = max([niveaux[p] for p in preds], default=-1) + 1

    noeuds_par_niveau = {}
    for node, niveau in niveaux.items():
        if niveau not in noeuds_par_niveau:
            noeuds_par_niveau[niveau] = []
        noeuds_par_niveau[niveau].append(node)

    pos = {}
    for niveau, noeuds in noeuds_par_niveau.items():
        n_noeuds = len(noeuds)
        for i, node in enumerate(sorted(noeuds)):
            x = (dates_tot[node]["ES"] + dates_tot[node]["EF"]) / 2
            y = (i - (n_noeuds - 1) / 2) * 3
            pos[node] = (x, y)

    return pos


def _obtenir_arcs_normaux(graphe, chemin):
    """Retourne les arcs non-critiques"""
    arcs_normaux = []
    for u, v in graphe.edges():
        est_critique = (
            u in chemin and v in chemin and chemin.index(v) == chemin.index(u) + 1
        )
        if not est_critique:
            arcs_normaux.append((u, v))
    return arcs_normaux


def _creer_labels(graphe, dates_tot):
    """Cree les labels pour les noeuds"""
    labels = {}
    for n in graphe.graphe.nodes():
        info = graphe.obtenir_info_tache(n)
        es = dates_tot[n]["ES"]
        ef = dates_tot[n]["EF"]
        labels[n] = f"{n}\n{info['duree']}min\n[{es}-{ef}]"
    return labels
