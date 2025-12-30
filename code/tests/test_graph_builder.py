import pytest
import tempfile
import os


from src.graph_builder import GraphePERT


class TestGraphePERT:
    """Tests pour la classe GraphePERT"""

    def test_init_empty(self):
        """Test de l'initialisation sans fichier"""
        graphe = GraphePERT()
        assert len(graphe.taches) == 0
        assert graphe.graphe.number_of_nodes() == 0
        assert graphe.graphe.number_of_edges() == 0

    def test_ajouter_tache_simple(self):
        """Test d'ajout d'une tache simple sans predecesseurs"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Tache A", 10)

        assert "A" in graphe.taches
        assert graphe.taches["A"]["nom"] == "Tache A"
        assert graphe.taches["A"]["duree"] == 10
        assert graphe.taches["A"]["predecesseurs"] == []
        assert "A" in graphe.graphe.nodes()

    def test_ajouter_tache_avec_predecesseurs(self):
        """Test d'ajout d'une tâche avec prédécesseurs"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Tache A", 10)
        graphe.ajouter_tache("B", "Tache B", 5)
        graphe.ajouter_tache("C", "Tache C", 15, ["A", "B"])

        assert graphe.taches["C"]["predecesseurs"] == ["A", "B"]
        assert graphe.graphe.has_edge("A", "C")
        assert graphe.graphe.has_edge("B", "C")
        assert graphe.graphe.number_of_edges() == 2

    def test_obtenir_taches_initiales(self):
        """Test de l'identification des tâches initiales"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Start 1", 5)
        graphe.ajouter_tache("B", "Start 2", 3)
        graphe.ajouter_tache("C", "Middle", 10, ["A"])
        graphe.ajouter_tache("D", "End", 8, ["B", "C"])

        initiales = graphe.obtenir_taches_initiales()
        assert set(initiales) == {"A", "B"}

    def test_obtenir_taches_finales(self):
        """Test de l'identification des tâches finales"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Start", 5)
        graphe.ajouter_tache("B", "Middle 1", 10, ["A"])
        graphe.ajouter_tache("C", "Middle 2", 8, ["A"])
        graphe.ajouter_tache("D", "End", 5, ["B", "C"])

        finales = graphe.obtenir_taches_finales()
        assert finales == ["D"]

    def test_valider_graphe_valide(self):
        """Test de validation d'un graphe valide (DAG)"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Tache A", 5)
        graphe.ajouter_tache("B", "Tache B", 10, ["A"])
        graphe.ajouter_tache("C", "Tache C", 8, ["B"])

        valide, message = graphe.valider_graphe()
        assert valide is True
        assert message == "Graphe Valide"

    def test_valider_graphe_avec_cycle(self):
        """Test de detection de cycle dans le graphe"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Tache A", 5)
        graphe.ajouter_tache("B", "Tache B", 10, ["A"])
        # Creer un cycle manuellement
        graphe.graphe.add_edge("B", "A")

        valide, message = graphe.valider_graphe()
        assert valide is False
        assert "cylces" in message.lower() or "cycle" in message.lower()

    def test_obtenir_info_tache(self):
        """Test de recuperation des informations d'une tache"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Test Task", 15, ["B"])

        info = graphe.obtenir_info_tache("A")
        assert info["nom"] == "Test Task"
        assert info["duree"] == 15
        assert info["predecesseurs"] == ["B"]

    def test_obtenir_info_tache_inexistante(self):
        """Test de recuperation d'une tache qui n'existe pas"""
        graphe = GraphePERT()
        info = graphe.obtenir_info_tache("Z")
        assert info == {}

    def test_charger_donnees_csv(self):
        """Test de chargement depuis un fichier CSV"""
        # Créer un fichier CSV temporaire
        csv_content = """code,nom,duree,predecesseurs
                A,Git Checkout,2,
                B,Compile Backend,15,A
                C,Compile Frontend,10,A
                D,Tests,8,"B,C"
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            graphe = GraphePERT(temp_path)

            # Verifier le chargement
            assert len(graphe.taches) == 4
            assert "A" in graphe.taches
            assert "B" in graphe.taches
            assert graphe.taches["B"]["predecesseurs"] == ["A"]
            assert set(graphe.taches["D"]["predecesseurs"]) == {"B", "C"}
            assert graphe.graphe.number_of_edges() == 4  # A->B, A->C, B->D, C->D
        finally:
            os.unlink(temp_path)

    def test_graphe_complexe_pipeline_cicd(self):
        """Test avec le graphe complet du pipeline CI/CD"""
        csv_content = """
                    code,nom,duree,predecesseurs
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

        try:
            graphe = GraphePERT(temp_path)

            # Vérifications
            assert len(graphe.taches) == 9
            assert graphe.obtenir_taches_initiales() == ["A"]
            assert graphe.obtenir_taches_finales() == ["I"]

            valide, _ = graphe.valider_graphe()
            assert valide is True

            # Vérifier les dépendances multiples
            assert set(graphe.taches["F"]["predecesseurs"]) == {"B", "C"}
            assert set(graphe.taches["H"]["predecesseurs"]) == {"D", "E", "F"}
            assert set(graphe.taches["I"]["predecesseurs"]) == {"G", "H"}
        finally:
            os.unlink(temp_path)

    def test_ajouter_tache_predecesseurs_none(self):
        """Test avec predecesseurs explicitement None"""
        graphe = GraphePERT()
        graphe.ajouter_tache("A", "Task", 10, None)
        assert graphe.taches["A"]["predecesseurs"] == []

    def test_graphe_multiple_debuts_fins(self):
        """Test avec plusieurs taches de debut et fin"""
        graphe = GraphePERT()
        # Deux starts
        graphe.ajouter_tache("A", "Start 1", 5)
        graphe.ajouter_tache("B", "Start 2", 3)
        # Convergence
        graphe.ajouter_tache("C", "Middle", 10, ["A", "B"])
        # Divergence vers deux fins
        graphe.ajouter_tache("D", "End 1", 8, ["C"])
        graphe.ajouter_tache("E", "End 2", 6, ["C"])

        initiales = graphe.obtenir_taches_initiales()
        finales = graphe.obtenir_taches_finales()

        assert set(initiales) == {"A", "B"}
        assert set(finales) == {"D", "E"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
