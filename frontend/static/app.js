const casFatou = {
  nom_complet: 'Fatou Traoré',
  secteur_activite: 'Commerce alimentaire',
  objet_credit: 'Achat de marchandises',
  montant_demande: 500000,
  duree_mois: 12,
  chiffre_affaires: 700000,
  achats_marchandises: 400000,
  loyer_activite: 50000,
  transport_activite: 30000,
  autres_charges_activite: 40000,
  alimentation: 50000,
  logement: 30000,
  transport_personnel: 15000,
  autres_depenses_menage: 25000,
  mensualite_dette_existante: 20000,
  anciennete_activite_mois: 60,
  nombre_retards: 2,
  regularite_tontine: 'reguliere',
  credits_termines: 3,
};

const champs = Object.keys(casFatou);
const formaterMontant = (valeur) => `${new Intl.NumberFormat('fr-FR').format(Math.round(valeur))} FCFA`;
const valeur = (identifiant) => Number(document.querySelector(`#${identifiant}`).value) || 0;

function chargerDossier(dossier) {
  champs.forEach((champ) => {
    if (dossier[champ] === undefined) {
      throw new Error(`Le champ obligatoire « ${champ} » est absent.`);
    }
    document.querySelector(`#${champ}`).value = dossier[champ];
  });
  mettreAJourCalculs();
}

function mettreAJourCalculs() {
  const resultatActivite = valeur('chiffre_affaires') - valeur('achats_marchandises') - valeur('loyer_activite') - valeur('transport_activite') - valeur('autres_charges_activite');
  const depensesMenage = valeur('alimentation') + valeur('logement') + valeur('transport_personnel') + valeur('autres_depenses_menage');
  document.querySelector('#resultat-activite').textContent = formaterMontant(resultatActivite);
  document.querySelector('#capacite-remboursement').textContent = formaterMontant(resultatActivite - depensesMenage - valeur('mensualite_dette_existante'));
}

function afficherListe(selecteur, valeurs) {
  const liste = document.querySelector(selecteur);
  liste.replaceChildren();
  (valeurs.length ? valeurs : ['Aucun élément particulier.']).forEach((texte) => {
    const element = document.createElement('li');
    element.textContent = texte;
    liste.appendChild(element);
  });
}

function donneesApi() {
  const resultatActivite = valeur('chiffre_affaires') - valeur('achats_marchandises') - valeur('loyer_activite') - valeur('transport_activite') - valeur('autres_charges_activite');
  const depensesMenage = valeur('alimentation') + valeur('logement') + valeur('transport_personnel') + valeur('autres_depenses_menage');
  return {
    nom_complet: document.querySelector('#nom_complet').value,
    secteur_activite: document.querySelector('#secteur_activite').value,
    revenu_mensuel: resultatActivite,
    charges_mensuelles: depensesMenage,
    mensualite_dette_existante: valeur('mensualite_dette_existante'),
    anciennete_activite_mois: valeur('anciennete_activite_mois'),
    nombre_retards: valeur('nombre_retards'),
    regularite_tontine: document.querySelector('#regularite_tontine').value,
    montant_demande: valeur('montant_demande'),
    duree_mois: valeur('duree_mois'),
  };
}

function afficherResultat(reponse) {
  document.querySelector('#niveau-risque').textContent = `Risque ${reponse.niveau_risque.toLowerCase()}`;
  document.querySelector('#score-risque').textContent = reponse.score_risque;
  document.querySelector('#recommandation-agent').textContent = reponse.recommandation;
  const indicateurs = reponse.indicateurs;
  afficherListe('#indicateurs', [
    `Capacité de remboursement : ${formaterMontant(indicateurs.capacite_remboursement)}`,
    `Échéance estimée : ${formaterMontant(indicateurs.echeance)}`,
    `Ratio capacité / échéance : ${indicateurs.ratio_capacite.toFixed(2)}`,
  ]);
  afficherListe('#facteurs-favorables', reponse.explication.facteurs_favorables);
  afficherListe('#points-vigilance', reponse.explication.points_vigilance);
  afficherListe('#regles-declenchees', reponse.explication.regles_declenchees);
  document.querySelector('#resultat').classList.remove('masque');
  document.querySelector('#resultat').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.querySelector('#formulaire-dossier').addEventListener('submit', async (evenement) => {
  evenement.preventDefault();
  const bouton = evenement.submitter;
  bouton.disabled = true;
  bouton.textContent = 'Analyse en cours…';
  try {
    const reponse = await fetch('/api/demandes-credit/analyser/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(donneesApi()),
    });
    const texteReponse = await reponse.text();
    let contenu;
    try {
      contenu = JSON.parse(texteReponse);
    } catch {
      throw new Error(`Le serveur a renvoyé une erreur (${reponse.status}). Recharge la page, lance le serveur puis applique les migrations.`);
    }
    if (!reponse.ok) throw new Error(contenu.erreur || 'Analyse impossible.');
    afficherResultat(contenu);
  } catch (erreur) {
    alert(`Impossible d'analyser le dossier : ${erreur.message}`);
  } finally {
    bouton.disabled = false;
    bouton.textContent = 'Analyser ce dossier';
  }
});

document.querySelector('#recharger-cas').addEventListener('click', () => chargerDossier(casFatou));
document.querySelector('#fichier-dossier').addEventListener('change', async (evenement) => {
  const fichier = evenement.target.files[0];
  const message = document.querySelector('#message-chargement');
  if (!fichier) return;
  try {
    const contenu = JSON.parse(await fichier.text());
    if (Array.isArray(contenu)) {
      throw new Error('Ce fichier contient plusieurs dossiers. Charge un dossier unique comme cas_fatou.json.');
    }
    chargerDossier(contenu);
    message.textContent = `Dossier « ${contenu.nom_complet} » chargé. Tu peux maintenant l'analyser.`;
  } catch (erreur) {
    message.textContent = `Chargement impossible : ${erreur.message}`;
    evenement.target.value = '';
  }
});
document.querySelector('#simuler-montant').addEventListener('click', () => {
  document.querySelector('#montant_demande').value = Math.round(valeur('montant_demande') * 0.8 / 5000) * 5000;
  document.querySelector('#formulaire-dossier').requestSubmit();
});
champs
  .filter((champ) => document.querySelector(`#${champ}`).type === 'number')
  .forEach((champ) => document.querySelector(`#${champ}`).addEventListener('input', mettreAJourCalculs));
chargerDossier(casFatou);

