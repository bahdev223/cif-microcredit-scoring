/* Clients : liste, dossier et pièces jointes.

   Le dossier est organisé comme un agent le lit : qui est cette personne, ce
   qu'elle fait, ce qu'elle a emprunté, comment elle a remboursé. */

import {
  $, $$, api, boutonIcone, creer, date as formaterDate, etatVide, ICONE_CORBEILLE,
  ICONE_CRAYON, ICONE_DOSSIER, ICONE_OEIL, initiales, listeDonnees, montant, nombre,
  ouvrirDialogue, fermerDialogue, activerPremierOnglet, taille,
} from "./noyau.js";
import { enregistrerChargeur, ouvrir } from "./navigation.js";
import { LIBELLES_STATUT_CREDIT } from "./pilotage.js";

let pageClients = 1;
export let clientAffiche = null;
let dossierAffiche = null;
let demarrerDemande = () => {};

export function brancherClients({ nouvelleDemande }) {
  demarrerDemande = nouvelleDemande;
  enregistrerChargeur("clients", chargerClients);

  $("#recherche-clients").oninput = () => { pageClients = 1; chargerClients(); };
  $("#nouveau-client").onclick = () => ouvrirFormulaireClient();
  $("#fiche-modifier").onclick = () => clientAffiche && ouvrirFormulaireClient(clientAffiche);
  $("#fiche-nouvelle-demande").onclick = () => demarrerDemande(clientAffiche?.identifiant);
  $("#fiche-ajouter-document").onclick = () => ouvrirDialogue("dialogue-categorie");
  $("#confirmer-categorie").onclick = () => {
    $("#categorie-document").value = $("#choix-categorie").value;
    fermerDialogue("dialogue-categorie");
    $("#fichier-document").click();
  };
  $("#fichier-document").onchange = evenement => {
    envoyerDocument(evenement.target.files[0]);
    evenement.target.value = "";
  };
  $("#formulaire-client").onsubmit = enregistrerClient;
}

/* ---------- Liste ---------- */

export async function chargerClients() {
  const recherche = encodeURIComponent($("#recherche-clients").value || "");
  const reponse = await api(`/api/clients/?page=${pageClients}&recherche=${recherche}`);
  const corps = $("#liste-clients");
  corps.replaceChildren();

  if (!reponse.resultats.length) {
    corps.innerHTML = '<tr><td colspan="5" class="etat-vide">Aucun client.</td></tr>';
  }

  reponse.resultats.forEach(client => {
    const ligne = creer("tr", { className: "cliquable" });
    ligne.insertAdjacentHTML("beforeend", `
      <td><span class="principale">${client.nom_complet}</span>${
        client.identifiant_source ? `<span class="secondaire">${client.identifiant_source}</span>` : ""}</td>
      <td>${client.secteur_activite}</td>
      <td>${client.anciennete_activite_mois} mois</td>
      <td>${client.identifiant_source ? "Importé" : "Saisi"}</td>`);

    const actions = creer("td", { className: "actions-tableau" });
    const modifier = boutonIcone("modifier", "Modifier", ICONE_CRAYON);
    const supprimer = boutonIcone("supprimer", "Supprimer", ICONE_CORBEILLE);
    modifier.onclick = evenement => { evenement.stopPropagation(); ouvrirFormulaireClient(client); };
    supprimer.onclick = evenement => { evenement.stopPropagation(); supprimerClient(client); };
    actions.append(modifier, supprimer);
    ligne.append(actions);
    ligne.onclick = () => ouvrirFicheClient(client.identifiant);
    corps.append(ligne);
  });

  $("#pagination-clients").textContent =
    `Page ${reponse.pagination.page} / ${reponse.pagination.pages} · ${reponse.pagination.total} clients`;
}

function ouvrirFormulaireClient(client = null) {
  $("#client-identifiant").value = client?.identifiant || "";
  $("#client-nom").value = client?.nom_complet || "";
  $("#client-secteur").value = client?.secteur_activite || "";
  $("#client-anciennete").value = client?.anciennete_activite_mois ?? 0;
  $("#titre-dialogue-client").textContent = client ? "Modifier le client" : "Nouveau client";
  $("#message-client").textContent = "";
  ouvrirDialogue("dialogue-client");
}

async function enregistrerClient(evenement) {
  evenement.preventDefault();
  const identifiant = $("#client-identifiant").value;
  try {
    await api(identifiant ? `/api/clients/${identifiant}/modifier/` : "/api/clients/creer/", {
      method: identifiant ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nom_complet: $("#client-nom").value,
        secteur_activite: $("#client-secteur").value,
        anciennete_activite_mois: +$("#client-anciennete").value,
      }),
    });
    fermerDialogue("dialogue-client");
    if (identifiant && clientAffiche?.identifiant == identifiant) ouvrirFicheClient(identifiant);
    else chargerClients();
  } catch (erreur) {
    $("#message-client").textContent = erreur.message;
  }
}

async function supprimerClient(client) {
  if (!confirm(`Supprimer définitivement « ${client.nom_complet} » ?`)) return;
  try {
    await api(`/api/clients/${client.identifiant}/supprimer/`, { method: "DELETE" });
    chargerClients();
  } catch (erreur) {
    alert(erreur.message);
  }
}

/* ---------- Dossier ---------- */

export async function ouvrirFicheClient(identifiant) {
  dossierAffiche = await api(`/api/clients/${identifiant}/`);
  clientAffiche = dossierAffiche.client;
  ouvrir("fiche-client");
  activerPremierOnglet("fiche");
  afficherDossier(dossierAffiche);
}

function afficherDossier(dossier) {
  const client = dossier.client;
  const synthese = dossier.synthese;

  $("#fiche-initiales").textContent = initiales(client.nom_complet);
  $("#fiche-nom").textContent = client.nom_complet;
  $("#fiche-resume").textContent = [client.secteur_activite, client.identifiant_source].filter(Boolean).join(" · ");
  $("#fiche-anciennete-relation").textContent = `Client depuis le ${formaterDate(client.cree_le)}`;

  $("#fiche-situation").innerHTML = synthese.renseignee
    ? listeDonnees([
        ["Recettes de l'activité", montant(synthese.recettes_declarees)],
        ["Charges de l'activité", "− " + montant(synthese.charges_declarees)],
        ["Résultat de l'activité", montant(synthese.resultat_activite)],
        ["Charges du ménage", "− " + montant(synthese.charges_menage)],
        ["Engagements existants", "− " + montant(synthese.engagements_existants)],
        ["Disponible", montant(synthese.marge_estimee), "total" + (synthese.marge_estimee < 0 ? " negatif" : "")],
      ]) + `<p class="sous-titre" style="margin-top:10px">Relevé du ${formaterDate(synthese.date_releve)}, lors de la dernière demande.</p>`
    : `<div class="encart">Aucune situation économique relevée. Elle est recueillie lors d'une demande de crédit, car elle change dans le temps.</div>`;

  $("#fiche-relation").innerHTML = listeDonnees([
    ["Crédits obtenus", nombre(synthese.nombre_credits)],
    ["Crédits soldés", nombre(synthese.nombre_credits_soldes)],
    ["Crédits en cours", nombre(synthese.nombre_credits_en_cours)],
    ["Montant cumulé emprunté", montant(synthese.montant_total_emprunte)],
    ["Reste dû", montant(synthese.reste_du_total)],
    ["Retard le plus long observé", synthese.jours_retard_max ? `${synthese.jours_retard_max} jours` : "aucun",
      synthese.jours_retard_max ? "negatif" : ""],
    ["Ancienneté de l'activité", `${client.anciennete_activite_mois} mois`],
  ]);

  afficherDemandesEnCours(dossier.demandes_en_cours);
  afficherActivites(dossier.activites);
  afficherCredits(dossier.historique_credit);
  afficherPaiements(dossier.historique_credit);
  afficherChronologie(dossier.chronologie);
  chargerDocuments(client.identifiant);
}

function afficherDemandesEnCours(demandes) {
  const conteneur = $("#fiche-demandes-en-cours");
  if (!demandes.length) {
    conteneur.innerHTML = etatVide("Aucune demande en cours.");
    return;
  }
  conteneur.innerHTML = `
    <div class="tableau-wrap"><table class="donnees-tableau">
      <thead><tr><th>Déposée le</th><th class="montant">Montant</th><th>Durée</th><th>Décision</th><th></th></tr></thead>
      <tbody>${demandes.map(demande => `
        <tr><td>${formaterDate(demande.cree_le)}</td>
        <td class="montant">${montant(demande.montant_demande)}</td>
        <td>${demande.duree_mois} mois</td>
        <td><span class="badge-statut ${demande.decision_agent.toLowerCase()}">${demande.decision_agent.replace("_", " ")}</span></td>
        <td class="actions-tableau"><button class="bouton-discret" data-instruire="${demande.identifiant}">Instruire</button></td></tr>`).join("")}
      </tbody></table></div>`;
}

function afficherActivites(activites) {
  $("#fiche-activites").innerHTML = activites.length
    ? `<div class="tableau-wrap"><table class="donnees-tableau">
        <thead><tr><th>Activité</th><th>Secteur</th><th>Depuis</th><th>Rôle</th></tr></thead>
        <tbody>${activites.map(activite => `
          <tr><td class="principale">${activite.libelle || activite.secteur}</td>
          <td>${activite.secteur}</td>
          <td>${activite.date_debut ? formaterDate(activite.date_debut) : "—"}</td>
          <td>${activite.est_principale ? "Activité principale" : "Secondaire"}</td></tr>`).join("")}
        </tbody></table></div>`
    : etatVide("Aucune activité déclarée pour ce client.");
}

function afficherCredits(credits) {
  const conteneur = $("#fiche-credits");
  conteneur.replaceChildren();
  if (!credits.length) {
    conteneur.innerHTML = etatVide("Aucun crédit enregistré.");
    return;
  }

  credits.forEach(credit => {
    const bloc = creer("article", { className: "credit" });
    const entete = creer("button", { className: "entete-credit", type: "button" });
    entete.insertAdjacentHTML("beforeend", `
      <span><strong>${credit.identifiant}</strong>
        <span class="secondaire">Décaissé le ${formaterDate(credit.date_decaissement)} · ${credit.duree_mois} mois</span></span>
      <span class="resume">
        <span>Montant <strong>${montant(credit.montant_decaisse)}</strong></span>
        <span>Remboursé <strong>${montant(credit.total_paye)}</strong></span>
        <span>Reste <strong>${montant(credit.reste_du)}</strong></span>
        <span class="badge-statut ${credit.statut.toLowerCase()}">${LIBELLES_STATUT_CREDIT[credit.statut]}</span>
      </span>`);

    const corps = creer("div", { className: "corps-credit masque" });
    corps.innerHTML = `
      <div class="tableau-wrap"><table class="donnees-tableau">
        <thead><tr><th>N°</th><th>Exigible le</th><th class="montant">Dû</th><th class="montant">Payé</th><th class="montant">Reste</th><th>Retard</th></tr></thead>
        <tbody>${credit.echeances.map(echeance => `
          <tr><td>${echeance.numero}</td>
          <td>${formaterDate(echeance.date_exigible)}</td>
          <td class="montant">${montant(echeance.montant_du)}</td>
          <td class="montant">${montant(echeance.montant_couvert)}</td>
          <td class="montant">${echeance.reste_du ? montant(echeance.reste_du) : "—"}</td>
          <td>${echeance.jours_retard ? echeance.jours_retard + " j" : "—"}</td></tr>`).join("")}
        </tbody></table></div>`;

    entete.onclick = () => corps.classList.toggle("masque");
    bloc.append(entete, corps);
    conteneur.append(bloc);
  });
}

function afficherPaiements(credits) {
  const versements = credits.flatMap(credit =>
    credit.paiements.map(paiement => ({ ...paiement, credit: credit.identifiant })));
  versements.sort((a, b) => b.date.localeCompare(a.date));

  const corps = $("#liste-paiements-client");
  corps.innerHTML = versements.length
    ? versements.map(versement => `
        <tr><td>${formaterDate(versement.date)}</td>
        <td>${versement.credit}</td>
        <td class="montant">${montant(versement.montant)}</td>
        <td>${versement.canal || "—"}</td></tr>`).join("")
    : '<tr><td colspan="4" class="etat-vide">Aucun versement enregistré.</td></tr>';
}

function afficherChronologie(evenements) {
  const conteneur = $("#fiche-chronologie");
  conteneur.replaceChildren();
  if (!evenements.length) {
    conteneur.innerHTML = etatVide("Aucun événement enregistré.");
    return;
  }

  const parAnnee = new Map();
  evenements.forEach(evenement => {
    const annee = evenement.date.slice(0, 4);
    if (!parAnnee.has(annee)) parAnnee.set(annee, []);
    parAnnee.get(annee).push(evenement);
  });

  parAnnee.forEach((liste, annee) => {
    const bloc = creer("div", { className: "annee" });
    bloc.innerHTML = `<h3>${annee}</h3><div class="evenements">${liste.map(evenement => `
      <div class="evenement ${evenement.type}">
        <strong>${evenement.libelle}</strong>
        <span>${evenement.detail || ""}</span>
        <time>${formaterDate(evenement.date)}</time>
      </div>`).join("")}</div>`;
    conteneur.append(bloc);
  });
}

/* ---------- Pièces du dossier ---------- */

export function gabaritPieces(donnees, { avecActions = true } = {}) {
  const parCategorie = new Map();
  donnees.documents.forEach(document_ => {
    if (!parCategorie.has(document_.categorie)) parCategorie.set(document_.categorie, []);
    parCategorie.get(document_.categorie).push(document_);
  });

  return donnees.categories.map(categorie => {
    const pieces = parCategorie.get(categorie.code) || [];
    if (!pieces.length) {
      return `<div class="piece manquante">
        <span class="etat">○</span>
        <span class="description"><strong>${categorie.libelle}</strong><span>Manquant</span></span>
        ${avecActions ? `<button class="bouton-discret" data-ajouter-piece="${categorie.code}">Ajouter</button>` : ""}
      </div>`;
    }
    return pieces.map(piece => `
      <div class="piece presente">
        <span class="etat">✓</span>
        <span class="description"><strong>${categorie.libelle}</strong>
          <span>${piece.nom_original} · ${taille(piece.taille_octets)} · ajouté le ${formaterDate(piece.televerse_le)}</span></span>
        <a class="bouton-discret" href="${piece.url}" target="_blank">Voir</a>
        ${avecActions ? `<button class="action-icone supprimer" data-supprimer-piece="${piece.identifiant}" title="Supprimer">${ICONE_CORBEILLE}</button>` : ""}
      </div>`).join("");
  }).join("");
}

export async function chargerDocuments(identifiantClient) {
  const donnees = await api(`/api/clients/${identifiantClient}/documents/`);
  const presentes = donnees.categories.filter(categorie => categorie.present).length;
  $("#fiche-pieces-compte").textContent = `${presentes} / ${donnees.categories.length}`;
  $("#fiche-documents").innerHTML = gabaritPieces(donnees);

  $$("#fiche-documents [data-ajouter-piece]").forEach(bouton => {
    bouton.onclick = () => {
      $("#categorie-document").value = bouton.dataset.ajouterPiece;
      $("#fichier-document").click();
    };
  });
  $$("#fiche-documents [data-supprimer-piece]").forEach(bouton => {
    bouton.onclick = async () => {
      if (!confirm("Supprimer ce document ?")) return;
      await api(`/api/documents/${bouton.dataset.supprimerPiece}/supprimer/`, { method: "DELETE" });
      chargerDocuments(identifiantClient);
    };
  });
}

async function envoyerDocument(fichier) {
  if (!clientAffiche || !fichier) return;
  const donnees = new FormData();
  donnees.append("fichier", fichier);
  donnees.append("categorie", $("#categorie-document").value || "autre");
  $("#message-document").textContent = "Envoi en cours…";
  try {
    await api(`/api/clients/${clientAffiche.identifiant}/documents/televerser/`, { method: "POST", body: donnees });
    $("#message-document").textContent = "";
    chargerDocuments(clientAffiche.identifiant);
  } catch (erreur) {
    $("#message-document").textContent = erreur.message;
  }
}
