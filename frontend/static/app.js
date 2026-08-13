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
let fichiersLotImport = [];
let dernierRapportImport = null;
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

function normaliserDossierImporte(dossier) {
  const donnees = { ...casFatou, ...dossier };
  const equivalences = {
    nom: 'nom_complet',
    nom_client: 'nom_complet',
    secteur: 'secteur_activite',
    montant: 'montant_demande',
    duree: 'duree_mois',
  };
  Object.entries(equivalences).forEach(([source, destination]) => {
    if (dossier[source] !== undefined && dossier[destination] === undefined) donnees[destination] = dossier[source];
  });
  Object.keys(donnees).forEach((cle) => {
    if (typeof donnees[cle] === 'string') donnees[cle] = donnees[cle].trim();
  });
  return donnees;
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
        afficherFicheClient(client.identifiant);
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

async function afficherFicheClient(identifiant) {
  try {
    const contenu = await appelJson(`/api/clients/${identifiant}/`);
    document.querySelector('#fiche-client-nom').textContent = contenu.client.nom_complet;
    document.querySelector('#fiche-client-resume').textContent = `${contenu.client.secteur_activite} · ancienneté ${contenu.client.anciennete_activite_mois} mois · ${contenu.credits.length} crédit(s) importé(s).`;
    const historique = document.querySelector('#fiche-client-historique');
    historique.replaceChildren();
    if (!contenu.credits.length) historique.textContent = 'Aucun historique importé pour ce client.';
    contenu.credits.forEach((credit) => {
      const bloc = document.createElement('article');
      bloc.className = 'historique-credit';
      bloc.innerHTML = `<h3>Crédit ${credit.identifiant} — ${formaterMontant(credit.montant)} sur ${credit.duree_mois} mois</h3><ul><li>Échéances : ${credit.echeances.length}</li><li>Paiements : ${credit.paiements.length}</li></ul><details><summary>Voir les échéances et paiements</summary><p>Échéances : ${credit.echeances.map((e) => `${e.numero} · ${e.date} · ${formaterMontant(e.montant)}`).join(' | ') || 'aucune'}</p><p>Paiements : ${credit.paiements.map((p) => `${p.date} · ${formaterMontant(p.montant)} · ${p.canal}`).join(' | ') || 'aucun'}</p></details>`;
      historique.appendChild(bloc);
    });
    document.querySelector('#fiche-client').classList.remove('masque');
  } catch (erreur) { alert(`Impossible d'ouvrir la fiche client : ${erreur.message}`); }
}
document.querySelector('#fermer-fiche-client').addEventListener('click', () => document.querySelector('#fiche-client').classList.add('masque'));

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

function formaterRapportImport(rapport) {
  dernierRapportImport = rapport;
  const element = document.querySelector('#rapport-import');
  element.replaceChildren();
  element.className = `rapport-import ${rapport.valide ? 'succes' : 'erreur'}`;
  const titre = document.createElement('h3');
  titre.textContent = rapport.valide ? `Lot valide — qualité : ${rapport.qualite} %` : `Lot à corriger — qualité : ${rapport.qualite} %`;
  element.appendChild(titre);
  const resume = document.createElement('p');
  resume.textContent = `${rapport.total_lignes} lignes détectées.`;
  element.appendChild(resume);
  const liste = document.createElement('ul');
  Object.entries(rapport.lignes || {}).forEach(([nom, nombre]) => {
    const ligne = document.createElement('li');
    ligne.textContent = `✓ ${nom} : ${nombre} lignes`;
    liste.appendChild(ligne);
  });
  (rapport.avertissements || []).forEach((avertissement) => {
    const ligne = document.createElement('li');
    ligne.textContent = `⚠ ${avertissement}`;
    liste.appendChild(ligne);
  });
  (rapport.erreurs || []).forEach((erreur) => {
    const ligne = document.createElement('li');
    ligne.textContent = `✕ ${erreur}`;
    liste.appendChild(ligne);
  });
  element.appendChild(liste);
  element.classList.remove('masque');
  document.querySelector('#confirmer-import').classList.toggle('masque', !rapport.valide);
  document.querySelector('#voir-anomalies').classList.toggle('masque', !(rapport.anomalies || []).length);
}

document.querySelector('#voir-anomalies').addEventListener('click', () => {
  const element = document.querySelector('#rapport-import');
  element.querySelector('.details-anomalies')?.remove();
  const details = document.createElement('details');
  details.className = 'details-anomalies';
  details.open = true;
  details.innerHTML = `<summary>Anomalies détectées (${(dernierRapportImport?.anomalies || []).length})</summary><ul>${(dernierRapportImport?.anomalies || []).map((a) => `<li><strong>${a.fichier}</strong>, ligne ${a.ligne} : ${a.type} — ${a.detail}</li>`).join('') || '<li>Aucune anomalie détaillée.</li>'}</ul>`;
  element.appendChild(details);
});

async function validerLotImport(fichiers) {
  fichiersLotImport = [...fichiers];
  const donnees = new FormData();
  fichiersLotImport.forEach((fichier) => donnees.append('fichiers', fichier));
  try {
    const reponse = await fetch('/api/imports-csv/valider/', { method: 'POST', body: donnees });
    const rapport = await reponse.json();
    if (!reponse.ok) throw new Error(rapport.erreur || 'Validation impossible.');
    formaterRapportImport(rapport);
  } catch (erreur) {
    formaterRapportImport({ valide: false, qualite: 0, erreurs: [erreur.message], avertissements: [], lignes: {}, total_lignes: 0 });
  }
}

const champLot = document.querySelector('#fichiers-institution');
champLot.addEventListener('change', () => validerLotImport(champLot.files));
const zoneLot = document.querySelector('#import-lot .zone-depot');
['dragenter', 'dragover'].forEach((type) => zoneLot.addEventListener(type, (evenement) => {
  evenement.preventDefault();
  zoneLot.classList.add('survol');
}));
['dragleave', 'drop'].forEach((type) => zoneLot.addEventListener(type, (evenement) => {
  evenement.preventDefault();
  zoneLot.classList.remove('survol');
}));
zoneLot.addEventListener('drop', (evenement) => validerLotImport(evenement.dataTransfer.files));
document.querySelector('#confirmer-import').addEventListener('click', async () => {
  const donnees = new FormData();
  fichiersLotImport.forEach((fichier) => donnees.append('fichiers', fichier));
  try {
    const reponse = await fetch('/api/imports-csv/confirmer/', { method: 'POST', body: donnees });
    const resultat = await reponse.json();
    if (!reponse.ok) throw new Error(resultat.erreur || 'Import impossible.');
    document.querySelector('#rapport-import').className = 'rapport-import succes';
    document.querySelector('#rapport-import').textContent = `Import confirmé : ${resultat.clients_ajoutes} clients ajoutés. ${resultat.total_lignes} lignes ont été contrôlées.`;
    document.querySelector('#confirmer-import').classList.add('masque');
    chargerListes();
  } catch (erreur) {
    alert(`Import impossible : ${erreur.message}`);
  }
});

document.querySelector('#recharger-cas').addEventListener('click', () => {
  identifiantClientSelectionne = null;
  chargerDossier(casFatou);
});
function analyserCsv(texte) {
  const lignes = texte.replace(/^\uFEFF/, '').trim().split(/\r?\n/).filter(Boolean);
  if (lignes.length < 2) throw new Error('Le CSV doit contenir une ligne de titres et une ligne de données.');
  const separateur = lignes[0].includes(';') ? ';' : ',';
  const titres = lignes[0].split(separateur).map((titre) => titre.trim().replace(/^"|"$/g, ''));
  const valeurs = lignes[1].split(separateur).map((valeur) => valeur.trim().replace(/^"|"$/g, ''));
  return Object.fromEntries(titres.map((titre, index) => [titre, valeurs[index] ?? '']));
}

async function importerFichier(fichier) {
  const message = document.querySelector('#message-chargement');
  if (!fichier) return;
  try {
    const texte = await fichier.text();
    const contenu = fichier.name.toLowerCase().endsWith('.csv') ? analyserCsv(texte) : JSON.parse(texte);
    if (Array.isArray(contenu)) {
      throw new Error('Ce fichier contient plusieurs dossiers. Charge un dossier unique comme cas_fatou.json.');
    }
    chargerDossier(normaliserDossierImporte(contenu));
    message.textContent = `Dossier « ${contenu.nom_complet} » chargé. Tu peux maintenant l'analyser.`;
  } catch (erreur) {
    message.textContent = `Chargement impossible : ${erreur.message}`;
  } finally {
    document.querySelector('#fichier-dossier').value = '';
  }
}

document.querySelector('#fichier-dossier').addEventListener('change', (evenement) => {
  importerFichier(evenement.target.files[0]);
});
const zoneDepot = document.querySelector('#zone-depot');
zoneDepot.addEventListener('click', () => document.querySelector('#fichier-dossier').click());
zoneDepot.addEventListener('keydown', (evenement) => {
  if (evenement.key === 'Enter' || evenement.key === ' ') {
    evenement.preventDefault();
    document.querySelector('#fichier-dossier').click();
  }
});
['dragenter', 'dragover'].forEach((type) => zoneDepot.addEventListener(type, (evenement) => {
  evenement.preventDefault();
  zoneDepot.classList.add('survol');
}));
['dragleave', 'drop'].forEach((type) => zoneDepot.addEventListener(type, (evenement) => {
  evenement.preventDefault();
  zoneDepot.classList.remove('survol');
}));
zoneDepot.addEventListener('drop', (evenement) => importerFichier(evenement.dataTransfer.files[0]));
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
