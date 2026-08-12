"""Point d'entrée prévu pour le générateur du monde fictif.

Les fichiers de configuration et les tables CSV existent déjà ; la logique de génération
sera ajoutée seulement après validation des hypothèses documentées dans documentation/.
"""

from pathlib import Path


if __name__ == "__main__":
    racine = Path(__file__).resolve().parent
    print(f"Simulation prête à être implémentée : {racine}")
