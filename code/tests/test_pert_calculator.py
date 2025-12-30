import pytest
import tempfile
import os

from src.graph_builder import GraphePERT
from src.pert_calculator import CalculateurPERT


class TestCalculateurPERT:
    """Tests pour la classe CalculateurPERT"""

    @pytest.fixture
    def graphe_simple(self):
        """Fixture: graphe simple A->B->C"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Tache A", 5)
        graphe.ajouter_tache("B", "Tache B", 10, ["A"])
        graphe.ajouter_tache("C", "Tache C", 8, ["B"])
        return graphe

    @pytest.fixture
    def graphe_parallele(self):
        """Fixture: graphe avec taches paralleles"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Start", 5)
        graphe.ajouter_tache("B", "Branch 1", 10, ["A"])
        graphe.ajouter_tache("C", "Branch 2", 15, ["A"])
        graphe.ajouter_tache("D", "End", 8, ["B", "C"])
        return graphe

    @pytest.fixture
    def graphe_cicd(self):
        """Fixture: graphe complet du pipeline CI/CD"""
        csv_content = """code,nom,duree,predecesseurs
            A,Git Checkout,2,
            B,Compile Backend,15,A
            C,Compile Frontend,10,A
            D,Unit Tests Back,8,B
            E,Unit Tests Front,5,C
            F,Build Docker Image,12,"B,C"
            G,Security Scan (SAST),20,A
            H,Integration Tests,25,"D,E,F"
            I,Deploy to Prod,10,"G,H"
            """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        graphe = GraphePERT(temp_path)
        os.unlink(temp_path)
        return graphe

    def test_init(self, graphe_simple):
        """Test de l'initialisation du calculateur"""
        calc = CalculateurPERT(graphe_simple)
        assert calc.graphe_pert == graphe_simple
        assert calc.graphe == graphe_simple.graphe
        assert calc.dates_tot == {}
        assert calc.dates_tard == {}
        assert calc.marges == {}
        assert calc.chemin_critique == []
        assert calc.duree_totale == 0

    def test_calculer_dates_au_plus_tot_simple(self, graphe_simple):
        """Test calcul dates au plus tôt - graphe simple"""
        calc = CalculateurPERT(graphe_simple)
        dates = calc.calculer_dates_au_plus_tot()

        assert dates["A"]["ES"] == 0
        assert dates["A"]["EF"] == 5
        assert dates["B"]["ES"] == 5
        assert dates["B"]["EF"] == 15
        assert dates["C"]["ES"] == 15
        assert dates["C"]["EF"] == 23
        assert calc.duree_totale == 23

    def test_calculer_dates_au_plus_tot_parallele(self, graphe_parallele):
        """Test calcul dates au plus tot - graphe avec parallelisme"""
        calc = CalculateurPERT(graphe_parallele)
        dates = calc.calculer_dates_au_plus_tot()

        assert dates["A"]["ES"] == 0
        assert dates["A"]["EF"] == 5

        # Deux branches paralleles
        assert dates["B"]["ES"] == 5
        assert dates["B"]["EF"] == 15
        assert dates["C"]["ES"] == 5
        assert dates["C"]["EF"] == 20

        # La tâche D attend la fin de la plus longue branche (C)
        assert dates["D"]["ES"] == 20  # max(15, 20)
        assert dates["D"]["EF"] == 28
        assert calc.duree_totale == 28

    def test_calculer_dates_au_plus_tard_simple(self, graphe_simple):
        """Test calcul dates au plus tard - graphe simple"""
        calc = CalculateurPERT(graphe_simple)
        calc.calculer_dates_au_plus_tot()
        dates_tard = calc.calculer_dates_au_plus_tard()

        # Dans un graphe linéaire, LS=ES et LF=EF pour toutes les tâches
        assert dates_tard["C"]["LF"] == 23
        assert dates_tard["C"]["LS"] == 15
        assert dates_tard["B"]["LF"] == 15
        assert dates_tard["B"]["LS"] == 5
        assert dates_tard["A"]["LF"] == 5
        assert dates_tard["A"]["LS"] == 0

    def test_calculer_dates_au_plus_tard_parallele(self, graphe_parallele):
        """Test calcul dates au plus tard - graphe avec parallelisme"""
        calc = CalculateurPERT(graphe_parallele)
        calc.calculer_dates_au_plus_tot()
        dates_tard = calc.calculer_dates_au_plus_tard()

        # Tache finale
        assert dates_tard["D"]["LF"] == 28
        assert dates_tard["D"]["LS"] == 20

        # Branche critique (C)
        assert dates_tard["C"]["LF"] == 20
        assert dates_tard["C"]["LS"] == 5

        # Branche avec marge (B)
        assert dates_tard["B"]["LF"] == 20
        assert dates_tard["B"]["LS"] == 10

    def test_calculer_marges_simple(self, graphe_simple):
        """Test calcul marges - graphe simple"""
        calc = CalculateurPERT(graphe_simple)
        calc.calculer_dates_au_plus_tot()
        calc.calculer_dates_au_plus_tard()
        marges = calc.calculer_marges()

        # Graphe lineaire = toutes les taches critiques
        assert marges["A"] == 0
        assert marges["B"] == 0
        assert marges["C"] == 0

    def test_calculer_marges_parallele(self, graphe_parallele):
        """Test calcul marges - graphe avec parallelisme"""
        calc = CalculateurPERT(graphe_parallele)
        calc.calculer_dates_au_plus_tot()
        calc.calculer_dates_au_plus_tard()
        marges = calc.calculer_marges()

        # Taches critiques (chemin le plus long)
        assert marges["A"] == 0
        assert marges["C"] == 0
        assert marges["D"] == 0

        # Tache non-critique (B a une marge)
        assert marges["B"] == 5

    def test_identifier_chemin_critique_simple(self, graphe_simple):
        """Test identification chemin critique - graphe simple"""
        calc = CalculateurPERT(graphe_simple)
        calc.executer_analyse_complete()

        assert calc.chemin_critique == ["A", "B", "C"]

    def test_identifier_chemin_critique_parallele(self, graphe_parallele):
        """Test identification chemin critique - graphe avec parallelisme"""
        calc = CalculateurPERT(graphe_parallele)
        calc.executer_analyse_complete()

        # Le chemin critique passe par la branche la plus longue (C)
        assert calc.chemin_critique == ["A", "C", "D"]

    def test_executer_analyse_complete_cicd(self, graphe_cicd):
        """Test analyse complete - pipeline CI/CD"""
        calc = CalculateurPERT(graphe_cicd)
        calc.executer_analyse_complete()

        # Verifier la duree totale
        assert calc.duree_totale == 64

        # Verifier le chemin critique
        assert calc.chemin_critique == ["A", "B", "F", "H", "I"]

        # Verifier les marges
        assert calc.marges["A"] == 0  # Critique
        assert calc.marges["B"] == 0  # Critique
        assert calc.marges["F"] == 0  # Critique
        assert calc.marges["H"] == 0  # Critique
        assert calc.marges["I"] == 0  # Critique

        assert calc.marges["C"] == 5  # Non-critique
        assert calc.marges["D"] == 4  # Non-critique
        assert calc.marges["E"] == 12  # Non-critique
        assert calc.marges["G"] == 32  # Non-critique

    def test_generer_tableau_resultats(self, graphe_cicd):
        """Test generation du tableau de resultats"""
        calc = CalculateurPERT(graphe_cicd)
        calc.executer_analyse_complete()
        tableau = calc.generer_tableau_resultats()

        # Verifier le nombre de lignes
        assert len(tableau) == 9

        # Verifier la structure
        assert all("Code" in ligne for ligne in tableau)
        assert all("Nom" in ligne for ligne in tableau)
        assert all("Duree" in ligne for ligne in tableau)
        assert all("ES" in ligne for ligne in tableau)
        assert all("EF" in ligne for ligne in tableau)
        assert all("LS" in ligne for ligne in tableau)
        assert all("LF" in ligne for ligne in tableau)
        assert all("Marge" in ligne for ligne in tableau)
        assert all("Critique" in ligne for ligne in tableau)

        # Verifier quelques valeurs specifiques
        tache_a = next(t for t in tableau if t["Code"] == "A")
        assert tache_a["ES"] == 0
        assert tache_a["EF"] == 2
        assert tache_a["Critique"] == "Oui"

        tache_g = next(t for t in tableau if t["Code"] == "G")
        assert tache_g["Marge"] == 32
        assert tache_g["Critique"] == "Non"

    def test_dates_coherentes(self, graphe_cicd):
        """Test de coherence des dates (ES <= LS, EF <= LF)"""
        calc = CalculateurPERT(graphe_cicd)
        calc.executer_analyse_complete()

        for tache in calc.graphe.nodes():
            es = calc.dates_tot[tache]["ES"]
            ef = calc.dates_tot[tache]["EF"]
            ls = calc.dates_tard[tache]["LS"]
            lf = calc.dates_tard[tache]["LF"]

            assert es <= ls, f"Tache {tache}: ES ({es}) > LS ({ls})"
            assert ef <= lf, f"Tache {tache}: EF ({ef}) > LF ({lf})"
            assert es < ef or (es == ef and calc.graphe.nodes[tache]["duree"] == 0)
            assert ls < lf or (ls == lf and calc.graphe.nodes[tache]["duree"] == 0)

    def test_marge_formule(self, graphe_cicd):
        """Test que la marge respecte la formule: Marge = LS - ES = LF - EF"""
        calc = CalculateurPERT(graphe_cicd)
        calc.executer_analyse_complete()

        for tache in calc.graphe.nodes():
            es = calc.dates_tot[tache]["ES"]
            ls = calc.dates_tard[tache]["LS"]
            ef = calc.dates_tot[tache]["EF"]
            lf = calc.dates_tard[tache]["LF"]
            marge = calc.marges[tache]

            assert marge == ls - es, f"Tâche {tache}: marge incorrecte (LS-ES)"
            assert marge == lf - ef, f"Tâche {tache}: marge incorrecte (LF-EF)"

    def test_chemin_critique_sans_marge(self, graphe_cicd):
        """Test que toutes les taches du chemin critique ont marge = 0"""
        calc = CalculateurPERT(graphe_cicd)
        calc.executer_analyse_complete()

        for tache in calc.chemin_critique:
            assert calc.marges[tache] == 0, f"Tache critique {tache} a marge > 0"

    def test_duree_totale_coherente(self, graphe_cicd):
        """Test que la duree totale = somme des durées du chemin critique"""
        calc = CalculateurPERT(graphe_cicd)
        calc.executer_analyse_complete()

        duree_chemin = sum(
            calc.graphe.nodes[tache]["duree"] for tache in calc.chemin_critique
        )

        assert calc.duree_totale == duree_chemin

    def test_graphe_tache_unique(self):
        """Test avec un graphe contenant une seule tache"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Seule tache", 10)

        calc = CalculateurPERT(graphe)
        calc.executer_analyse_complete()

        assert calc.duree_totale == 10
        assert calc.chemin_critique == ["A"]
        assert calc.marges["A"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
