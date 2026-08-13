/* Vue d'ensemble et portefeuille. */

import {
  $, api, boutonIcone, creer, ICONE_DOSSIER, listeDonnees, montant, nombre,
  date as formaterDate, etatVide,
} from "./noyau.js";
import { enregistrerChargeur, ouvrir } from "./navigation.js";

export const LIBELLES_STATUT_CREDIT = {
  SOLDE: "Soldé",
  SOLDE_AVEC_RETARD: "Soldé avec retard",
  EN_COURS: "En cours",
  EN_RETARD: "En retard",
  SANS_ECHEANCIER: "Sans échéancier",
};

let ouvrirInstruction = () => {};
let ouvrirFiche = () => {};

export function brancherPilotage({ instruction, fiche }) {
  ouvrirInstruction = instruction;
  ouvrirFiche = fiche;
  enregistrerChargeur("vue-ensemble", chargerVueEnsemble);
  enregistrerChargeur("portefeuille", chargerPortefeuille);
  ["#pf-filtre-secteur", "#pf-filtre-statut", "#pf-filtre-annee"].forEach(selecteur => {
    $(selecteur).onchange = () => chargerPortefeuille();
  });
}

export async function chargerVueEnsemble() {
  const donnees = await api("/api/tableau-bord/");
  $("#date-observation").textContent = formaterDate(donnees.date_observation);

  $("#kpi-clients").textContent = nombre(donnees.clients);
  $("#kpi-clients-actifs").textContent = `${nombre(donnees.clients_avec_credit_actif)} avec un crédit en cours`;
  $("#kpi-demandes").textContent = nombre(donnees.demandes_en_cours);
  $("#kpi-demandes-detail").textContent = `${donnees.demandes_a_analyser} à analyser · ${donnees.demandes_en_attente_decision} en attente`;
  $("#kpi-credits-actifs").textContent = nombre(donnees.credits_actifs);
  $("#kpi-credits-total").textContent = `${nombre(donnees.credits)} crédits enregistrés`;
  $("#kpi-encours").textContent = montant(donnees.encours);
  $("#kpi-decaisse").textContent = `${montant(donnees.montant_decaisse)} décaissés au total`;

  $("#kpi-echeances-jour").textContent = nombre(donnees.echeances_du_jour);
  $("#kpi-echeances-jour-montant").textContent = montant(donnees.montant_echeances_du_jour);
  $("#kpi-echeances-venir").textContent = nombre(donnees.echeances_a_venir);
  $("#kpi-echeances-venir-montant").textContent = montant(donnees.montant_echeances_a_venir);
  $("#kpi-retards").textContent = nombre(donnees.echeances_en_retard);
  $("#kpi-retards-montant").textContent = `${montant(donnees.montant_en_retard)} restant dus`;
  $("#kpi-credits-retard").textContent = nombre(donnees.credits_en_retard);

  const compteur = $("#compteur-nav-demandes");
  compteur.textContent = donnees.demandes_en_cours;
  compteur.classList.toggle("masque", donnees.demandes_en_cours === 0);

  afficherAttention(donnees.demandes_attention);
  $("#liste-tranches").innerHTML = donnees.tranches_retard.length
    ? listeDonnees(donnees.tranches_retard.map(t => [`Retard de ${t.libelle}`, `${t.nombre} échéance${t.nombre > 1 ? "s" : ""}`]))
    : '<p class="sous-titre">Aucune échéance en retard.</p>';
}

function afficherAttention(demandes) {
  const corps = $("#liste-attention");
  corps.replaceChildren();
  if (!demandes.length) {
    corps.innerHTML = '<tr><td colspan="4" class="etat-vide">Aucune demande en attente.</td></tr>';
    return;
  }
  demandes.forEach(demande => {
    const ligne = creer("tr");
    ligne.insertAdjacentHTML("beforeend", `
      <td class="principale">${demande.client}</td>
      <td><span class="secondaire">${demande.etat} · ${demande.duree_mois} mois</span></td>
      <td class="montant">${montant(demande.montant_demande)}</td>`);
    const actions = creer("td", { className: "actions-tableau" });
    const bouton = boutonIcone("", "Instruire la demande", ICONE_DOSSIER);
    bouton.onclick = () => ouvrirInstruction(demande.identifiant);
    actions.append(bouton);
    ligne.append(actions);
    corps.append(ligne);
  });
}

let filtresCharges = false;

export async function chargerPortefeuille() {
  const parametres = new URLSearchParams({
    secteur: $("#pf-filtre-secteur").value,
    statut: $("#pf-filtre-statut").value,
    annee: $("#pf-filtre-annee").value,
  });
  const donnees = await api("/api/portefeuille/?" + parametres);

  if (!filtresCharges) {
    remplirFiltre("#pf-filtre-secteur", "Tous les secteurs", donnees.filtres.secteurs);
    remplirFiltre("#pf-filtre-annee", "Toutes les périodes", donnees.filtres.annees);
    remplirFiltre("#pf-filtre-statut", "Tous les statuts", donnees.filtres.statuts,
      statut => LIBELLES_STATUT_CREDIT[statut] || statut);
    $("#pf-indisponibles").textContent =
      "Filtres indisponibles : " + donnees.filtres.indisponibles.join(", ").toLowerCase();
    filtresCharges = true;
  }

  const indicateurs = donnees.indicateurs;
  $("#pf-credits").textContent = nombre(indicateurs.credits);
  $("#pf-credits-actifs").textContent = `${nombre(indicateurs.credits_actifs)} encore actifs`;
  $("#pf-decaisse").textContent = montant(indicateurs.montant_decaisse);
  $("#pf-rembourse").textContent = `${montant(indicateurs.montant_rembourse)} remboursés`;
  $("#pf-encours").textContent = montant(indicateurs.encours);
  $("#pf-retard").textContent = nombre(indicateurs.credits_en_retard);

  const corps = $("#liste-portefeuille");
  corps.replaceChildren();
  if (!donnees.credits.length) {
    corps.innerHTML = '<tr><td colspan="7" class="etat-vide">Aucun crédit ne correspond aux filtres.</td></tr>';
  }
  donnees.credits.forEach(credit => {
    const ligne = creer("tr", { className: "cliquable" });
    ligne.insertAdjacentHTML("beforeend", `
      <td class="principale">${credit.identifiant}</td>
      <td>${credit.client}</td>
      <td>${credit.secteur}</td>
      <td class="montant">${montant(credit.montant_decaisse)}</td>
      <td class="montant">${credit.reste_du ? montant(credit.reste_du) : "—"}</td>
      <td>${formaterDate(credit.date_decaissement)}</td>
      <td><span class="badge-statut ${credit.statut.toLowerCase()}">${LIBELLES_STATUT_CREDIT[credit.statut] || credit.statut}</span></td>`);
    ligne.onclick = () => ouvrirFiche(credit.identifiant_client);
    corps.append(ligne);
  });

  $("#pf-repartition").innerHTML = donnees.repartition_secteur.length
    ? listeDonnees(donnees.repartition_secteur.map(e => [e.libelle, `${e.nombre} crédits · ${montant(e.encours)} d'encours`]))
    : etatVide("Aucun crédit.");
}

function remplirFiltre(selecteur, libelleVide, valeurs, transformer = valeur => valeur) {
  $(selecteur).replaceChildren(
    new Option(libelleVide, ""),
    ...valeurs.map(valeur => new Option(transformer(valeur), valeur)),
  );
}

export function allerAuxDemandes() {
  ouvrir("demandes");
}
