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
let identifiantClientSelectionne = null;
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

function donneesClient() {
  const donnees = donneesApi();
  delete donnees.montant_demande;
  delete donnees.duree_mois;
  return donnees;
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
  const donnees = {
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
  if (identifiantClientSelectionne) donnees.identifiant_client = identifiantClientSelectionne;
  return donnees;
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
    chargerListes();
  } catch (erreur) {
    alert(`Impossible d'analyser le dossier : ${erreur.message}`);
  } finally {
    bouton.disabled = false;
    bouton.textContent = 'Analyser ce dossier';
  }
});

async function appelJson(url, options = {}) {
  const reponse = await fetch(url, options);
  const contenu = await reponse.json();
  if (!reponse.ok) throw new Error(contenu.erreur || 'Opération impossible.');
  return contenu;
}

function afficherClients(clients) {
  const liste = document.querySelector('#liste-clients');
  liste.replaceChildren();
  (clients.length ? clients : [{ nom_complet: 'Aucun client enregistré.' }]).forEach((client) => {
    const element = document.createElement('li');
    const bouton = document.createElement(client.identifiant ? 'button' : 'span');
    bouton.textContent = client.identifiant
      ? `${client.nom_complet} — ${client.secteur_activite}`
      : client.nom_complet;
    if (client.identifiant) {
      bouton.className = 'bouton-lien';
      bouton.type = 'button';
      bouton.addEventListener('click', () => {
        chargerDossier({ ...client, objet_credit: 'Besoin de fonds de roulement', montant_demande: 100000, duree_mois: 12, chiffre_affaires: client.revenu_mensuel, achats_marchandises: 0, loyer_activite: 0, transport_activite: 0, autres_charges_activite: 0, alimentation: client.charges_mensuelles, logement: 0, transport_personnel: 0, autres_depenses_menage: 0, credits_termines: 0 });
        identifiantClientSelectionne = client.identifiant;
        document.querySelector('#message-chargement').textContent = `Client « ${client.nom_complet} » sélectionné : la prochaine analyse créera une nouvelle demande pour ce client.`;
      });
    }
    element.appendChild(bouton);
    liste.appendChild(element);
  });
}

function afficherDemandes(demandes) {
  const liste = document.querySelector('#liste-demandes');
  liste.replaceChildren();
  (demandes.length ? demandes : [{ client: 'Aucune demande enregistrée.' }]).forEach((demande) => {
    const element = document.createElement('li');
    const score = demande.score_risque === null || demande.score_risque === undefined ? 'en attente' : `risque ${demande.niveau_risque.toLowerCase()} (${demande.score_risque}/100)`;
    element.textContent = demande.identifiant ? `${demande.client} — ${formaterMontant(demande.montant_demande)}, ${score}` : demande.client;
    liste.appendChild(element);
  });
}

async function chargerListes() {
  try {
    const [clients, demandes] = await Promise.all([
      appelJson('/api/clients/'),
      appelJson('/api/demandes-credit/'),
    ]);
    afficherClients(clients.clients);
    afficherDemandes(demandes.demandes);
  } catch (erreur) {
    document.querySelector('#liste-clients').textContent = `Impossible de charger les clients : ${erreur.message}`;
  }
}

async function chargerInstitution() {
  const contenu = await appelJson('/api/institution/');
  const institution = contenu.institution;
  document.querySelector('#institution-nom').value = institution.nom;
  document.querySelector('#institution-sigle').value = institution.sigle;
  document.querySelector('#institution-ville').value = institution.ville;
  document.querySelector('#institution-pays').value = institution.pays;
  document.querySelector('#nom-institution').textContent = institution.nom;
  document.querySelector('#sigle-institution').textContent = `${institution.sigle} · Démonstration microcrédit`;
}

document.querySelector('#enregistrer-client').addEventListener('click', async () => {
  try {
    const contenu = await appelJson('/api/clients/creer/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(donneesClient()) });
    identifiantClientSelectionne = contenu.client.identifiant;
    document.querySelector('#message-chargement').textContent = `Client « ${contenu.client.nom_complet} » enregistré. Vous pouvez maintenant créer sa demande.`;
    chargerListes();
  } catch (erreur) {
    alert(`Impossible d'enregistrer le client : ${erreur.message}`);
  }
});

document.querySelector('#formulaire-institution').addEventListener('submit', async (evenement) => {
  evenement.preventDefault();
  try {
    const contenu = await appelJson('/api/institution/enregistrer/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nom: document.querySelector('#institution-nom').value, sigle: document.querySelector('#institution-sigle').value, ville: document.querySelector('#institution-ville').value, pays: document.querySelector('#institution-pays').value }),
    });
    document.querySelector('#nom-institution').textContent = contenu.institution.nom;
    document.querySelector('#sigle-institution').textContent = `${contenu.institution.sigle} · Démonstration microcrédit`;
    document.querySelector('#message-institution').textContent = 'Configuration enregistrée.';
  } catch (erreur) {
    document.querySelector('#message-institution').textContent = `Enregistrement impossible : ${erreur.message}`;
  }
});
document.querySelector('#actualiser-listes').addEventListener('click', chargerListes);

document.querySelector('#recharger-cas').addEventListener('click', () => {
  identifiantClientSelectionne = null;
  chargerDossier(casFatou);
});
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
chargerInstitution().catch((erreur) => { document.querySelector('#message-institution').textContent = `Configuration indisponible : ${erreur.message}`; });
chargerListes();
