/* Instruction du dossier : l'écran principal du produit.

   L'ordre de lecture est délibéré. L'agent voit d'abord ce que le client
   demande, ce qu'il peut supporter et ce qu'il a déjà fait ; ensuite ce qui
   appelle son attention ; le détail des moteurs vient en dernier, et la
   décision lui appartient. */

import {
  $, $$, api, date as formaterDate, etatVide, horodatage, listeDonnees, montant,
  nombre, pourcentage, valeurIndicateur, listePoints, activerPremierOnglet,
} from "./noyau.js";
import { enregistrerChargeur, ouvrir } from "./navigation.js";
import { gabaritPieces } from "./clients.js";

const LIBELLES_PRESSION = {
  soutenable: "Soutenable",
  tendue: "Tendue",
  critique: "Critique",
  depassee: "Échéance supérieure à la marge",
  insuffisante: "Marge nulle ou négative",
  indeterminee: "Indéterminée",
};

let dossier = null;
let minuteurSimulation = null;
let simulationCourante = 0;
let ouvrirFiche = () => {};

export function brancherInstruction({ fiche }) {
  ouvrirFiche = fiche;
  $("#instruction-voir-client").onclick = () => dossier && ouvrirFiche(dossier.demande.identifiant_client);
  $("#simulation-montant").oninput = lancerSimulation;
  $("#simulation-duree").onchange = lancerSimulation;
  $("#appliquer-simulation").onclick = appliquerSimulation;
  $("#enregistrer-decision").onclick = enregistrerDecision;
  enregistrerChargeur("instruction", () => {});
}

export async function ouvrirInstruction(identifiant) {
  dossier = await api(`/api/demandes-credit/${identifiant}/`);
  ouvrir("instruction");
  activerPremierOnglet("instruction");
  afficher();
}

function afficher() {
  const demande = dossier.demande;
  const analyse = dossier.analyse;

  $("#instruction-reference").textContent = demande.reference;
  $("#instruction-client").textContent = demande.client;
  $("#instruction-resume").textContent =
    [montant(demande.montant_demande), `${demande.duree_mois} mois`, demande.objet_credit, demande.produit]
      .filter(Boolean).join(" · ");
  const badge = $("#instruction-decision");
  badge.textContent = demande.decision_agent.replace("_", " ");
  badge.className = "badge-statut " + demande.decision_agent.toLowerCase();

  const completude = analyse.qualite_dossier.completude;
  $("#instruction-jauge").style.width = completude + "%";
  $("#instruction-completude").textContent = `Dossier ${completude} % complet`;

  afficherApercu(demande, analyse);
  afficherFinances(analyse);
  afficherHistorique(analyse);
  afficherPieces(demande.identifiant_client);
  afficherAnalyse(analyse);

  $("#instruction-observations").value = demande.observations_agent || "";
  $("#instruction-motif").value = demande.motif_decision || "";
  $$('input[name="decision"]').forEach(bouton => (bouton.checked = bouton.value === demande.decision_agent));
  $("#message-decision").textContent = "";

  preparerSimulation(demande);
}

const moteurParCode = (analyse, code) => analyse.moteurs.find(moteur => moteur.code === code);

function afficherApercu(demande, analyse) {
  const premiere = analyse.premiere_demande;
  $("#instruction-premiere-demande").innerHTML = premiere
    ? `<div class="encart attention" style="margin-bottom:22px">
         <strong>${premiere.titre}.</strong> ${premiere.explication}
         L'analyse repose uniquement sur ${premiere.appuis.join(", ")}. ${premiere.consequence}
       </div>`
    : "";

  $("#apercu-demande").innerHTML = listeDonnees([
    ["Montant demandé", montant(demande.montant_demande)],
    ["Durée", `${demande.duree_mois} mois`],
    ["Objet", demande.objet_credit || "non renseigné"],
    ["Produit", demande.produit || "non renseigné"],
    ["Échéance estimée", montant(demande.echeance_estimee), "total"],
  ]);

  const capacite = moteurParCode(analyse, "capacite");
  $("#apercu-capacite").innerHTML = capacite.evaluable
    ? listeDonnees(capacite.indicateurs.map(indicateur => [indicateur.libelle, valeurIndicateur(indicateur)]))
      + listeDonnees([["Pression", LIBELLES_PRESSION[capacite.pression.niveau],
        ["depassee", "insuffisante", "critique"].includes(capacite.pression.niveau) ? "total negatif" : "total"]])
    : `<div class="encart attention">${capacite.message}</div>`;

  const historique = moteurParCode(analyse, "historique");
  $("#apercu-historique").innerHTML = historique.evaluable
    ? listeDonnees(historique.indicateurs.map(indicateur => [indicateur.libelle, valeurIndicateur(indicateur)]))
    : `<div class="encart attention">${historique.message}</div>`;

  $("#points-attention").innerHTML = listePoints(analyse.points.attention, "attention");
  $("#points-favorables").innerHTML = listePoints(analyse.points.favorables, "favorable");
}

function afficherFinances(analyse) {
  const capacite = moteurParCode(analyse, "capacite");
  if (!capacite.evaluable) {
    $("#cascade-capacite").innerHTML = `<div class="encart attention">${capacite.message}</div>`;
    $("#pression-remboursement").innerHTML = "";
  } else {
    $("#cascade-capacite").innerHTML = capacite.cascade.map(ligne => {
      const classes = ligne.sens === "total" ? "total" : ligne.sens === "sous_total" ? "total" : "";
      const prefixe = ligne.sens === "debit" ? "− " : "";
      return `<div class="${classes}"><span class="libelle">${ligne.libelle}</span><span class="valeur ${
        ligne.sens === "total" && ligne.montant < 0 ? "negatif" : ""}">${prefixe}${montant(ligne.montant)}</span></div>`;
    }).join("");

    const pression = capacite.pression;
    const largeur = pression.valeur === null ? 0 : Math.min(100, Math.round(pression.valeur * 100));
    const critique = ["depassee", "insuffisante", "critique"].includes(pression.niveau);
    $("#pression-remboursement").innerHTML = `
      <span class="surtexte">Pression de remboursement</span>
      <div class="jauge" style="margin:8px 0 6px"><div style="width:${largeur}%;background:${
        critique ? "var(--danger)" : pression.niveau === "tendue" ? "var(--alerte)" : "var(--succes)"}"></div></div>
      <p class="sous-titre">${LIBELLES_PRESSION[pression.niveau]}${
        pression.valeur !== null ? ` · l'échéance représente ${pourcentage(pression.valeur)} de la marge disponible` : ""}</p>`;
  }

  const endettement = moteurParCode(analyse, "endettement");
  $("#detail-endettement").innerHTML = endettement.evaluable
    ? listeDonnees(endettement.indicateurs.map(indicateur => [indicateur.libelle, valeurIndicateur(indicateur)]))
    : `<div class="encart attention">${endettement.message}</div>`;
  $("#note-endettement").innerHTML = endettement.note ? `<p class="sous-titre">${endettement.note}</p>` : "";
}

function afficherHistorique(analyse) {
  const historique = moteurParCode(analyse, "historique");
  const comportement = moteurParCode(analyse, "comportement");
  const activite = moteurParCode(analyse, "activite");

  $("#detail-historique").innerHTML = historique.evaluable
    ? listeDonnees(historique.indicateurs.map(i => [i.libelle, valeurIndicateur(i)]))
    : `<div class="encart attention">${historique.message}</div>`;

  $("#detail-comportement").innerHTML = comportement.evaluable
    ? listeDonnees(comportement.indicateurs.map(i => [i.libelle, valeurIndicateur(i)]))
    : `<div class="encart attention">${comportement.message}</div>`;

  $("#detail-activite").innerHTML = listeDonnees(activite.indicateurs.map(i => [i.libelle, valeurIndicateur(i)]));
  $("#profil-saisonnier").innerHTML = activite.profil_versements
    ? gabaritProfilMensuel(activite.profil_versements) + `<p class="sous-titre" style="margin-top:10px">${activite.message_profil}</p>`
    : `<p class="sous-titre">${activite.message_profil}</p>`;
}

function gabaritProfilMensuel(profil) {
  const maximum = Math.max(...profil.map(mois => mois.versements), 1);
  return `<div class="barres-mensuelles">${profil.map(mois => `
    <div class="barre-mois">
      <div class="colonne"><div style="height:${Math.round(100 * mois.versements / maximum)}%"></div></div>
      <span>${mois.mois}</span>
    </div>`).join("")}</div>`;
}

async function afficherPieces(identifiantClient) {
  const pieces = await api(`/api/clients/${identifiantClient}/documents/`);
  const presentes = pieces.categories.filter(categorie => categorie.present).length;
  $("#instruction-pieces-compte").textContent = `${presentes} / ${pieces.categories.length}`;
  $("#instruction-pieces").innerHTML = gabaritPieces(pieces, { avecActions: false });
}

function afficherAnalyse(analyse) {
  const confiance = analyse.confiance;
  $("#bloc-confiance").innerHTML = `
    <div class="jauge" style="margin-bottom:10px"><div style="width:${confiance.niveau}%"></div></div>
    <div class="donnees">${listeDonnees([
      ["Niveau de confiance", `${confiance.niveau} % · ${confiance.libelle}`, "total"],
      ["Dimensions évaluables", `${confiance.moteurs_evaluables} / ${confiance.moteurs_total}`],
    ])}</div>
    <p class="sous-titre" style="margin:12px 0 6px"><strong>${confiance.consequence}</strong></p>
    ${confiance.reserves.length ? `<div class="points" style="margin-top:10px">${
      confiance.reserves.map(reserve => `<div class="point attention"><span class="marque">⚠</span><span>${reserve}</span></div>`).join("")}</div>` : ""}`;

  $("#bloc-modele").innerHTML = `
    <div class="encart information">${analyse.modele_statistique.message}</div>
    <p class="sous-titre" style="margin-top:12px">
      L'emplacement du moteur statistique est prévu dans la chaîne d'analyse. Il ne sera activé
      qu'après entraînement et validation sur les données réelles d'une institution.</p>`;

  $("#detail-moteurs").innerHTML = analyse.moteurs.map(moteur => `
    <div class="section-compacte">
      <header style="display:flex;justify-content:space-between;align-items:baseline;padding-bottom:6px;margin-bottom:10px;border-bottom:1px solid var(--ligne)">
        <h3>${moteur.libelle}</h3>
        <span class="badge-statut ${moteur.evaluable ? "solde" : "en_attente"}">${moteur.evaluable ? "Évalué" : "Non évaluable"}</span>
      </header>
      ${moteur.evaluable
        ? `<div class="grille-2">
             <div class="donnees">${listeDonnees(moteur.indicateurs.map(i => [i.libelle, valeurIndicateur(i)]))}</div>
             <div class="points">${listePointsMoteur(moteur.constats)}</div>
           </div>`
        : `<div class="encart">${moteur.message}</div>`}
    </div>`).join("");

  $("#bloc-regles").innerHTML = `
    <div class="encart attention" style="margin-bottom:14px">${analyse.regles_experimentales.avertissement}</div>
    <div class="donnees">${listeDonnees([
      ["Indicateur composite", `${analyse.regles_experimentales.indicateur_composite} / 100`],
      ["Niveau indicatif", analyse.regles_experimentales.niveau_indicatif],
    ])}</div>
    <ul class="liste-puces" style="margin-top:10px;padding-left:18px;color:var(--muted);font-size:12.5px">
      ${analyse.regles_experimentales.regles_declenchees.map(regle => `<li>${regle}</li>`).join("")}</ul>`;

  const versions = analyse.versions;
  $("#bloc-versions").innerHTML = listeDonnees([
    ["Feature Engine", "v" + versions.feature_engine],
    ["Moteurs métier", "v" + versions.moteurs_metier],
    ["Modèle statistique", versions.modele_statistique_actif ? "v" + versions.modele_statistique : "non activé"],
  ]);

  $("#instruction-journal").innerHTML = dossier.journal.length
    ? `<span class="surtexte">Journal de la demande</span><div class="donnees" style="margin-top:8px">${
        dossier.journal.map(entree =>
          `<div><span class="libelle">${horodatage(entree.date)}</span><span class="valeur" style="font-weight:400">${
            entree.evenement.replaceAll("_", " ").toLowerCase()}</span></div>`).join("")}</div>`
    : "";
}

function listePointsMoteur(constats) {
  return constats.map(constat => {
    const marque = constat.sens === "favorable" ? "✓" : constat.sens === "attention" ? "⚠" : "·";
    return `<div class="point ${constat.sens}"><span class="marque">${marque}</span><span>${constat.texte}</span></div>`;
  }).join("");
}

/* ---------- Simulation ---------- */

function preparerSimulation(demande) {
  const curseur = $("#simulation-montant");
  curseur.max = Math.max(500000, demande.montant_demande * 2);
  curseur.value = demande.montant_demande;
  $("#simulation-duree").value = String(demande.duree_mois);
  $("#simulation-montant-valeur").textContent = montant(demande.montant_demande);
  lancerSimulation();
}

function lancerSimulation() {
  if (!dossier) return;
  $("#simulation-montant-valeur").textContent = montant(+$("#simulation-montant").value);
  clearTimeout(minuteurSimulation);
  minuteurSimulation = setTimeout(async () => {
    /* Le curseur émet plus vite que le réseau ne répond. Sans ce jeton, une
       réponse ancienne arrivée en retard écrase la simulation en cours. */
    const jeton = (simulationCourante += 1);
    const resultat = await api(`/api/demandes-credit/${dossier.demande.identifiant}/simuler/`
      + `?montant=${+$("#simulation-montant").value}&duree=${+$("#simulation-duree").value}`);
    if (jeton === simulationCourante) afficherSimulation(resultat);
  }, 180);
}

function afficherSimulation(resultat) {
  const actuel = resultat.situation_actuelle;
  const simule = resultat.simulation;
  const ligne = (libelle, gauche, droite) =>
    `<tr><td>${libelle}</td><td class="montant">${gauche}</td><td class="montant">${droite}</td></tr>`;

  $("#tableau-simulation").innerHTML = `
    <div class="tableau-wrap"><table class="donnees-tableau">
      <thead><tr><th></th><th class="montant">Dossier actuel</th><th class="montant">Simulation</th></tr></thead>
      <tbody>
        ${ligne("Montant", montant(actuel.montant), montant(simule.montant))}
        ${ligne("Durée", actuel.duree_mois + " mois", simule.duree_mois + " mois")}
        ${ligne("Échéance estimée", montant(actuel.echeance_estimee), montant(simule.echeance_estimee))}
        ${ligne("Marge disponible", montant(actuel.marge_estimee), montant(simule.marge_estimee))}
        ${ligne("Écart", montant(actuel.ecart), montant(simule.ecart))}
      </tbody></table></div>
    ${simule.ecart < 0
      ? '<div class="encart attention" style="margin-top:12px">L\'échéance simulée reste supérieure à la marge disponible.</div>'
      : '<div class="encart" style="margin-top:12px">L\'échéance simulée tient dans la marge disponible.</div>'}`;
}

async function appliquerSimulation() {
  if (!dossier) return;
  const identifiant = dossier.demande.identifiant;
  await api(`/api/demandes-credit/${identifiant}/appliquer-simulation/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ montant: +$("#simulation-montant").value, duree_mois: +$("#simulation-duree").value }),
  });
  await ouvrirInstruction(identifiant);
}

async function enregistrerDecision() {
  const choisi = $$('input[name="decision"]').find(bouton => bouton.checked);
  if (!choisi) {
    $("#message-decision").textContent = "Sélectionnez une décision.";
    return;
  }
  try {
    const identifiant = dossier.demande.identifiant;
    await api(`/api/demandes-credit/${identifiant}/decision/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        decision: choisi.value,
        motif: $("#instruction-motif").value,
        observations: $("#instruction-observations").value,
      }),
    });
    await ouvrirInstruction(identifiant);
    $("#message-decision").textContent = "Décision enregistrée.";
  } catch (erreur) {
    $("#message-decision").textContent = erreur.message;
  }
}
