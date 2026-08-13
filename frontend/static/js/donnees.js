/* Import de données et qualité : déposer, contrôler, corriger, confirmer. */

import { $, api, nombre } from "./noyau.js";
import { enregistrerChargeur, ouvrir } from "./navigation.js";

const NOMBRE_ETAPES = 4;
let etape = 1;
let fichiers = [];
let rapport = null;
let apresImport = () => {};

export function brancherDonnees({ rafraichir }) {
  apresImport = rafraichir;
  enregistrerChargeur("importer", () => afficherEtape());

  const zone = $("#zone-import");
  $("#fichiers-institution").onchange = evenement => valider(evenement.target.files);
  ["dragenter", "dragover"].forEach(type => zone.addEventListener(type, evenement => {
    evenement.preventDefault();
    zone.classList.add("survol");
  }));
  ["dragleave", "drop"].forEach(type => zone.addEventListener(type, evenement => {
    evenement.preventDefault();
    zone.classList.remove("survol");
  }));
  zone.addEventListener("drop", evenement => valider(evenement.dataTransfer.files));

  $("#import-precedent").onclick = () => { etape = Math.max(1, etape - 1); afficherEtape(); };
  $("#import-suivant").onclick = () => { etape = Math.min(NOMBRE_ETAPES, etape + 1); afficherEtape(); };
  $("#confirmer-import").onclick = confirmer;
}

function afficherEtape() {
  for (let numero = 1; numero <= NOMBRE_ETAPES; numero += 1) {
    $("#import-etape-" + numero).classList.toggle("masque", numero !== etape);
  }
  document.querySelectorAll("#etapes-import li").forEach(element => {
    const numero = +element.dataset.etapeImport;
    element.classList.toggle("active", numero === etape);
    element.classList.toggle("faite", numero < etape);
  });
  $("#import-precedent").disabled = etape === 1;
  $("#import-suivant").classList.toggle("masque", etape >= NOMBRE_ETAPES || !rapport);
  $("#confirmer-import").classList.toggle("masque", etape !== NOMBRE_ETAPES || !rapport?.valide);
}

function donneesFichiers() {
  const donnees = new FormData();
  fichiers.forEach(fichier => donnees.append("fichiers", fichier));
  return donnees;
}

async function valider(liste) {
  fichiers = [...liste];
  $("#etat-import").textContent = `${fichiers.length} fichier(s) déposé(s), contrôle en cours…`;
  try {
    rapport = await api("/api/imports-csv/valider/", { method: "POST", body: donneesFichiers() });
  } catch (erreur) {
    rapport = { valide: false, erreurs: [erreur.message], avertissements: [], anomalies: [], lignes: {} };
  }
  afficherControle();
  afficherAnomalies();
  afficherConfirmation();
  afficherRapportQualite();
  etape = 2;
  afficherEtape();
}

function afficherControle() {
  const lignesParFichier = rapport.lignes || {};
  const anomaliesParFichier = {};
  (rapport.anomalies || []).forEach(anomalie => {
    anomaliesParFichier[anomalie.fichier] = (anomaliesParFichier[anomalie.fichier] || 0) + 1;
  });

  const noms = Object.keys(lignesParFichier).sort();
  $("#import-fichiers").innerHTML = noms.length
    ? `<div class="tableau-wrap"><table class="donnees-tableau">
        <thead><tr><th>Fichier</th><th class="montant">Lignes</th><th>État</th></tr></thead>
        <tbody>${noms.map(nom => {
          const anomalies = anomaliesParFichier[nom] || 0;
          return `<tr><td class="principale">${nom}</td>
            <td class="montant">${nombre(lignesParFichier[nom])}</td>
            <td>${anomalies
              ? `<span class="badge-statut en_retard">${anomalies} anomalie${anomalies > 1 ? "s" : ""}</span>`
              : '<span class="badge-statut solde">conforme</span>'}</td></tr>`;
        }).join("")}</tbody></table></div>`
    : '<div class="encart danger">Aucun fichier exploitable n\'a été lu.</div>';

  const erreurs = rapport.erreurs || [];
  const avertissements = rapport.avertissements || [];
  $("#import-synthese").innerHTML = `
    <div class="chiffres">
      <div><span>Qualité</span><strong>${rapport.qualite != null ? rapport.qualite + " %" : "—"}</strong></div>
      <div><span>Lignes contrôlées</span><strong>${nombre(rapport.total_lignes)}</strong></div>
      <div class="danger"><span>Erreurs</span><strong>${erreurs.length}</strong></div>
      <div class="alerte"><span>Avertissements</span><strong>${avertissements.length}</strong></div>
    </div>
    ${erreurs.length ? `<div class="encart danger" style="margin-top:16px">${erreurs.map(e => `<div>${e}</div>`).join("")}</div>` : ""}
    ${avertissements.length ? `<p class="sous-titre" style="margin-top:12px">${avertissements.join(" ")}</p>` : ""}`;
}

function tableauAnomalies(anomalies) {
  return `<div class="tableau-wrap"><table class="donnees-tableau">
    <thead><tr><th>Fichier</th><th>Ligne</th><th>Type</th><th>Détail</th></tr></thead>
    <tbody>${anomalies.map(anomalie => `
      <tr><td class="principale">${anomalie.fichier}</td><td>${anomalie.ligne}</td>
      <td>${anomalie.type}</td><td>${anomalie.detail}</td></tr>`).join("")}</tbody></table></div>`;
}

function afficherAnomalies() {
  const anomalies = rapport.anomalies || [];
  $("#import-anomalies").innerHTML = anomalies.length
    ? tableauAnomalies(anomalies)
    : '<p class="sous-titre">Aucune anomalie relevée sur ce lot.</p>';
}

function afficherConfirmation() {
  $("#import-confirmation").innerHTML = rapport.valide
    ? `<p class="sous-titre">${nombre(rapport.total_lignes)} lignes seront intégrées. Les clients déjà connus sont mis à jour, pas dupliqués.</p>
       ${(rapport.avertissements || []).length
         ? '<div class="encart attention" style="margin-top:14px">Des avertissements subsistent : ils n\'empêchent pas l\'import.</div>' : ""}`
    : '<div class="encart danger">Le lot contient des erreurs bloquantes. Corrigez les fichiers à la source, puis redéposez-les.</div>';
}

function afficherRapportQualite() {
  const conteneur = $("#rapport-import");
  const anomalies = rapport.anomalies || [];
  conteneur.className = anomalies.length ? "" : "etat-vide";
  conteneur.innerHTML = anomalies.length
    ? `<p class="sous-titre" style="margin-bottom:14px">${anomalies.length} anomalie(s) relevée(s) lors du dernier contrôle.</p>${tableauAnomalies(anomalies)}`
    : "Aucune anomalie lors du dernier contrôle.";
}

async function confirmer() {
  $("#message-import").textContent = "Import en cours…";
  try {
    const resultat = await api("/api/imports-csv/confirmer/", { method: "POST", body: donneesFichiers() });
    $("#message-import").textContent =
      `${resultat.clients_ajoutes} client(s) ajouté(s), ${resultat.credits_importes} crédit(s) importé(s).`;
    await apresImport();
    ouvrir("clients");
  } catch (erreur) {
    $("#message-import").textContent = erreur.message;
  }
}
