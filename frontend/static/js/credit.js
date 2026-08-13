/* Demandes de crédit : la liste, puis la constitution du dossier en quatre
   étapes. Chaque étape correspond à un moment réel de l'instruction, pas à un
   écran de formulaire découpé. */

import {
  $, $$, api, boutonIcone, creer, date as formaterDate, etatVide, ICONE_DOSSIER,
  ICONE_OEIL, listeDonnees, montant, nombre,
} from "./noyau.js";
import { enregistrerChargeur, ouvrir } from "./navigation.js";
import { gabaritPieces } from "./clients.js";

const NOMBRE_ETAPES = 4;
let etapeCourante = 1;
let ouvrirInstruction = () => {};
let ouvrirFiche = () => {};

export function brancherCredit({ instruction, fiche }) {
  ouvrirInstruction = instruction;
  ouvrirFiche = fiche;
  enregistrerChargeur("demandes", chargerDemandes);

  $("#recherche-demandes").oninput = () => chargerDemandes();
  $("#filtre-decision").onchange = () => chargerDemandes();
  $("#nouvelle-demande").onclick = () => demarrerDemande();
  $("#etape-precedente").onclick = () => { etapeCourante = Math.max(1, etapeCourante - 1); afficherEtape(); };
  $("#etape-suivante").onclick = etapeSuivante;
  $("#enregistrer-dossier").onclick = enregistrerDossier;

  ["#demande-recettes", "#demande-charges-activite", "#demande-autres-revenus",
   "#demande-charges-menage", "#demande-dette", "#demande-montant", "#demande-duree"]
    .forEach(selecteur => ($(selecteur).oninput = afficherApercuCapacite));
}

/* ---------- Liste ---------- */

export async function chargerDemandes() {
  const reponse = await api("/api/demandes-credit/");
  const demandes = reponse.demandes || [];
  const recherche = ($("#recherche-demandes").value || "").toLowerCase();
  const filtre = $("#filtre-decision").value;

  $("#demande-total").textContent = nombre(demandes.length);
  $("#demande-montant-total").textContent = montant(demandes.reduce((total, d) => total + (d.montant_demande || 0), 0));
  $("#demande-attente").textContent = nombre(demandes.filter(d => d.decision_agent === "EN_ATTENTE").length);

  const visibles = demandes.filter(demande =>
    demande.client.toLowerCase().includes(recherche) && (!filtre || demande.decision_agent === filtre));

  const corps = $("#liste-demandes");
  corps.replaceChildren();
  if (!visibles.length) {
    corps.innerHTML = '<tr><td colspan="6" class="etat-vide">Aucune demande ne correspond aux filtres.</td></tr>';
    return;
  }

  visibles.forEach(demande => {
    const ligne = creer("tr", { className: "cliquable" });
    ligne.insertAdjacentHTML("beforeend", `
      <td><span class="principale">${demande.client}</span><span class="secondaire">déposée le ${formaterDate(demande.cree_le)}</span></td>
      <td>${demande.objet_credit || "—"}</td>
      <td class="montant">${montant(demande.montant_demande)}</td>
      <td>${demande.duree_mois} mois</td>
      <td><span class="badge-statut ${demande.decision_agent.toLowerCase()}">${demande.decision_agent.replace("_", " ")}</span></td>`);

    const actions = creer("td", { className: "actions-tableau" });
    const client = boutonIcone("", "Voir le client", ICONE_OEIL);
    client.onclick = evenement => { evenement.stopPropagation(); ouvrirFiche(demande.identifiant_client); };
    actions.append(client);
    ligne.append(actions);
    ligne.onclick = () => ouvrirInstruction(demande.identifiant);
    corps.append(ligne);
  });
}

/* ---------- Constitution du dossier ---------- */

export async function demarrerDemande(identifiantClient = "") {
  const [clients, produits] = await Promise.all([
    api("/api/clients/?taille=300"),
    api("/api/produits-credit/"),
  ]);

  $("#demande-client").replaceChildren(
    new Option("Sélectionnez un client", ""),
    ...clients.resultats.map(client => new Option(client.nom_complet, client.identifiant)),
  );
  if (identifiantClient) $("#demande-client").value = identifiantClient;

  $("#demande-produit").replaceChildren(
    new Option(produits.produits.length ? "Sélectionnez un produit" : "Aucun produit configuré", ""),
    ...produits.produits.map(produit => new Option(produit.libelle, produit.identifiant)),
  );

  ["#demande-montant", "#demande-objet"].forEach(selecteur => ($(selecteur).value = ""));
  ["#demande-recettes", "#demande-charges-activite", "#demande-autres-revenus",
   "#demande-charges-menage", "#demande-dette", "#demande-anciennete"].forEach(s => ($(s).value = 0));
  $("#demande-duree").value = 12;
  $("#demande-saisonnalite").value = "";
  $("#message-demande").textContent = "";

  etapeCourante = 1;
  ouvrir("nouvelle-demande-vue");
  afficherEtape();
  if (identifiantClient) chargerContexteClient(identifiantClient);
}

async function chargerContexteClient(identifiant) {
  const dossier = await api(`/api/clients/${identifiant}/`);
  const client = dossier.client;
  const synthese = dossier.synthese;

  if (client.anciennete_activite_mois) $("#demande-anciennete").value = client.anciennete_activite_mois;
  if (synthese.renseignee) {
    $("#demande-recettes").value = synthese.recettes_declarees;
    $("#demande-charges-activite").value = synthese.charges_declarees;
    $("#demande-charges-menage").value = synthese.charges_menage;
    $("#demande-autres-revenus").value = synthese.autres_revenus;
    $("#demande-dette").value = synthese.engagements_existants;
  }

  $("#demande-historique").innerHTML = synthese.nombre_credits
    ? listeDonnees([
        ["Crédits obtenus", nombre(synthese.nombre_credits)],
        ["Crédits soldés", nombre(synthese.nombre_credits_soldes)],
        ["Crédits en cours", nombre(synthese.nombre_credits_en_cours)],
        ["Reste dû", montant(synthese.reste_du_total)],
        ["Retard le plus long", synthese.jours_retard_max ? `${synthese.jours_retard_max} jours` : "aucun"],
      ])
    : `<div class="encart attention">Aucun crédit antérieur dans l'institution : le comportement de remboursement ne pourra pas être évalué.</div>`;

  const pieces = await api(`/api/clients/${identifiant}/documents/`);
  $("#demande-pieces").innerHTML = gabaritPieces(pieces, { avecActions: false });
  afficherApercuCapacite();
}

function afficherApercuCapacite() {
  const valeur = selecteur => +$(selecteur).value || 0;
  const marge = valeur("#demande-recettes") + valeur("#demande-autres-revenus")
    - valeur("#demande-charges-activite") - valeur("#demande-charges-menage") - valeur("#demande-dette");
  const echeance = Math.round(valeur("#demande-montant") / (valeur("#demande-duree") || 1));

  $("#demande-apercu-capacite").innerHTML = listeDonnees([
    ["Résultat de l'activité", montant(valeur("#demande-recettes") - valeur("#demande-charges-activite"))],
    ["Marge disponible", montant(marge), "total"],
    ["Échéance estimée", montant(echeance), echeance > marge ? "negatif" : ""],
  ]);
}

function afficherEtape() {
  for (let numero = 1; numero <= NOMBRE_ETAPES; numero += 1) {
    $("#etape-" + numero).classList.toggle("masque", numero !== etapeCourante);
  }
  $$("#etapes-demande li").forEach(element => {
    const numero = +element.dataset.etape;
    element.classList.toggle("active", numero === etapeCourante);
    element.classList.toggle("faite", numero < etapeCourante);
  });
  $("#etape-precedente").disabled = etapeCourante === 1;
  $("#etape-suivante").classList.toggle("masque", etapeCourante === NOMBRE_ETAPES);
  $("#enregistrer-dossier").classList.toggle("masque", etapeCourante !== NOMBRE_ETAPES);
}

async function etapeSuivante() {
  $("#message-demande").textContent = "";
  if (etapeCourante === 1) {
    if (!$("#demande-client").value) {
      $("#message-demande").textContent = "Sélectionnez un client pour continuer.";
      return;
    }
    if (!(+$("#demande-montant").value > 0)) {
      $("#message-demande").textContent = "Indiquez le montant demandé.";
      return;
    }
    await chargerContexteClient($("#demande-client").value);
  }
  etapeCourante = Math.min(NOMBRE_ETAPES, etapeCourante + 1);
  if (etapeCourante === NOMBRE_ETAPES) afficherVerification();
  afficherEtape();
}

function afficherVerification() {
  const valeur = selecteur => +$(selecteur).value || 0;
  const marge = valeur("#demande-recettes") + valeur("#demande-autres-revenus")
    - valeur("#demande-charges-activite") - valeur("#demande-charges-menage") - valeur("#demande-dette");
  const echeance = Math.round(valeur("#demande-montant") / (valeur("#demande-duree") || 1));

  const controles = [
    ["Client identifié", !!$("#demande-client").value],
    ["Montant et durée", valeur("#demande-montant") > 0],
    ["Objet du financement", !!$("#demande-objet").value.trim()],
    ["Produit de crédit", !!$("#demande-produit").value],
    ["Recettes de l'activité", valeur("#demande-recettes") > 0],
    ["Charges du ménage", valeur("#demande-charges-menage") > 0],
    ["Saisonnalité", !!$("#demande-saisonnalite").value],
  ];

  $("#demande-verification").innerHTML = `
    <div class="grille-2">
      <div class="points">${controles.map(([libelle, present]) => `
        <div class="point ${present ? "favorable" : "absent"}">
          <span class="marque">${present ? "✓" : "○"}</span>
          <span>${libelle}${present ? "" : " — non renseigné"}</span>
        </div>`).join("")}</div>
      <div>
        <div class="donnees">${listeDonnees([
          ["Marge disponible", montant(marge), "total"],
          ["Échéance estimée", montant(echeance), echeance > marge ? "negatif" : ""],
        ])}</div>
        ${echeance > marge
          ? '<div class="encart attention" style="margin-top:14px">L\'échéance estimée dépasse la marge disponible. Le dossier peut être enregistré : la décision reste la vôtre.</div>'
          : '<div class="encart" style="margin-top:14px">L\'échéance estimée reste dans la marge disponible.</div>'}
      </div>
    </div>`;
}

async function enregistrerDossier() {
  try {
    const reponse = await api("/api/demandes-credit/analyser/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifiant_client: $("#demande-client").value,
        identifiant_produit: $("#demande-produit").value || null,
        montant_demande: +$("#demande-montant").value,
        duree_mois: +$("#demande-duree").value,
        objet_credit: $("#demande-objet").value,
        anciennete_activite_mois: +$("#demande-anciennete").value,
        saisonnalite_activite: $("#demande-saisonnalite").value,
        recettes_activite: +$("#demande-recettes").value,
        charges_activite: +$("#demande-charges-activite").value,
        autres_revenus_menage: +$("#demande-autres-revenus").value,
        charges_menage: +$("#demande-charges-menage").value,
        mensualite_dette_existante: +$("#demande-dette").value,
      }),
    });
    ouvrirInstruction(reponse.identifiant_demande);
  } catch (erreur) {
    $("#message-demande").textContent = erreur.message;
  }
}
