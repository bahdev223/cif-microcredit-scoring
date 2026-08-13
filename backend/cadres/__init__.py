"""Cadres d'analyse configurables par l'institution.

Une institution commerciale et une institution agricole n'analysent pas un
dossier de la même manière. Plutôt que de graver une formule dans le code, ce
paquet laisse l'institution décrire la sienne :

    cadre → sections → rubriques → formules → ordre de calcul

Le moteur de calcul est strictement déterministe : mêmes valeurs et même cadre
donnent toujours le même résultat. Il ne juge rien. L'interprétation appartient
au moteur de règles, et l'estimation statistique à un modèle qui n'existe pas
encore.

Les cadres sont versionnés. Une demande instruite en février reste rattachée à
la version du cadre en vigueur ce jour-là : on ne recalcule jamais le passé
avec les règles d'aujourd'hui.
"""
