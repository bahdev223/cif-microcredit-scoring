"""Cœur analytique du dossier de crédit.

L'organisation suit la chaîne décidée au départ du projet :

    dossier → variables métier → moteurs spécialisés → confiance → analyse

Trois principes gouvernent ce paquet :

1. **Le Feature Engine est séparé des moteurs.** Les variables métier sont
   calculées une fois, à un endroit, et tous les moteurs lisent les mêmes.
2. **Aucun moteur ne décide.** Chacun observe une dimension et énonce des
   constats. L'agrégation en une décision appartient à l'agent.
3. **La place du modèle statistique est réservée mais vide.** Il n'a pas été
   construit : aucune donnée réelle n'a servi à l'entraîner. L'architecture
   doit pouvoir l'accueillir sans réécrire le métier.

Ce qui n'est pas connu est dit comme tel. Un dossier sans historique produit
« comportement non évaluable », jamais un score par défaut.
"""
