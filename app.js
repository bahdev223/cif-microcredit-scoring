const formulaire = document.querySelector('#formulaire-credit');
const resultat = document.querySelector('#resultat');
const listeJournal = document.querySelector('#liste-journal');
let dernierDossier = null;

const formaterMontant = (valeur) => new Intl.NumberFormat('fr-FR').format(valeur) + ' FCFA';
const afficherListe = (selecteur, valeurs) => {
  document.querySelector(selecteur).innerHTML = valeurs.length
    ? valeurs.map((valeur) => `<li>${valeur}</li>`).join('')
    : '<li>Aucun element particulier.</li>';
};

function analyser(dossier) {
  const capacite = dossier.revenu - dossier.charges;
  const echeance = dossier.montant / 12;
  let risque = 45;
  const favorables = [], vigilances = [], regles = [];

  if (capacite >= echeance * 2) { risque -= 18; favorables.push("Capacite mensuelle confortable par rapport a l'echeance estimee."); }
  else if (capacite >= echeance) { risque -= 5; favorables.push('Capacite mensuelle suffisante mais a surveiller.'); }
  else { risque += 25; vigilances.push("Capacite mensuelle inferieure a l'echeance estimee."); regles.push('R01 - capacite de remboursement insuffisante'); }
  if (dossier.ancienneteActivite >= 24) { risque -= 10; favorables.push('Activite exercee depuis au moins 24 mois.'); }
  else if (dossier.ancienneteActivite < 12) { risque += 12; vigilances.push('Activite recente : recul limite sur les revenus.'); regles.push('R02 - anciennete faible'); }
  if (dossier.nombreRetards === 0) { risque -= 8; favorables.push('Aucun retard de paiement renseigne.'); }
  else { risque += dossier.nombreRetards <= 2 ? 12 : 25; vigilances.push('Retards precedents declares.'); regles.push('R03 - historique de retard'); }
  if (dossier.regulariteTontine === 'reguliere') { risque -= 7; favorables.push('Cotisations tontine regulieres.'); }
  else if (dossier.regulariteTontine === 'inconnue') { risque += 4; vigilances.push('Information tontine indisponible.'); }

  risque = Math.max(5, Math.min(95, Math.round(risque)));
  const qualite = [dossier.revenu, dossier.charges, dossier.ancienneteActivite, dossier.montant].every(Number.isFinite) && dossier.nom.trim() ? 'Bonne : les champs essentiels sont renseignes.' : 'Incomplete : verifier le dossier avant toute decision.';
  return { risque, favorables, vigilances, regles: regles.length ? regles : ['Aucune regle bloquante declenchee'], qualite };
}

function afficherResultat(evaluation, dossier) {
  const libelle = evaluation.risque < 30 ? 'Risque faible' : evaluation.risque < 60 ? 'Risque modere' : 'Risque eleve';
  const recommandation = evaluation.risque < 30 ? "A examiner favorablement par l'agent." : evaluation.risque < 60 ? 'Demander une verification complementaire avant decision.' : 'A ne pas valider sans analyse humaine approfondie.';
  document.querySelector('#libelle-risque').textContent = libelle;
  document.querySelector('#score-risque').textContent = evaluation.risque;
  document.querySelector('#recommandation-agent').textContent = recommandation;
  document.querySelector('#qualite-donnees').textContent = evaluation.qualite;
  afficherListe('#facteurs-favorables', evaluation.favorables);
  afficherListe('#points-vigilance', evaluation.vigilances);
  afficherListe('#regles-declenchees', evaluation.regles);
  resultat.classList.remove('masque');
  const element = document.createElement('li');
  element.textContent = `${dossier.nom} - ${libelle.toLowerCase()} (${evaluation.risque}/100) - demande ${formaterMontant(dossier.montant)}`;
  if (listeJournal.textContent.includes('Aucune analyse')) listeJournal.innerHTML = '';
  listeJournal.prepend(element);
}

function lireDossier() {
  return { nom: document.querySelector('#nom').value, secteur: document.querySelector('#secteur').value, montant: Number(document.querySelector('#montant').value), revenu: Number(document.querySelector('#revenu').value), charges: Number(document.querySelector('#charges').value), ancienneteActivite: Number(document.querySelector('#anciennete-activite').value), nombreRetards: Number(document.querySelector('#nombre-retards').value), regulariteTontine: document.querySelector('#regularite-tontine').value };
}
formulaire.addEventListener('submit', (evenement) => { evenement.preventDefault(); dernierDossier = lireDossier(); afficherResultat(analyser(dernierDossier), dernierDossier); });
document.querySelector('#simuler').addEventListener('click', () => { if (!dernierDossier) return; document.querySelector('#montant').value = Math.round(dernierDossier.montant * .8 / 5000) * 5000; dernierDossier = lireDossier(); afficherResultat(analyser(dernierDossier), dernierDossier); });
document.querySelector('#effacer-journal').addEventListener('click', () => { listeJournal.innerHTML = '<li>Aucune analyse dans cette session.</li>'; });
