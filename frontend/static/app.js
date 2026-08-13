/* Poste de travail de l'agent de crédit.

   Le code est volontairement écrit en clair, fonction par fonction : ce
   prototype sert de support de discussion métier, il doit rester lisible et
   modifiable rapidement pendant ou après une visite terrain. */

const $ = selecteur => document.querySelector(selecteur);
const $$ = selecteur => [...document.querySelectorAll(selecteur)];

let fichiersSelectionnes = [];
let rapportImport = null;
let pageClients = 1;
let clientAffiche = null;
let dossierAffiche = null;

const TITRES = {
  "tableau-bord": ["Tableau de bord", "Suivez votre portefeuille de crédit."],
  portefeuille: ["Portefeuille", "Vue d'ensemble du portefeuille par agence, produit et secteur."],
  demandes: ["Demandes de crédit", "Instruisez les demandes et suivez les décisions."],
  clients: ["Clients", "Créez, recherchez et consultez les dossiers clients."],
  "fiche-client": ["Dossier client", "Situation, historique et parcours du client."],
  credits: ["Crédits", "Crédits décaissés et suivis par l'institution."],
  remboursements: ["Échéances & remboursements", "Versements reçus sur les crédits en cours."],
  retards: ["Retards", "Échéances impayées et suivi du recouvrement."],
  importer: ["Importer des données", "Chargez et contrôlez un lot de fichiers CSV."],
  qualite: ["Qualité des données", "Anomalies détectées avant intégration."],
  produits: ["Produits de crédit", "Paramétrage des produits proposés par l'institution."],
  regles: ["Règles d'analyse", "Règles appliquées lors de l'analyse préliminaire."],
  configuration: ["Institution", "Informations de votre organisation."],
  audit: ["Journal d'audit", "Traçabilité des opérations effectuées."],
};

/* Les écrans encore à construire annoncent leur contenu et la question à poser
   à l'institution. Un écran vide serait un trou ; celui-ci est un support
   d'entretien. */
const ECRANS_PREVUS = {
  portefeuille: {
    titre: "Portefeuille crédit",
    intention: "Vue filtrable du portefeuille : agence, produit, secteur, période et statut.",
    contenu: ["Crédits actifs, montant décaissé et encours", "Crédits récents et échéances prochaines", "Répartition par produit et par secteur"],
    question: "Quels indicateurs utilisez-vous réellement pour piloter votre portefeuille ?",
  },
  retards: {
    titre: "Retards et recouvrement",
    intention: "Liste des échéances impayées, avec le détail de chaque crédit concerné.",
    contenu: ["Client, crédit, montant attendu, montant payé, reste dû", "Ancienneté du retard en jours", "Historique des versements du crédit"],
    question: "Que faites-vous concrètement lorsqu'une échéance n'est pas payée, et à partir de quand intervenez-vous ?",
  },
  produits: {
    titre: "Produits de crédit",
    intention: "Chaque institution définit ses propres produits ; rien n'est figé dans l'application.",
    contenu: ["Libellé, montants et durées possibles", "Périodicité et mode de remboursement", "Secteurs visés et pièces exigées"],
    question: "Qu'est-ce qui différencie réellement vos produits les uns des autres ?",
  },
  regles: {
    titre: "Règles d'analyse",
    intention: "Règles appliquées à l'analyse préliminaire, visibles et désactivables une par une.",
    contenu: ["Complétude du dossier", "Capacité de remboursement déclarée", "Disponibilité d'un historique interne"],
    question: "Chez vous, comment ces règles fonctionnent-elles, et lesquelles manquent ?",
  },
};

const LIBELLES_STATUT_CREDIT = {
  SOLDE: "Soldé",
  SOLDE_AVEC_RETARD: "Soldé avec retard",
  EN_COURS: "En cours",
  EN_RETARD: "En retard",
  SANS_ECHEANCIER: "Sans échéancier",
};

/* ---------- Utilitaires ---------- */

const formaterNombre = valeur => new Intl.NumberFormat("fr-FR").format(valeur || 0);
const formaterMontant = valeur => formaterNombre(valeur) + " F";

function formaterDate(texte) {
  if (!texte) return "—";
  const [annee, mois, jour] = texte.slice(0, 10).split("-");
  return `${jour}/${mois}/${annee}`;
}

function initiales(nom) {
  return (nom || "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map(mot => mot[0].toUpperCase())
    .join("");
}

function classeStatut(statut) {
  return (statut || "inconnu").toLowerCase();
}

async function api(url, options = {}) {
  const reponse = await fetch(url, options);
  const donnees = await reponse.json();
  if (!reponse.ok) throw new Error(donnees.erreur || "Opération impossible");
  return donnees;
}

function creer(balise, proprietes = {}) {
  return Object.assign(document.createElement(balise), proprietes);
}

function boutonAction(classe, libelle, icone) {
  const bouton = creer("button", { className: "action-icone " + classe, type: "button", title: libelle, innerHTML: icone });
  bouton.setAttribute("aria-label", libelle);
  return bouton;
}

const ICONE_OEIL = '<svg viewBox="0 0 24 24"><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.6"/></svg>';
const ICONE_CRAYON = '<svg viewBox="0 0 24 24"><path d="m4 16.5-.8 4.3 4.3-.8L19 8.5 15.5 5 4 16.5Z"/><path d="m13.8 6.7 3.5 3.5"/></svg>';
const ICONE_CORBEILLE = '<svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3m-8 0 1 13h8l1-13M10 11v5m4-5v5"/></svg>';

/* ---------- Navigation ---------- */

function ouvrir(vue) {
  $$(".vue").forEach(section => section.classList.toggle("vue-masque", section.id !== vue));
  $$(".barre-laterale nav button").forEach(bouton => bouton.classList.toggle("nav-actif", bouton.dataset.vue === vue));

  const [titre, description] = TITRES[vue] || ["", ""];
  $("#titre-vue").textContent = titre;
  $("#description-vue").textContent = description;

  if (vue === "clients") chargerClients();
  if (vue === "demandes") chargerDemandes();
  if (["credits", "remboursements", "audit"].includes(vue)) chargerListeSimple(vue);
  if (ECRANS_PREVUS[vue]) afficherEcranPrevu(vue);
}

function afficherEcranPrevu(vue) {
  const ecran = ECRANS_PREVUS[vue];
  const conteneur = $(`.ecran-prevu[data-ecran="${vue}"]`);
  conteneur.replaceChildren();
  conteneur.insertAdjacentHTML("beforeend", `
    <p class="surtexte">Écran prévu</p>
    <h2>${ecran.titre}</h2>
    <p class="sous-titre" style="margin-top:6px">${ecran.intention}</p>
    <ul>${ecran.contenu.map(ligne => `<li>${ligne}</li>`).join("")}</ul>
    <div class="question-metier"><strong>Question à poser</strong>${ecran.question}</div>
  `);
}

/* ---------- Tableau de bord ---------- */

async function chargerTableauBord() {
  const donnees = await api("/api/tableau-bord/");
  $("#date-observation").textContent = formaterDate(donnees.date_observation);

  $("#kpi-clients").textContent = formaterNombre(donnees.clients);
  $("#kpi-clients-actifs").textContent = `${formaterNombre(donnees.clients_avec_credit_actif)} avec un crédit en cours`;
  $("#kpi-demandes").textContent = formaterNombre(donnees.demandes_en_cours);
  $("#kpi-demandes-detail").textContent = `${donnees.demandes_a_analyser} à analyser · ${donnees.demandes_en_attente_decision} en attente de décision`;
  $("#kpi-credits-actifs").textContent = formaterNombre(donnees.credits_actifs);
  $("#kpi-credits-total").textContent = `${formaterNombre(donnees.credits)} crédits enregistrés`;
  $("#kpi-encours").textContent = formaterMontant(donnees.encours);
  $("#kpi-decaisse").textContent = `${formaterMontant(donnees.montant_decaisse)} décaissés au total`;

  $("#kpi-echeances-jour").textContent = formaterNombre(donnees.echeances_du_jour);
  $("#kpi-echeances-jour-montant").textContent = formaterMontant(donnees.montant_echeances_du_jour);
  $("#kpi-echeances-venir").textContent = formaterNombre(donnees.echeances_a_venir);
  $("#kpi-echeances-venir-montant").textContent = formaterMontant(donnees.montant_echeances_a_venir);
  $("#kpi-retards").textContent = formaterNombre(donnees.echeances_en_retard);
  $("#kpi-retards-montant").textContent = `${formaterMontant(donnees.montant_en_retard)} restant dus`;
  $("#kpi-credits-retard").textContent = formaterNombre(donnees.credits_en_retard);

  const compteur = $("#compteur-nav-demandes");
  compteur.textContent = donnees.demandes_en_cours;
  compteur.classList.toggle("masque", donnees.demandes_en_cours === 0);

  afficherDemandesAttention(donnees.demandes_attention);
  afficherTranchesRetard(donnees.tranches_retard);
}

function afficherDemandesAttention(demandes) {
  const conteneur = $("#liste-attention");
  conteneur.replaceChildren();
  if (!demandes.length) {
    conteneur.append(creer("p", { className: "sous-titre", textContent: "Aucune demande en attente." }));
    return;
  }
  demandes.forEach(demande => {
    const ligne = creer("div", { className: "ligne-attention" });
    ligne.insertAdjacentHTML("beforeend", `
      <div class="identite"><strong>${demande.client}</strong><span>${demande.duree_mois} mois · ${demande.etat}</span></div>
      <div class="montant">${formaterMontant(demande.montant_demande)}</div>
    `);
    const action = boutonAction("details", "Ouvrir le dossier client", ICONE_OEIL);
    action.onclick = () => ouvrirFicheClient(demande.identifiant_client);
    ligne.append(action);
    conteneur.append(ligne);
  });
}

function afficherTranchesRetard(tranches) {
  const conteneur = $("#liste-tranches");
  conteneur.replaceChildren();
  if (!tranches.length) {
    conteneur.append(creer("p", { className: "sous-titre", textContent: "Aucune échéance en retard." }));
    return;
  }
  tranches.forEach(tranche => {
    const ligne = creer("div", { className: "ligne-repartition" });
    ligne.append(creer("span", { textContent: `Retard de ${tranche.libelle}` }));
    ligne.append(creer("strong", { textContent: `${tranche.nombre} échéance${tranche.nombre > 1 ? "s" : ""}` }));
    conteneur.append(ligne);
  });
}

/* ---------- Clients ---------- */

async function chargerClients() {
  const recherche = encodeURIComponent($("#recherche-clients").value || "");
  const reponse = await api(`/api/clients/?page=${pageClients}&recherche=${recherche}`);
  const corps = $("#liste-clients");
  corps.replaceChildren();

  if (!reponse.resultats.length) {
    corps.innerHTML = '<tr><td colspan="5">Aucun client.</td></tr>';
  }

  reponse.resultats.forEach(client => {
    const ligne = creer("tr");
    const celluleNom = creer("td");
    celluleNom.append(creer("span", { className: "cellule-principale", textContent: client.nom_complet }));
    if (client.identifiant_source) {
      celluleNom.append(creer("span", { className: "cellule-secondaire", textContent: client.identifiant_source }));
    }
    ligne.append(
      celluleNom,
      creer("td", { textContent: client.secteur_activite }),
      creer("td", { textContent: `${client.anciennete_activite_mois} mois` }),
      creer("td", { textContent: client.identifiant_source ? "Importé" : "Saisi" }),
    );

    const actions = creer("td", { className: "actions-tableau" });
    const details = boutonAction("details", "Ouvrir le dossier", ICONE_OEIL);
    const modifier = boutonAction("modifier", "Modifier le client", ICONE_CRAYON);
    const supprimer = boutonAction("supprimer", "Supprimer le client", ICONE_CORBEILLE);
    details.onclick = () => ouvrirFicheClient(client.identifiant);
    modifier.onclick = () => ouvrirFormulaireClient(client);
    supprimer.onclick = () => supprimerClient(client);
    actions.append(details, modifier, supprimer);
    ligne.append(actions);
    corps.append(ligne);
  });

  $("#pagination-clients").textContent =
    `Page ${reponse.pagination.page} / ${reponse.pagination.pages} · ${reponse.pagination.total} clients`;
}

function ouvrirFormulaireClient(client = null) {
  $("#client-identifiant").value = client?.identifiant || "";
  $("#client-nom").value = client?.nom_complet || "";
  $("#client-secteur").value = client?.secteur_activite || "";
  $("#client-revenu").value = client?.revenu_mensuel ?? 0;
  $("#client-charges").value = client?.charges_mensuelles ?? 0;
  $("#client-dette").value = client?.mensualite_dette_existante ?? 0;
  $("#client-anciennete").value = client?.anciennete_activite_mois ?? 0;
  $("#client-retards").value = client?.nombre_retards ?? 0;
  $("#titre-dialogue-client").textContent = client ? "Modifier le client" : "Nouveau client";
  $("#message-client").textContent = "";
  ouvrirDialogue("dialogue-client");
}

async function supprimerClient(client) {
  if (!confirm(`Supprimer définitivement « ${client.nom_complet} » ?`)) return;
  try {
    await api(`/api/clients/${client.identifiant}/supprimer/`, { method: "DELETE" });
    chargerClients();
    chargerTableauBord();
  } catch (erreur) {
    alert(erreur.message);
  }
}

/* ---------- Fiche client ---------- */

async function ouvrirFicheClient(identifiant) {
  dossierAffiche = await api(`/api/clients/${identifiant}/`);
  clientAffiche = dossierAffiche.client;
  ouvrir("fiche-client");
  afficherFicheClient(dossierAffiche);
}

function afficherFicheClient(dossier) {
  const client = dossier.client;
  const synthese = dossier.synthese;

  $("#fiche-initiales").textContent = initiales(client.nom_complet);
  $("#fiche-nom").textContent = client.nom_complet;
  $("#fiche-anciennete-relation").textContent = `Client depuis ${formaterDate(client.cree_le)}`;
  $("#fiche-resume").textContent =
    [client.secteur_activite, `${client.anciennete_activite_mois} mois d'activité`, client.identifiant_source]
      .filter(Boolean).join(" · ");

  afficherSyntheseFinanciere(synthese);
  afficherComportement(synthese, dossier.historique_credit);
  afficherActivites(dossier.activites);
  afficherChronologie(dossier.chronologie);
  afficherCreditsFiche(dossier.historique_credit);
}

function ligneSynthese(libelle, valeur, classe = "") {
  return `<div class="ligne-synthese ${classe}"><span>${libelle}</span><strong>${valeur}</strong></div>`;
}

function afficherSyntheseFinanciere(synthese) {
  /* Un client importé n'a pas de situation financière : les recettes vivent
     dans les relevés d'activité, qui ne font pas partie du lot importé.
     Afficher « 0 F » laisserait croire à un revenu nul ; on dit « inconnu ». */
  const renseigne = synthese.recettes_declarees || synthese.charges_declarees || synthese.engagements_existants;
  if (!renseigne) {
    $("#fiche-synthese").innerHTML = `
      <p class="sous-titre">Aucune situation financière n'est enregistrée pour ce client.</p>
      <div class="avertissement" style="margin-top:12px">
        Les recettes et charges sont relevées lors de l'instruction d'une demande.
        Elles ne figurent pas dans le fichier <code>clients.csv</code> importé.
      </div>`;
    return;
  }

  const marge = synthese.marge_estimee;
  $("#fiche-synthese").innerHTML = `
    <div>
      ${ligneSynthese("Recettes déclarées", formaterMontant(synthese.recettes_declarees))}
      ${ligneSynthese("Charges déclarées", "− " + formaterMontant(synthese.charges_declarees))}
      ${ligneSynthese("Engagements existants", "− " + formaterMontant(synthese.engagements_existants))}
      ${ligneSynthese("Marge estimée", formaterMontant(marge), "total" + (marge < 0 ? " negatif" : ""))}
    </div>`;
}

function afficherComportement(synthese, credits) {
  const retard = synthese.jours_retard_max;
  $("#fiche-comportement").innerHTML = `
    <div>
      ${ligneSynthese("Crédits obtenus", `${synthese.nombre_credits}`)}
      ${ligneSynthese("Crédits soldés", `${synthese.nombre_credits_soldes}`)}
      ${ligneSynthese("Crédits en cours", `${synthese.nombre_credits_en_cours}`)}
      ${ligneSynthese("Montant total emprunté", formaterMontant(synthese.montant_total_emprunte))}
      ${ligneSynthese("Reste dû", formaterMontant(synthese.reste_du_total))}
      ${ligneSynthese("Échéances en retard", `${synthese.nombre_echeances_en_retard}`)}
      ${ligneSynthese("Retard le plus long observé", retard ? `${retard} jours` : "aucun", retard > 0 ? "negatif" : "")}
    </div>`;
}

function afficherActivites(activites) {
  const conteneur = $("#fiche-activites");
  conteneur.replaceChildren();
  if (!activites.length) {
    conteneur.append(creer("p", { className: "sous-titre", textContent: "Aucune activité déclarée." }));
    return;
  }
  activites.forEach(activite => {
    const carte = creer("div", { className: "carte-secondaire" });
    carte.insertAdjacentHTML("beforeend", `
      <strong>${activite.libelle || activite.secteur}</strong>
      <span>${activite.secteur}${activite.date_debut ? " · depuis le " + formaterDate(activite.date_debut) : ""}${activite.est_principale ? " · activité principale" : ""}</span>
    `);
    conteneur.append(carte);
  });
}

function afficherChronologie(evenements) {
  const conteneur = $("#fiche-chronologie");
  conteneur.replaceChildren();
  if (!evenements.length) {
    conteneur.append(creer("p", { className: "sous-titre", textContent: "Aucun événement enregistré." }));
    return;
  }

  const parAnnee = new Map();
  evenements.forEach(evenement => {
    const annee = evenement.date.slice(0, 4);
    if (!parAnnee.has(annee)) parAnnee.set(annee, []);
    parAnnee.get(annee).push(evenement);
  });

  parAnnee.forEach((liste, annee) => {
    const bloc = creer("div", { className: "annee-chronologie" });
    bloc.append(creer("h3", { textContent: annee }));
    const suite = creer("div", { className: "evenements" });
    liste.forEach(evenement => {
      const element = creer("div", { className: "evenement " + evenement.type });
      element.insertAdjacentHTML("beforeend", `
        <strong>${evenement.libelle}</strong>
        <span>${evenement.detail || ""}</span>
        <time>${formaterDate(evenement.date)}</time>
      `);
      suite.append(element);
    });
    bloc.append(suite);
    conteneur.append(bloc);
  });
}

function afficherCreditsFiche(credits) {
  const conteneur = $("#fiche-credits");
  conteneur.replaceChildren();
  if (!credits.length) {
    conteneur.append(creer("p", { className: "sous-titre", textContent: "Aucun crédit enregistré pour ce client." }));
    return;
  }

  credits.forEach(credit => {
    const carte = creer("article", { className: "carte-credit" });
    const entete = creer("div", { className: "entete-credit" });
    entete.insertAdjacentHTML("beforeend", `
      <div>
        <span class="reference">${credit.identifiant}</span>
        <span class="cellule-secondaire">Décaissé le ${formaterDate(credit.date_decaissement)} · ${credit.duree_mois} mois</span>
      </div>
      <div class="details-credit">
        <span>Montant <strong>${formaterMontant(credit.montant_decaisse)}</strong></span>
        <span>Remboursé <strong>${formaterMontant(credit.total_paye)}</strong></span>
        <span>Reste dû <strong>${formaterMontant(credit.reste_du)}</strong></span>
        <span class="badge-statut ${classeStatut(credit.statut)}">${LIBELLES_STATUT_CREDIT[credit.statut] || credit.statut}</span>
      </div>
    `);

    const corps = creer("div", { className: "corps-credit masque" });
    corps.insertAdjacentHTML("beforeend", `
      <div class="tableau-wrap">
        <table>
          <thead><tr><th>N°</th><th>Échéance</th><th class="montant">Montant dû</th><th class="montant">Payé</th><th class="montant">Reste</th><th>Retard</th></tr></thead>
          <tbody>${credit.echeances.map(echeance => `
            <tr>
              <td>${echeance.numero}</td>
              <td>${formaterDate(echeance.date_exigible)}</td>
              <td class="montant">${formaterMontant(echeance.montant_du)}</td>
              <td class="montant">${formaterMontant(echeance.montant_couvert)}</td>
              <td class="montant">${echeance.reste_du ? formaterMontant(echeance.reste_du) : "—"}</td>
              <td>${echeance.jours_retard ? echeance.jours_retard + " j" : "—"}</td>
            </tr>`).join("")}
          </tbody>
        </table>
      </div>
    `);

    entete.onclick = () => corps.classList.toggle("masque");
    carte.append(entete, corps);
    conteneur.append(carte);
  });
}

/* ---------- Demandes ---------- */

async function chargerDemandes() {
  const reponse = await api("/api/demandes-credit/");
  const demandes = reponse.demandes || [];
  const recherche = ($("#recherche-demandes").value || "").toLowerCase();
  const filtre = $("#filtre-risque").value;

  $("#demande-total").textContent = formaterNombre(demandes.length);
  $("#demande-montant-total").textContent = formaterMontant(demandes.reduce((total, d) => total + (d.montant_demande || 0), 0));
  $("#demande-attente").textContent = formaterNombre(demandes.filter(d => d.decision_agent === "EN_ATTENTE").length);

  const visibles = demandes.filter(demande =>
    demande.client.toLowerCase().includes(recherche) && (!filtre || demande.niveau_risque === filtre));

  const corps = $("#liste-demandes");
  corps.replaceChildren();
  if (!visibles.length) {
    corps.innerHTML = '<tr><td colspan="6">Aucune demande ne correspond aux filtres.</td></tr>';
    return;
  }

  visibles.forEach(demande => {
    const ligne = creer("tr");
    ligne.insertAdjacentHTML("beforeend", `
      <td><span class="cellule-principale">${demande.client}</span><span class="cellule-secondaire">${formaterDate(demande.cree_le)}</span></td>
      <td class="montant">${formaterMontant(demande.montant_demande)}</td>
      <td>${demande.duree_mois} mois</td>
      <td><span class="badge-risque ${classeStatut(demande.niveau_risque)}">${demande.niveau_risque || "Non analysée"}</span></td>
      <td><span class="badge-decision">${demande.decision_agent || "EN_ATTENTE"}</span></td>
    `);
    const actions = creer("td", { className: "actions-tableau" });
    const action = boutonAction("details", "Ouvrir le dossier client", ICONE_OEIL);
    action.onclick = () => ouvrirFicheClient(demande.identifiant_client);
    actions.append(action);
    ligne.append(actions);
    corps.append(ligne);
  });
}

async function ouvrirDialogueDemande(identifiantClient = "") {
  const reponse = await api("/api/clients/?taille=200");
  const select = $("#demande-client");
  select.replaceChildren(
    new Option("Sélectionnez un client", ""),
    ...reponse.resultats.map(client => new Option(client.nom_complet, client.identifiant)),
  );
  if (identifiantClient) select.value = identifiantClient;
  $("#message-demande").textContent = "";
  ouvrirDialogue("dialogue-demande");
}

/* ---------- Listes simples ---------- */

async function chargerListeSimple(vue) {
  const urls = { credits: "/api/credits/", remboursements: "/api/remboursements/", audit: "/api/audit/" };
  const reponse = await api(urls[vue]);
  const lignes = reponse.resultats || [];
  const corps = $("#liste-" + vue);
  corps.replaceChildren();

  if (!lignes.length) {
    corps.innerHTML = '<tr><td colspan="4">Aucune donnée.</td></tr>';
    return;
  }

  lignes.forEach(ligne => {
    const cellules = vue === "credits"
      ? [ligne.identifiant, ligne.client, `<span class="montant">${formaterMontant(ligne.montant)}</span>`, `${ligne.duree_mois} mois`]
      : vue === "remboursements"
        ? [ligne.identifiant, ligne.client, `<span class="montant">${formaterMontant(ligne.montant)}</span>`, formaterDate(ligne.date)]
        : [ligne.evenement, ligne.client, formaterDate(ligne.date)];
    corps.append(creer("tr", { innerHTML: cellules.map(valeur => `<td>${valeur}</td>`).join("") }));
  });
}

/* ---------- Import CSV ---------- */

function donneesFichiers() {
  const donnees = new FormData();
  fichiersSelectionnes.forEach(fichier => donnees.append("fichiers", fichier));
  return donnees;
}

async function validerFichiers(liste) {
  fichiersSelectionnes = [...liste];
  ouvrir("qualite");
  try {
    afficherRapport(await api("/api/imports-csv/valider/", { method: "POST", body: donneesFichiers() }));
  } catch (erreur) {
    afficherRapport({ valide: false, erreurs: [erreur.message] });
  }
}

function afficherRapport(rapport) {
  rapportImport = rapport;
  const conteneur = $("#rapport-import");
  conteneur.className = "rapport";
  const erreurs = rapport.erreurs || [];
  const avertissements = rapport.avertissements || [];

  conteneur.innerHTML = `
    <div class="indicateurs" style="margin-bottom:6px">
      <article><span>Qualité</span><strong>${rapport.qualite != null ? rapport.qualite + " %" : "—"}</strong></article>
      <article><span>Lignes contrôlées</span><strong>${formaterNombre(rapport.total_lignes)}</strong></article>
      <article class="accent-danger"><span>Erreurs</span><strong>${erreurs.length}</strong></article>
      <article class="accent-alerte"><span>Avertissements</span><strong>${avertissements.length}</strong></article>
    </div>
    ${erreurs.length ? `<div class="avertissement">${erreurs.map(e => `<div>${e}</div>`).join("")}</div>` : ""}
    ${avertissements.length ? `<p class="sous-titre">${avertissements.length} avertissement(s) n'empêchent pas l'import.</p>` : ""}
  `;

  $("#confirmer-import").classList.toggle("masque", !rapport.valide);
  $("#voir-anomalies").classList.toggle("masque", !rapport.anomalies);
}

/* ---------- Dialogues ---------- */

function ouvrirDialogue(identifiant) {
  $("#" + identifiant).classList.remove("masque");
  document.body.style.overflow = "hidden";
}

function fermerDialogue(identifiant) {
  $("#" + identifiant).classList.add("masque");
  document.body.style.overflow = "";
}

/* ---------- Chargement général ---------- */

async function charger() {
  const [institution, lots] = await Promise.all([api("/api/institution/"), api("/api/imports-csv/lots/")]);

  $("#nom-institution").textContent = institution.institution.nom;
  $("#nom-marque").textContent = institution.institution.sigle || "CIF";
  $("#marque-logo").textContent = (institution.institution.sigle || "C")[0];
  $("#entete-sigle").textContent = institution.institution.sigle || "Espace opérationnel";
  $("#resume-institution").textContent =
    [institution.institution.ville, institution.institution.pays].filter(Boolean).join(" · ");
  $("#detail-institution").innerHTML =
    ligneSynthese("Nom", institution.institution.nom) +
    ligneSynthese("Sigle", institution.institution.sigle) +
    ligneSynthese("Ville", institution.institution.ville || "—") +
    ligneSynthese("Pays", institution.institution.pays);
  for (const champ of ["nom", "sigle", "ville", "pays"]) {
    $("#institution-" + champ).value = institution.institution[champ] || "";
  }

  $("#lot-reference").replaceChildren(...lots.lots.map(lot => new Option(lot.libelle, lot.code)));
  $("#fichiers-attendus").replaceChildren(...lots.fichiers_attendus.map(nom => creer("span", { textContent: nom })));

  await chargerTableauBord();
}

/* ---------- Branchements ---------- */

$$("[data-vue]").forEach(element => (element.onclick = () => ouvrir(element.dataset.vue)));

$("#actualiser").onclick = () => charger();
$("#nouveau-client").onclick = () => ouvrirFormulaireClient();
$("#annuler-client").onclick = () => fermerDialogue("dialogue-client");
$("#modifier-institution").onclick = () => ouvrirDialogue("dialogue-institution");
$("#retour-clients").onclick = () => ouvrir("clients");
$("#fiche-modifier").onclick = () => clientAffiche && ouvrirFormulaireClient(clientAffiche);
$("#fiche-nouvelle-demande").onclick = () => ouvrirDialogueDemande(clientAffiche?.identifiant);
$("#nouvelle-demande").onclick = () => ouvrirDialogueDemande();
$("#recherche-demandes").oninput = () => chargerDemandes();
$("#filtre-risque").onchange = () => chargerDemandes();
$("#recherche-clients").oninput = () => { pageClients = 1; chargerClients(); };

$$("[data-fermer]").forEach(element => (element.onclick = () => fermerDialogue(element.dataset.fermer)));
$$(".dialogue").forEach(dialogue => (dialogue.onclick = evenement => {
  if (evenement.target === dialogue) fermerDialogue(dialogue.id);
}));
document.addEventListener("keydown", evenement => {
  if (evenement.key === "Escape") $$(".dialogue:not(.masque)").forEach(dialogue => fermerDialogue(dialogue.id));
});

$("#formulaire-client").onsubmit = async evenement => {
  evenement.preventDefault();
  const identifiant = $("#client-identifiant").value;
  const donnees = {
    nom_complet: $("#client-nom").value,
    secteur_activite: $("#client-secteur").value,
    revenu_mensuel: +$("#client-revenu").value,
    charges_mensuelles: +$("#client-charges").value,
    mensualite_dette_existante: +$("#client-dette").value,
    anciennete_activite_mois: +$("#client-anciennete").value,
    nombre_retards: +$("#client-retards").value,
    regularite_tontine: "inconnue",
  };
  try {
    await api(identifiant ? `/api/clients/${identifiant}/modifier/` : "/api/clients/creer/", {
      method: identifiant ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(donnees),
    });
    fermerDialogue("dialogue-client");
    if (identifiant && clientAffiche?.identifiant == identifiant) ouvrirFicheClient(identifiant);
    else chargerClients();
    charger();
  } catch (erreur) {
    $("#message-client").textContent = erreur.message;
  }
};

$("#formulaire-demande").onsubmit = async evenement => {
  evenement.preventDefault();
  try {
    await api("/api/demandes-credit/analyser/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifiant_client: $("#demande-client").value,
        montant_demande: +$("#demande-montant").value,
        duree_mois: +$("#demande-duree").value,
      }),
    });
    fermerDialogue("dialogue-demande");
    ouvrir("demandes");
    chargerTableauBord();
  } catch (erreur) {
    $("#message-demande").textContent = erreur.message;
  }
};

$("#formulaire-institution").onsubmit = async evenement => {
  evenement.preventDefault();
  try {
    await api("/api/institution/enregistrer/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nom: $("#institution-nom").value,
        sigle: $("#institution-sigle").value,
        ville: $("#institution-ville").value,
        pays: $("#institution-pays").value,
      }),
    });
    fermerDialogue("dialogue-institution");
    charger();
  } catch (erreur) {
    $("#message-institution").textContent = erreur.message;
  }
};

const zoneImport = $("#zone-import");
$("#fichiers-institution").onchange = evenement => validerFichiers(evenement.target.files);
["dragenter", "dragover"].forEach(type => zoneImport.addEventListener(type, evenement => {
  evenement.preventDefault();
  zoneImport.classList.add("survol");
}));
["dragleave", "drop"].forEach(type => zoneImport.addEventListener(type, evenement => {
  evenement.preventDefault();
  zoneImport.classList.remove("survol");
}));
zoneImport.addEventListener("drop", evenement => validerFichiers(evenement.dataTransfer.files));

$("#confirmer-import").onclick = async () => {
  await api("/api/imports-csv/confirmer/", { method: "POST", body: donneesFichiers() });
  await charger();
  ouvrir("clients");
};
$("#voir-anomalies").onclick = () =>
  $("#rapport-import").insertAdjacentHTML("beforeend", `<pre>${JSON.stringify(rapportImport.anomalies, null, 2)}</pre>`);

charger();
