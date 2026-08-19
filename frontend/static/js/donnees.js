/* Import de données et qualité : déposer, contrôler, corriger, confirmer. */

import { $, api, nombre } from "./noyau.js";
import { enregistrerChargeur, ouvrir } from "./navigation.js";

const NOMBRE_ETAPES = 4;
let etape = 1;
let fichiers = [];
let rapport = null;
let apresImport = () => {};
let fichierAnalyse = null;
let analyseExport = null;
let lotAcquisition = [];

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

  const zoneAnalyse = $("#zone-analyse-export");
  $("#fichier-analyse-export").onchange = evenement => analyserExport(evenement.target.files[0]);
  ["dragenter", "dragover"].forEach(type => zoneAnalyse.addEventListener(type, evenement => {
    evenement.preventDefault(); zoneAnalyse.classList.add("survol");
  }));
  ["dragleave", "drop"].forEach(type => zoneAnalyse.addEventListener(type, evenement => {
    evenement.preventDefault(); zoneAnalyse.classList.remove("survol");
  }));
  zoneAnalyse.addEventListener("drop", evenement => analyserExport(evenement.dataTransfer.files[0]));
}

function echapper(valeur) {
  return String(valeur ?? "").replace(/[&<>\"]/g, caractere => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[caractere]);
}

function formaterValeur(valeur) {
  const texte = String(valeur ?? "");
  return texte.length > 48 ? `${echapper(texte.slice(0, 45))}…` : echapper(texte);
}

async function analyserExport(fichier, feuille = "") {
  if (!fichier) return;
  fichierAnalyse = fichier;
  $("#etat-analyse-export").textContent = `Lecture de ${fichier.name}…`;
  const donnees = new FormData();
  donnees.append("fichier", fichier);
  if (feuille) donnees.append("feuille", feuille);
  try {
    analyseExport = await api("/api/acquisition/analyser-fichier/", { method: "POST", body: donnees });
    $("#etat-analyse-export").textContent = `${analyseExport.fichier.lignes} lignes et ${analyseExport.fichier.colonnes} colonnes lues. ${analyseExport.message}`;
    afficherChoixFeuille();
    afficherAnalyseExport();
  } catch (erreur) {
    analyseExport = null;
    $("#etat-analyse-export").textContent = erreur.message;
    $("#resultat-analyse-export").classList.add("masque");
  }
}

function afficherChoixFeuille() {
  const conteneur = $("#choix-feuille-export");
  const feuilles = analyseExport.feuilles || [];
  if (feuilles.length < 2) { conteneur.classList.add("masque"); return; }
  conteneur.classList.remove("masque");
  const active = analyseExport.fichier.feuille || feuilles[0];
  conteneur.innerHTML = `<label>Feuille à analyser<select id="feuille-export">${feuilles.map(nom => `<option value="${echapper(nom)}" ${nom === active ? "selected" : ""}>${echapper(nom)}</option>`).join("")}</select></label>`;
  $("#feuille-export").onchange = evenement => analyserExport(fichierAnalyse, evenement.target.value);
}

function optionsTables(selection) {
  return `<option value="">Choisir une table…</option>${analyseExport.referentiel.map(table => `<option value="${table.code}" ${selection === table.code ? "selected" : ""}>${echapper(table.libelle)}</option>`).join("")}`;
}

function optionsChamps(tableCode, selection) {
  const table = analyseExport.referentiel.find(element => element.code === tableCode);
  if (!table) return '<option value="">Ignorer cette colonne</option>';
  return `<option value="">Ignorer cette colonne</option>${table.champs.map(champ => `<option value="${champ.code}" ${selection === champ.code ? "selected" : ""}>${echapper(champ.libelle)}${champ.obligatoire ? " *" : ""}</option>`).join("")}`;
}

function afficherAnalyseExport() {
  const conteneur = $("#resultat-analyse-export");
  const correspondance = analyseExport.correspondance;
  conteneur.classList.remove("masque");
  conteneur.innerHTML = `
    <div class="grille-2" style="margin-bottom:18px">
      <div><span class="surtexte">Table cible</span><label>Nature de cet export<select id="table-export">${optionsTables(correspondance.table)}</select></label><p class="sous-titre" style="margin-top:8px">Un fichier correspond à une table métier. Vous pourrez analyser les autres exports du même lot ensuite.</p></div>
      <div><span class="surtexte">Aperçu source</span><p class="sous-titre">${echapper(analyseExport.fichier.nom)} · ${nombre(analyseExport.fichier.lignes)} lignes · ${nombre(analyseExport.fichier.colonnes)} colonnes</p></div>
    </div>
    <div class="tableau-wrap"><table class="donnees-tableau"><thead><tr><th>Colonne source</th><th>Exemple</th><th>Champ CIF</th><th>Proposition</th></tr></thead><tbody>
      ${correspondance.colonnes.map(colonne => `<tr data-colonne="${echapper(colonne.colonne)}"><td class="principale">${echapper(colonne.colonne)}</td><td>${formaterValeur(analyseExport.apercu[0]?.[colonne.colonne])}</td><td><select class="champ-export">${optionsChamps(correspondance.table, colonne.champ)}</select></td><td><span class="secondaire">${echapper(colonne.motif)}</span></td></tr>`).join("")}
    </tbody></table></div>
    <div class="actions" style="margin-top:16px"><button id="controler-correspondance" class="bouton-principal" type="button">Contrôler cette correspondance</button><span id="message-correspondance" class="message"></span></div>
    <div id="rapport-correspondance" class="masque" style="margin-top:18px"></div>`;
  $("#table-export").onchange = evenement => {
    correspondance.table = evenement.target.value;
    correspondance.colonnes.forEach(colonne => { colonne.champ = ""; });
    afficherAnalyseExport();
  };
  conteneur.querySelectorAll(".champ-export").forEach((selecteur, index) => {
    selecteur.onchange = evenement => { correspondance.colonnes[index].champ = evenement.target.value; };
  });
  $("#controler-correspondance").onclick = controlerCorrespondance;
}

async function controlerCorrespondance() {
  const correspondance = analyseExport.correspondance;
  $("#message-correspondance").textContent = "Contrôle qualité en cours…";
  const donnees = new FormData();
  donnees.append("fichier", fichierAnalyse);
  donnees.append("correspondance", JSON.stringify({ table: correspondance.table, colonnes: correspondance.colonnes.map(({ colonne, champ }) => ({ colonne, champ })) }));
  if (analyseExport.fichier.feuille) donnees.append("feuille", analyseExport.fichier.feuille);
  try {
    const resultat = await api("/api/acquisition/valider-correspondance/", { method: "POST", body: donnees });
    $("#message-correspondance").textContent = resultat.message;
    afficherRapportCorrespondance(resultat);
  } catch (erreur) { $("#message-correspondance").textContent = erreur.message; }
}

function afficherRapportCorrespondance(resultat) {
  const conteneur = $("#rapport-correspondance");
  conteneur.classList.remove("masque");
  const diagnostic = resultat.prediagnostic;
  conteneur.innerHTML = `<div class="section" style="margin:0"><header><h3>Résultat du contrôle</h3><span class="badge">${echapper(resultat.libelle_table)}</span></header>${gabaritDimensions(resultat.rapport)}<div class="encart information" style="margin-top:14px">${echapper(resultat.message)}</div>${resultat.rapport.integrable ? '<div class="actions" style="margin-top:14px"><button id="ajouter-au-lot" class="bouton-principal" type="button">Ajouter cet export au lot</button></div>' : ""}</div>
    <div class="section" style="margin-top:18px"><header><div><h3>Pré-diagnostic de préparation au scoring</h3><p class="sous-titre">${echapper(diagnostic.constat)}</p></div><span class="badge">${echapper(diagnostic.libelle)}</span></header>
      <div class="puces">${diagnostic.sources_requises.map(source => `<span class="puce ${source.recu ? "active" : ""}">${source.recu ? "✓" : "○"} ${echapper(source.libelle)}</span>`).join("")}</div>
      <div class="encart attention" style="margin-top:14px"><strong>Étapes nécessaires</strong>${diagnostic.actions.map(action => `<div>${echapper(action)}</div>`).join("")}</div>
    </div>`;
  if (resultat.rapport.integrable) $("#ajouter-au-lot").onclick = () => ajouterAuLot(resultat);
}

function ajouterAuLot(resultat) {
  const correspondance = analyseExport.correspondance;
  const entree = {
    fichier: fichierAnalyse,
    feuille: analyseExport.fichier.feuille || "",
    table: correspondance.table,
    colonnes: correspondance.colonnes.map(({ colonne, champ }) => ({ colonne, champ })),
    lignes: analyseExport.fichier.lignes,
    libelle: resultat.libelle_table,
  };
  lotAcquisition = [...lotAcquisition.filter(element => element.table !== entree.table), entree];
  $("#message-correspondance").textContent = `${entree.libelle} ajouté au lot de préparation.`;
  afficherLotAcquisition();
}

function donneesLot() {
  const donnees = new FormData();
  lotAcquisition.forEach(element => donnees.append("fichiers", element.fichier));
  donnees.append("correspondances", JSON.stringify(lotAcquisition.map(({ table, feuille, colonnes }) => ({ table, feuille, colonnes }))));
  return donnees;
}

function afficherLotAcquisition(resultat = null) {
  const conteneur = $("#lot-acquisition");
  if (!lotAcquisition.length) { conteneur.classList.add("masque"); return; }
  conteneur.classList.remove("masque");
  conteneur.innerHTML = `<div class="section" style="margin:0"><header><div><h3>Lot de préparation</h3><p class="sous-titre">Chaque export a été mappé individuellement. Contrôlez le lot complet avant l'import.</p></div><span class="badge">${lotAcquisition.length} export(s)</span></header>
    <div class="tableau-wrap"><table class="donnees-tableau"><thead><tr><th>Table</th><th>Fichier</th><th class="montant">Lignes</th><th></th></tr></thead><tbody>${lotAcquisition.map(element => `<tr><td class="principale">${echapper(element.libelle)}</td><td>${echapper(element.fichier.name)}</td><td class="montant">${nombre(element.lignes)}</td><td><button class="bouton-secondaire retirer-lot" data-table="${echapper(element.table)}" type="button">Retirer</button></td></tr>`).join("")}</tbody></table></div>
    <div class="actions" style="margin-top:16px"><button id="controler-lot" class="bouton-principal" type="button">Contrôler le lot complet</button>${resultat?.rapport?.integrable ? '<button id="importer-lot" class="bouton-principal" type="button">Importer le lot</button>' : ""}<span id="message-lot" class="message"></span></div>
    <div id="diagnostic-lot" ${resultat ? "" : 'class="masque"'} style="margin-top:16px"></div></div>`;
  conteneur.querySelectorAll(".retirer-lot").forEach(bouton => bouton.onclick = () => {
    lotAcquisition = lotAcquisition.filter(element => element.table !== bouton.dataset.table); afficherLotAcquisition();
  });
  $("#controler-lot").onclick = controlerLot;
  if (resultat?.rapport?.integrable) $("#importer-lot").onclick = importerLot;
  if (resultat) afficherDiagnosticLot(resultat.diagnostic, resultat.rapport);
}

function afficherDiagnosticLot(diagnostic, rapport) {
  const conteneur = $("#diagnostic-lot");
  conteneur.classList.remove("masque");
  conteneur.innerHTML = `<div class="encart ${diagnostic.niveau === "exploration_possible" ? "information" : "attention"}"><strong>${echapper(diagnostic.libelle)}</strong><div>${echapper(diagnostic.constat)}</div></div>
    <div class="puces" style="margin-top:12px">${diagnostic.sources.map(source => `<span class="puce ${source.recu ? "active" : ""}">${source.recu ? "✓" : "○"} ${echapper(source.libelle)}${source.recu ? ` (${nombre(source.lignes)})` : ""}</span>`).join("")}</div>
    <div class="grille-2" style="margin-top:14px"><div class="encart"><strong>Période observée</strong><div>${diagnostic.periode.debut ? `${echapper(diagnostic.periode.debut)} au ${echapper(diagnostic.periode.fin)}` : "Aucune date exploitable dans ce lot."}</div></div><div class="encart"><strong>Conditions du modèle</strong><div>Données T0 : non vérifiées · Cible de défaut : non définie</div></div></div>
    <div class="encart attention" style="margin-top:12px"><strong>Suite à donner</strong>${diagnostic.actions.map(action => `<div>${echapper(action)}</div>`).join("")}</div>${gabaritDimensions(rapport)}`;
}

async function controlerLot() {
  $("#message-lot").textContent = "Contrôle relationnel du lot en cours…";
  try {
    const resultat = await api("/api/acquisition/valider-lot/", { method: "POST", body: donneesLot() });
    $("#message-lot").textContent = "Lot contrôlé. Aucune donnée n'a encore été ajoutée.";
    afficherLotAcquisition(resultat);
  } catch (erreur) { $("#message-lot").textContent = erreur.message; }
}

async function importerLot() {
  $("#message-lot").textContent = "Import du lot en cours…";
  try {
    const resultat = await api("/api/acquisition/confirmer-lot/", { method: "POST", body: donneesLot() });
    $("#message-lot").textContent = `${nombre(resultat.clients_ajoutes)} client(s) ajouté(s). Les dossiers et historiques sont maintenant consultables.`;
    await apresImport();
    afficherLotAcquisition(resultat);
    window.setTimeout(() => ouvrir("clients"), 700);
  } catch (erreur) { $("#message-lot").textContent = erreur.message; }
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

function afficherControle(rapport) {
  const lignesParFichier = rapport.lignes || {};
  const fichiers = Object.keys(lignesParFichier).sort();

  $("#import-fichiers").innerHTML = fichiers.length ? `
    <div class="tableau-wrap">
      <table class="donnees-tableau">
        <thead><tr><th>Fichier</th><th class="montant">Lignes</th></tr></thead>
        <tbody>${fichiers.map(nom => `
          <tr><td class="principale">${nom}.csv</td>
          <td class="montant">${nombre(lignesParFichier[nom])}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>` : "<div class=\"encart danger\">Aucun fichier exploitable n'a été lu.</div>";

  $("#import-synthese").innerHTML = gabaritDimensions(rapport);
}

/* Six dimensions séparées, jamais un pourcentage global : un chiffre unique
   ne dit ni quoi corriger, ni si le lot est utilisable. */
function gabaritDimensions(rapport) {
  const marques = { ok: "✓", avertissement: "⚠", erreur: "✕", non_verifiable: "○" };
  const sens = { ok: "favorable", avertissement: "attention", erreur: "attention", non_verifiable: "absent" };
  const dimensions = rapport.dimensions || [];

  return `
    <div class="tableau-wrap">
      <table class="donnees-tableau">
        <thead><tr><th></th><th>Dimension</th><th>Question contrôlée</th><th>Constat</th></tr></thead>
        <tbody>${dimensions.map(d => `
          <tr>
            <td><span class="point ${sens[d.statut] || ""}"><span class="marque">${marques[d.statut] || "·"}</span></span></td>
            <td class="principale">${d.libelle}</td>
            <td><span class="secondaire">${d.question}</span></td>
            <td>${d.constat}</td>
          </tr>`).join("")}
        </tbody>
      </table>
    </div>
    ${(rapport.erreurs || []).length ? `<div class="encart danger" style="margin-top:14px">
      <strong>Erreurs bloquantes</strong>${rapport.erreurs.map(e => `<div>${e}</div>`).join("")}</div>` : ""}
    ${(rapport.avertissements || []).length ? `<div class="encart attention" style="margin-top:12px">
      <strong>Avertissements</strong>${rapport.avertissements.map(a => `<div>${a}</div>`).join("")}</div>` : ""}
    <p class="sous-titre" style="margin-top:12px">L'exactitude ne se contrôle pas depuis un fichier : elle demande une visite, une pièce justificative ou un recoupement externe.</p>`;
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
  $("#import-confirmation").innerHTML = rapport.integrable
    ? `<p class="sous-titre">${nombre(rapport.total_lignes)} lignes seront intégrées. Les clients déjà connus sont mis à jour, pas dupliqués.</p>
       ${(rapport.avertissements || []).length
         ? '<div class="encart attention" style="margin-top:14px">Des avertissements subsistent : ils n\'empêchent pas l\'import.</div>' : ""}`
    : '<div class="encart danger">Le lot contient des erreurs bloquantes. Corrigez les fichiers à la source, puis redéposez-les.</div>';
}

function afficherRapportQualite(rapport) {
  const conteneur = $("#rapport-import");
  const anomalies = rapport.anomalies || [];
  conteneur.className = "";
  conteneur.innerHTML = gabaritDimensions(rapport)
    + (anomalies.length
      ? `<h3 style="margin:22px 0 12px">Anomalies relevées</h3>${tableauAnomalies(anomalies)}`
      : '<p class="sous-titre" style="margin-top:18px">Aucune anomalie ligne à ligne.</p>');
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
