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
  "nouvelle-demande-vue": ["Nouvelle demande de crédit", "Constitution du dossier, étape par étape."],
  instruction: ["Instruction du dossier", "Analyse préliminaire, simulation et décision de l'agent."],
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
const ECRANS_PREVUS = {};

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

function formaterHorodatage(texte) {
  if (!texte) return "—";
  const moment = new Date(texte);
  return `${formaterDate(texte)} ${String(moment.getHours()).padStart(2, "0")}:${String(moment.getMinutes()).padStart(2, "0")}`;
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
const ICONE_DOSSIER = '<svg viewBox="0 0 24 24"><path d="M4 6.5A1.5 1.5 0 0 1 5.5 5h4l2 2.5h7A1.5 1.5 0 0 1 20 9v8.5A1.5 1.5 0 0 1 18.5 19h-13A1.5 1.5 0 0 1 4 17.5Z"/><path d="M8.5 12.5h7M8.5 15.5h4"/></svg>';

/* ---------- Navigation ---------- */

function ouvrir(vue) {
  $$(".vue").forEach(section => section.classList.toggle("vue-masque", section.id !== vue));
  $$(".barre-laterale nav button").forEach(bouton => bouton.classList.toggle("nav-actif", bouton.dataset.vue === vue));

  const [titre, description] = TITRES[vue] || ["", ""];
  $("#titre-vue").textContent = titre;
  $("#description-vue").textContent = description;

  if (vue === "clients") chargerClients();
  if (vue === "demandes") chargerDemandes();
  if (vue === "portefeuille") chargerPortefeuille();
  if (vue === "retards") chargerRetards();
  if (vue === "produits") chargerProduits();
  if (vue === "regles") chargerRegles();
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
    const instruire = boutonAction("details", "Instruire la demande", ICONE_DOSSIER);
    const voirClient = boutonAction("details", "Ouvrir le dossier client", ICONE_OEIL);
    instruire.onclick = () => ouvrirInstruction(demande.identifiant);
    voirClient.onclick = () => ouvrirFicheClient(demande.identifiant_client);
    actions.append(instruire, voirClient);
    ligne.append(actions);
    corps.append(ligne);
  });
}

/* ---------- Constitution du dossier en sept étapes ---------- */

const NOMBRE_ETAPES = 7;
let etapeCourante = 1;

async function ouvrirNouvelleDemande(identifiantClient = "") {
  const [clients, produits] = await Promise.all([
    api("/api/clients/?taille=200"),
    api("/api/produits-credit/"),
  ]);

  $("#demande-client").replaceChildren(
    new Option("Sélectionnez un client", ""),
    ...clients.resultats.map(client => new Option(client.nom_complet, client.identifiant)),
  );
  if (identifiantClient) $("#demande-client").value = identifiantClient;

  const selectProduit = $("#demande-produit");
  selectProduit.replaceChildren(
    new Option(produits.produits.length ? "Sélectionnez un produit" : "Aucun produit configuré", ""),
    ...produits.produits.map(produit => new Option(produit.libelle, produit.identifiant)),
  );
  $("#note-produits").classList.toggle("masque", produits.produits.length > 0);

  ["#demande-montant", "#demande-objet", "#demande-recettes", "#demande-charges-activite",
   "#demande-autres-revenus", "#demande-charges-menage", "#demande-dette"].forEach(selecteur => {
    $(selecteur).value = selecteur === "#demande-objet" ? "" : 0;
  });
  $("#demande-montant").value = "";
  $("#demande-duree").value = 12;
  $("#message-demande").textContent = "";

  etapeCourante = 1;
  ouvrir("nouvelle-demande-vue");
  afficherEtape();
  if (identifiantClient) preremplirDepuisClient(identifiantClient);
}

async function preremplirDepuisClient(identifiant) {
  /* Reprise de ce que l'institution sait déjà : l'agent corrige au lieu de
     ressaisir. Les zéros ne sont pas recopiés, pour ne pas faire passer une
     information absente pour une information relevée. */
  const dossier = await api(`/api/clients/${identifiant}/`);
  const client = dossier.client;
  if (client.anciennete_activite_mois) $("#demande-anciennete").value = client.anciennete_activite_mois;
  if (client.revenu_mensuel) $("#demande-recettes").value = client.revenu_mensuel;
  if (client.charges_mensuelles) $("#demande-charges-activite").value = client.charges_mensuelles;
  if (client.mensualite_dette_existante) $("#demande-dette").value = client.mensualite_dette_existante;
  afficherHistoriqueEtape(dossier);
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

function validerEtape() {
  $("#message-demande").textContent = "";
  if (etapeCourante === 1 && !$("#demande-client").value) {
    $("#message-demande").textContent = "Sélectionnez un client pour continuer.";
    return false;
  }
  if (etapeCourante === 2 && !(+$("#demande-montant").value > 0)) {
    $("#message-demande").textContent = "Indiquez le montant demandé.";
    return false;
  }
  return true;
}

async function etapeSuivante() {
  if (!validerEtape()) return;
  if (etapeCourante === 1) await preremplirDepuisClient($("#demande-client").value);
  etapeCourante = Math.min(NOMBRE_ETAPES, etapeCourante + 1);
  if (etapeCourante === NOMBRE_ETAPES) afficherVerification();
  afficherEtape();
}

function afficherHistoriqueEtape(dossier) {
  const conteneur = $("#demande-historique");
  const synthese = dossier.synthese;
  if (!synthese.nombre_credits) {
    conteneur.innerHTML = `<div class="avertissement">Aucun crédit antérieur dans l'institution : le dossier ne dispose d'aucun historique interne.</div>`;
    return;
  }
  conteneur.innerHTML = `
    <div>
      ${ligneSynthese("Crédits obtenus", synthese.nombre_credits)}
      ${ligneSynthese("Crédits soldés", synthese.nombre_credits_soldes)}
      ${ligneSynthese("Crédits en cours", synthese.nombre_credits_en_cours)}
      ${ligneSynthese("Reste dû", formaterMontant(synthese.reste_du_total))}
      ${ligneSynthese("Retard le plus long observé", synthese.jours_retard_max ? synthese.jours_retard_max + " jours" : "aucun")}
    </div>`;
}

function afficherVerification() {
  const montant = +$("#demande-montant").value;
  const duree = +$("#demande-duree").value || 1;
  const marge = (+$("#demande-recettes").value + +$("#demande-autres-revenus").value)
    - +$("#demande-charges-activite").value - +$("#demande-charges-menage").value - +$("#demande-dette").value;
  const echeance = Math.round(montant / duree);

  const controles = [
    ["Client identifié", !!$("#demande-client").value],
    ["Montant et durée", montant > 0 && duree > 0],
    ["Objet du financement", !!$("#demande-objet").value.trim()],
    ["Produit de crédit", !!$("#demande-produit").value],
    ["Activité renseignée", +$("#demande-recettes").value > 0],
    ["Charges du ménage", +$("#demande-charges-menage").value > 0],
    ["Engagements existants", true],
  ];

  $("#demande-verification").innerHTML = `
    ${controles.map(([libelle, present]) => `
      <div class="ligne-controle ${present ? "present" : "absent"}">
        <span class="marque-controle">${present ? "✓" : "⚠"}</span>
        <span>${libelle}${present ? "" : " — information manquante"}</span>
      </div>`).join("")}
    <div style="margin-top:16px">
      ${ligneSynthese("Marge estimée", formaterMontant(marge))}
      ${ligneSynthese("Échéance estimée", formaterMontant(echeance), "total" + (echeance > marge ? " negatif" : ""))}
    </div>
    ${echeance > marge ? '<div class="avertissement" style="margin-top:12px">L\'échéance estimée dépasse la marge estimée. Le dossier peut être enregistré : la décision reste la vôtre.</div>' : ""}
  `;
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
    await ouvrirInstruction(reponse.identifiant_demande);
    chargerTableauBord();
  } catch (erreur) {
    $("#message-demande").textContent = erreur.message;
  }
}

/* ---------- Instruction du dossier ---------- */

let demandeInstruite = null;

async function ouvrirInstruction(identifiantDemande) {
  demandeInstruite = await api(`/api/demandes-credit/${identifiantDemande}/`);
  ouvrir("instruction");
  afficherInstruction(demandeInstruite);
}

function afficherInstruction(dossier) {
  const demande = dossier.demande;

  $("#instruction-reference").textContent = demande.reference;
  $("#instruction-client").textContent = demande.client;
  $("#instruction-resume").textContent =
    [formaterMontant(demande.montant_demande), `${demande.duree_mois} mois`, demande.objet_credit, demande.produit]
      .filter(Boolean).join(" · ");
  $("#instruction-decision").textContent = demande.decision_agent;

  $("#instruction-dossier").innerHTML = `
    <div>
      ${ligneSynthese("Objet du financement", demande.objet_credit || "non renseigné")}
      ${ligneSynthese("Produit", demande.produit || "non renseigné")}
      ${ligneSynthese("Montant demandé", formaterMontant(demande.montant_demande))}
      ${ligneSynthese("Durée", demande.duree_mois + " mois")}
      ${ligneSynthese("Ancienneté de l'activité", demande.anciennete_activite_mois + " mois")}
      ${ligneSynthese("Saisonnalité", demande.saisonnalite_activite || "non renseignée")}
      ${ligneSynthese("Dossier constitué le", formaterDate(demande.cree_le))}
    </div>`;

  afficherCapacite(dossier.analyse.capacite);
  afficherHistoriqueInstruction(dossier.analyse.historique);
  afficherQualiteDossier(dossier.analyse.qualite_dossier);
  afficherIndicateursExperimentaux(dossier.indicateurs_experimentaux);
  afficherJournalDemande(dossier.journal);

  $("#instruction-observations").value = demande.observations_agent || "";
  $("#instruction-motif").value = demande.motif_decision || "";
  $$('input[name="decision"]').forEach(bouton => (bouton.checked = bouton.value === demande.decision_agent));
  $("#message-decision").textContent = "";

  preparerSimulation(demande);
}

function afficherCapacite(capacite) {
  const conteneur = $("#instruction-capacite");
  if (!capacite.renseigne) {
    conteneur.innerHTML = `<div class="avertissement">${capacite.alerte}</div>`;
    return;
  }
  conteneur.innerHTML = `
    <div>
      ${capacite.lignes.map(ligne => ligneSynthese(
        ligne.libelle,
        (ligne.sens === "debit" ? "− " : "") + formaterMontant(ligne.montant),
      )).join("")}
      ${ligneSynthese("Marge estimée", formaterMontant(capacite.marge_estimee), "total")}
      ${ligneSynthese("Échéance de la nouvelle demande", formaterMontant(capacite.echeance_estimee),
        capacite.ecart < 0 ? "negatif" : "")}
    </div>
    ${capacite.alerte ? `<div class="avertissement" style="margin-top:12px">${capacite.alerte}</div>` : ""}
    <p class="sous-titre" style="margin-top:10px">${capacite.note_methode}</p>`;
}

function afficherHistoriqueInstruction(historique) {
  const conteneur = $("#instruction-historique");
  if (historique.sans_historique) {
    conteneur.innerHTML = `<div class="avertissement">${historique.message}</div>`;
    return;
  }
  conteneur.innerHTML = `
    <div>
      ${ligneSynthese("Crédits antérieurs", historique.nombre_credits)}
      ${ligneSynthese("Soldés", historique.nombre_soldes)}
      ${ligneSynthese("En cours", historique.nombre_en_cours)}
      ${ligneSynthese("Crédits ayant connu un retard", historique.nombre_avec_retard)}
      ${ligneSynthese("Retard le plus long", historique.jours_retard_max ? historique.jours_retard_max + " jours" : "aucun")}
      ${ligneSynthese("Échéances actuellement en retard", historique.echeances_en_retard)}
      ${ligneSynthese("Reste dû", formaterMontant(historique.reste_du_total))}
    </div>`;
}

function afficherQualiteDossier(qualite) {
  $("#instruction-qualite").innerHTML = `
    <p class="sous-titre" style="margin-bottom:10px">${qualite.renseignes} informations sur ${qualite.total} sont renseignées (${qualite.completude} %).</p>
    ${qualite.controles.map(controle => `
      <div class="ligne-controle ${controle.present ? "present" : "absent"}">
        <span class="marque-controle">${controle.present ? "✓" : "⚠"}</span>
        <span>${controle.libelle}${controle.present ? "" : " — absent"}</span>
      </div>`).join("")}`;
}

function afficherIndicateursExperimentaux(indicateurs) {
  $("#instruction-experimental").innerHTML = `
    <div class="avertissement" style="margin-bottom:14px">${indicateurs.avertissement}</div>
    <div>
      ${ligneSynthese("Indicateur composite", `${indicateurs.score_risque} / 100`)}
      ${ligneSynthese("Niveau indicatif", indicateurs.niveau_risque)}
    </div>
    ${indicateurs.points_vigilance.length ? `<p class="surtexte" style="margin-top:14px">Points de vigilance</p>
      <ul class="liste-puces">${indicateurs.points_vigilance.map(point => `<li>${point}</li>`).join("")}</ul>` : ""}
    ${indicateurs.facteurs_favorables.length ? `<p class="surtexte" style="margin-top:12px">Éléments favorables</p>
      <ul class="liste-puces">${indicateurs.facteurs_favorables.map(point => `<li>${point}</li>`).join("")}</ul>` : ""}`;
}

function afficherJournalDemande(journal) {
  const conteneur = $("#instruction-journal");
  conteneur.className = "liste-journal";
  if (!journal.length) {
    conteneur.innerHTML = '<p class="sous-titre">Aucun événement.</p>';
    return;
  }
  conteneur.innerHTML = journal.map(entree => `
    <div class="entree-journal">
      <time>${formaterDate(entree.date)}</time>
      <span>${entree.evenement.replaceAll("_", " ").toLowerCase()}</span>
    </div>`).join("");
}

/* ---------- Simulation ---------- */

let minuteurSimulation = null;

function preparerSimulation(demande) {
  const curseur = $("#simulation-montant");
  curseur.max = Math.max(500000, demande.montant_demande * 2);
  curseur.value = demande.montant_demande;
  $("#simulation-duree").value = String(demande.duree_mois);
  $("#simulation-montant-valeur").textContent = formaterMontant(demande.montant_demande);
  lancerSimulation();
}

function lancerSimulation() {
  if (!demandeInstruite) return;
  $("#simulation-montant-valeur").textContent = formaterMontant(+$("#simulation-montant").value);
  clearTimeout(minuteurSimulation);
  minuteurSimulation = setTimeout(async () => {
    const identifiant = demandeInstruite.demande.identifiant;
    const montant = +$("#simulation-montant").value;
    const duree = +$("#simulation-duree").value;
    const resultat = await api(`/api/demandes-credit/${identifiant}/simuler/?montant=${montant}&duree=${duree}`);
    afficherSimulation(resultat);
  }, 180);
}

function afficherSimulation(resultat) {
  const actuel = resultat.situation_actuelle;
  const simule = resultat.simulation;
  const ligne = (libelle, gauche, droite, classe = "") => `
    <tr class="${classe}">
      <td>${libelle}</td>
      <td class="montant">${gauche}</td>
      <td class="montant">${droite}</td>
    </tr>`;

  $("#tableau-simulation").innerHTML = `
    <div class="tableau-wrap">
      <table>
        <thead><tr><th></th><th class="montant">Dossier actuel</th><th class="montant">Simulation</th></tr></thead>
        <tbody>
          ${ligne("Montant", formaterMontant(actuel.montant), formaterMontant(simule.montant))}
          ${ligne("Durée", actuel.duree_mois + " mois", simule.duree_mois + " mois")}
          ${ligne("Échéance estimée", formaterMontant(actuel.echeance_estimee), formaterMontant(simule.echeance_estimee))}
          ${ligne("Marge estimée", formaterMontant(actuel.marge_estimee), formaterMontant(simule.marge_estimee))}
          ${ligne("Écart marge / échéance", formaterMontant(actuel.ecart), formaterMontant(simule.ecart))}
        </tbody>
      </table>
    </div>
    ${simule.ecart < 0
      ? '<div class="avertissement" style="margin-top:12px">L\'échéance simulée reste supérieure à la marge estimée.</div>'
      : ""}`;
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
        : [formaterHorodatage(ligne.date), ligne.evenement, ligne.reference_demande, ligne.client, ligne.detail || "—"];
    corps.append(creer("tr", { innerHTML: cellules.map(valeur => `<td>${valeur}</td>`).join("") }));
  });
}

/* ---------- Portefeuille ---------- */

let filtresPortefeuilleCharges = false;

async function chargerPortefeuille() {
  const parametres = new URLSearchParams({
    secteur: $("#pf-filtre-secteur").value,
    statut: $("#pf-filtre-statut").value,
    annee: $("#pf-filtre-annee").value,
  });
  const donnees = await api("/api/portefeuille/?" + parametres);

  if (!filtresPortefeuilleCharges) {
    remplirFiltre("#pf-filtre-secteur", "Tous les secteurs", donnees.filtres.secteurs);
    remplirFiltre("#pf-filtre-annee", "Toutes les périodes", donnees.filtres.annees);
    remplirFiltre("#pf-filtre-statut", "Tous les statuts", donnees.filtres.statuts,
      statut => LIBELLES_STATUT_CREDIT[statut] || statut);
    $("#pf-indisponibles").textContent =
      "Filtres indisponibles : " + donnees.filtres.indisponibles.join(", ").toLowerCase();
    filtresPortefeuilleCharges = true;
  }

  const indicateurs = donnees.indicateurs;
  $("#pf-credits").textContent = formaterNombre(indicateurs.credits);
  $("#pf-credits-actifs").textContent = `${formaterNombre(indicateurs.credits_actifs)} encore actifs`;
  $("#pf-decaisse").textContent = formaterMontant(indicateurs.montant_decaisse);
  $("#pf-rembourse").textContent = `${formaterMontant(indicateurs.montant_rembourse)} remboursés`;
  $("#pf-encours").textContent = formaterMontant(indicateurs.encours);
  $("#pf-retard").textContent = formaterNombre(indicateurs.credits_en_retard);

  const corps = $("#liste-portefeuille");
  corps.replaceChildren();
  if (!donnees.credits.length) {
    corps.innerHTML = '<tr><td colspan="8">Aucun crédit ne correspond aux filtres.</td></tr>';
  }
  donnees.credits.forEach(credit => {
    const ligne = creer("tr");
    ligne.insertAdjacentHTML("beforeend", `
      <td class="cellule-principale">${credit.identifiant}</td>
      <td>${credit.client}</td>
      <td>${credit.secteur}</td>
      <td class="montant">${formaterMontant(credit.montant_decaisse)}</td>
      <td class="montant">${credit.reste_du ? formaterMontant(credit.reste_du) : "—"}</td>
      <td>${formaterDate(credit.date_decaissement)}</td>
      <td><span class="badge-statut ${classeStatut(credit.statut)}">${LIBELLES_STATUT_CREDIT[credit.statut] || credit.statut}</span></td>
    `);
    const actions = creer("td", { className: "actions-tableau" });
    const bouton = boutonAction("details", "Ouvrir le dossier client", ICONE_OEIL);
    bouton.onclick = () => ouvrirFicheClient(credit.identifiant_client);
    actions.append(bouton);
    ligne.append(actions);
    corps.append(ligne);
  });

  const repartition = $("#pf-repartition");
  repartition.replaceChildren();
  donnees.repartition_secteur.forEach(entree => {
    const ligne = creer("div", { className: "ligne-repartition" });
    ligne.append(creer("span", { textContent: entree.libelle }));
    ligne.append(creer("strong", { textContent: `${entree.nombre} crédits · ${formaterMontant(entree.encours)} d'encours` }));
    repartition.append(ligne);
  });
}

function remplirFiltre(selecteur, libelleVide, valeurs, transformer = valeur => valeur) {
  $(selecteur).replaceChildren(
    new Option(libelleVide, ""),
    ...valeurs.map(valeur => new Option(transformer(valeur), valeur)),
  );
}

/* ---------- Retards ---------- */

async function chargerRetards() {
  const donnees = await api("/api/retards/");
  const indicateurs = donnees.indicateurs;
  $("#rt-echeances").textContent = formaterNombre(indicateurs.echeances_en_retard);
  $("#rt-montant").textContent = formaterMontant(indicateurs.montant_en_retard);
  $("#rt-clients").textContent = formaterNombre(indicateurs.clients_concernes);
  $("#rt-credits").textContent = formaterNombre(indicateurs.credits_concernes);

  const tranches = $("#rt-tranches");
  tranches.replaceChildren();
  if (!donnees.tranches.length) {
    tranches.append(creer("p", { className: "sous-titre", textContent: "Aucune échéance en retard." }));
  }
  donnees.tranches.forEach(tranche => {
    const ligne = creer("div", { className: "ligne-repartition" });
    ligne.append(creer("span", { textContent: `Retard de ${tranche.libelle}` }));
    ligne.append(creer("strong", { textContent: `${tranche.nombre} échéances · ${formaterMontant(tranche.montant)}` }));
    tranches.append(ligne);
  });

  const corps = $("#liste-retards");
  corps.replaceChildren();
  if (!donnees.impayes.length) {
    corps.innerHTML = '<tr><td colspan="9">Aucune échéance impayée.</td></tr>';
  }
  donnees.impayes.forEach(impaye => {
    const ligne = creer("tr");
    ligne.insertAdjacentHTML("beforeend", `
      <td class="cellule-principale">${impaye.client}</td>
      <td>${impaye.identifiant_credit}</td>
      <td>n° ${impaye.numero_echeance}</td>
      <td>${formaterDate(impaye.date_exigible)}</td>
      <td class="montant">${formaterMontant(impaye.montant_du)}</td>
      <td class="montant">${impaye.montant_couvert ? formaterMontant(impaye.montant_couvert) : "—"}</td>
      <td class="montant">${formaterMontant(impaye.reste_du)}</td>
      <td><span class="badge-statut en_retard">${impaye.jours_retard} j</span></td>
    `);
    const actions = creer("td", { className: "actions-tableau" });
    const bouton = boutonAction("details", "Ouvrir le dossier client", ICONE_OEIL);
    bouton.onclick = () => ouvrirFicheClient(impaye.identifiant_client);
    actions.append(bouton);
    ligne.append(actions);
    corps.append(ligne);
  });
}

/* ---------- Produits de crédit ---------- */

async function chargerProduits() {
  const donnees = await api("/api/produits-credit/");
  const corps = $("#liste-produits");
  corps.replaceChildren();

  if (!donnees.produits.length) {
    corps.innerHTML = '<tr><td colspan="6">Aucun produit configuré. Ajoutez ceux de votre institution.</td></tr>';
    return;
  }

  donnees.produits.forEach(produit => {
    const bornesMontant = produit.montant_max
      ? `${formaterMontant(produit.montant_min)} à ${formaterMontant(produit.montant_max)}`
      : "non bornés";
    const bornesDuree = produit.duree_max_mois
      ? `${produit.duree_min_mois} à ${produit.duree_max_mois} mois`
      : "non bornées";
    const ligne = creer("tr");
    ligne.insertAdjacentHTML("beforeend", `
      <td class="cellule-principale">${produit.code}</td>
      <td>${produit.libelle}</td>
      <td class="montant">${bornesMontant}</td>
      <td>${bornesDuree}</td>
      <td>${produit.secteurs_vises || "—"}</td>
    `);
    const actions = creer("td", { className: "actions-tableau" });
    const modifier = boutonAction("modifier", "Modifier le produit", ICONE_CRAYON);
    const supprimer = boutonAction("supprimer", "Supprimer le produit", ICONE_CORBEILLE);
    modifier.onclick = () => ouvrirFormulaireProduit(produit);
    supprimer.onclick = async () => {
      if (!confirm(`Supprimer le produit « ${produit.libelle} » ?`)) return;
      await api(`/api/produits-credit/${produit.identifiant}/`, { method: "DELETE" });
      chargerProduits();
    };
    actions.append(modifier, supprimer);
    ligne.append(actions);
    corps.append(ligne);
  });
}

/* ---------- Règles d'analyse ---------- */

async function chargerRegles() {
  const donnees = await api("/api/regles-analyse/");
  $("#avertissement-regles").innerHTML = `<div class="avertissement">${donnees.avertissement}</div>`;

  const corps = $("#liste-regles");
  corps.replaceChildren();
  donnees.regles.forEach(regle => {
    corps.append(creer("tr", {
      innerHTML: `
        <td class="cellule-principale">${regle.code}</td>
        <td>${regle.libelle}</td>
        <td>${regle.description}</td>
        <td>${regle.seuils}</td>
        <td><span class="badge-statut ${regle.active ? "solde" : "en_cours"}">${regle.active ? "Active" : "Inactive"}</span></td>`,
    }));
  });
}

function ouvrirFormulaireProduit(produit = null) {
  $("#produit-identifiant").value = produit?.identifiant || "";
  $("#produit-code").value = produit?.code || "";
  $("#produit-libelle").value = produit?.libelle || "";
  $("#produit-montant-min").value = produit?.montant_min ?? 0;
  $("#produit-montant-max").value = produit?.montant_max ?? 0;
  $("#produit-duree-min").value = produit?.duree_min_mois ?? 0;
  $("#produit-duree-max").value = produit?.duree_max_mois ?? 0;
  $("#produit-secteurs").value = produit?.secteurs_vises || "";
  $("#titre-dialogue-produit").textContent = produit ? "Modifier le produit" : "Nouveau produit de crédit";
  $("#message-produit").textContent = "";
  ouvrirDialogue("dialogue-produit");
}

/* ---------- Import CSV ---------- */

function donneesFichiers() {
  const donnees = new FormData();
  fichiersSelectionnes.forEach(fichier => donnees.append("fichiers", fichier));
  return donnees;
}

const NOMBRE_ETAPES_IMPORT = 4;
let etapeImport = 1;

function afficherEtapeImport() {
  for (let numero = 1; numero <= NOMBRE_ETAPES_IMPORT; numero += 1) {
    $("#import-etape-" + numero).classList.toggle("masque", numero !== etapeImport);
  }
  $$("#etapes-import li").forEach(element => {
    const numero = +element.dataset.etapeImport;
    element.classList.toggle("active", numero === etapeImport);
    element.classList.toggle("faite", numero < etapeImport);
  });
  $("#import-precedent").disabled = etapeImport === 1;
  $("#import-suivant").classList.toggle("masque", etapeImport >= NOMBRE_ETAPES_IMPORT || !rapportImport);
  $("#confirmer-import").classList.toggle("masque", etapeImport !== NOMBRE_ETAPES_IMPORT || !rapportImport?.valide);
}

async function validerFichiers(liste) {
  fichiersSelectionnes = [...liste];
  $("#etat-import").textContent = `${fichiersSelectionnes.length} fichier(s) sélectionné(s), contrôle en cours…`;
  try {
    rapportImport = await api("/api/imports-csv/valider/", { method: "POST", body: donneesFichiers() });
  } catch (erreur) {
    rapportImport = { valide: false, erreurs: [erreur.message], avertissements: [], anomalies: [], lignes: {} };
  }
  afficherControle(rapportImport);
  afficherAnomalies(rapportImport);
  afficherConfirmation(rapportImport);
  afficherRapportQualite(rapportImport);
  etapeImport = 2;
  afficherEtapeImport();
}

function afficherControle(rapport) {
  const lignesParFichier = rapport.lignes || {};
  const anomaliesParFichier = {};
  (rapport.anomalies || []).forEach(anomalie => {
    anomaliesParFichier[anomalie.fichier] = (anomaliesParFichier[anomalie.fichier] || 0) + 1;
  });

  const fichiers = Object.keys(lignesParFichier).sort();
  $("#import-fichiers").innerHTML = fichiers.length ? `
    <div class="tableau-wrap">
      <table>
        <thead><tr><th>Fichier</th><th class="montant">Lignes</th><th>État</th></tr></thead>
        <tbody>
          ${fichiers.map(nom => {
            const anomalies = anomaliesParFichier[nom] || 0;
            return `<tr>
              <td class="cellule-principale">${nom}</td>
              <td class="montant">${formaterNombre(lignesParFichier[nom])}</td>
              <td>${anomalies
                ? `<span class="badge-statut en_retard">${anomalies} anomalie${anomalies > 1 ? "s" : ""}</span>`
                : '<span class="badge-statut solde">conforme</span>'}</td>
            </tr>`;
          }).join("")}
        </tbody>
      </table>
    </div>` : '<div class="avertissement">Aucun fichier exploitable n\'a été lu.</div>';

  const erreurs = rapport.erreurs || [];
  const avertissements = rapport.avertissements || [];
  $("#import-synthese").innerHTML = `
    <div class="indicateurs">
      <article><span>Qualité</span><strong>${rapport.qualite != null ? rapport.qualite + " %" : "—"}</strong></article>
      <article><span>Lignes contrôlées</span><strong>${formaterNombre(rapport.total_lignes)}</strong></article>
      <article class="accent-danger"><span>Erreurs</span><strong>${erreurs.length}</strong></article>
      <article class="accent-alerte"><span>Avertissements</span><strong>${avertissements.length}</strong></article>
    </div>
    ${erreurs.length ? `<div class="avertissement">${erreurs.map(erreur => `<div>${erreur}</div>`).join("")}</div>` : ""}
    ${avertissements.length ? `<p class="sous-titre" style="margin-top:10px">${avertissements.join(" ")}</p>` : ""}`;
}

function tableauAnomalies(anomalies) {
  return `
    <div class="tableau-wrap">
      <table>
        <thead><tr><th>Fichier</th><th>Ligne</th><th>Type</th><th>Détail</th></tr></thead>
        <tbody>
          ${anomalies.map(anomalie => `
            <tr>
              <td class="cellule-principale">${anomalie.fichier}</td>
              <td>${anomalie.ligne}</td>
              <td>${anomalie.type}</td>
              <td>${anomalie.detail}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

function afficherAnomalies(rapport) {
  const anomalies = rapport.anomalies || [];
  $("#import-anomalies").innerHTML = anomalies.length
    ? tableauAnomalies(anomalies)
    : '<p class="sous-titre">Aucune anomalie relevée sur ce lot.</p>';
}

function afficherConfirmation(rapport) {
  const total = formaterNombre(rapport.total_lignes);
  $("#import-confirmation").innerHTML = rapport.valide
    ? `<p class="sous-titre">${total} lignes seront intégrées. Les clients déjà connus sont mis à jour, pas dupliqués.</p>
       ${(rapport.avertissements || []).length
         ? '<div class="avertissement" style="margin-top:12px">Des avertissements subsistent : ils n\'empêchent pas l\'import.</div>'
         : ""}`
    : `<div class="avertissement">Le lot contient des erreurs bloquantes. Corrigez les fichiers à la source, puis redéposez-les.</div>`;
}

function afficherRapportQualite(rapport) {
  const conteneur = $("#rapport-import");
  const anomalies = rapport.anomalies || [];
  conteneur.className = anomalies.length ? "rapport" : "etat-vide";
  conteneur.innerHTML = anomalies.length
    ? `<p class="sous-titre" style="margin-bottom:12px">${anomalies.length} anomalie(s) relevée(s) lors du dernier contrôle.</p>${tableauAnomalies(anomalies)}`
    : "Aucune anomalie lors du dernier contrôle.";
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
$("#fiche-nouvelle-demande").onclick = () => ouvrirNouvelleDemande(clientAffiche?.identifiant);
$("#nouvelle-demande").onclick = () => ouvrirNouvelleDemande();
$("#etape-precedente").onclick = () => { etapeCourante = Math.max(1, etapeCourante - 1); afficherEtape(); };
$("#etape-suivante").onclick = etapeSuivante;
$("#enregistrer-dossier").onclick = enregistrerDossier;
$("#instruction-voir-client").onclick = () => demandeInstruite && ouvrirFicheClient(demandeInstruite.demande.identifiant_client);
$("#simulation-montant").oninput = lancerSimulation;
$("#simulation-duree").onchange = lancerSimulation;

$("#appliquer-simulation").onclick = async () => {
  if (!demandeInstruite) return;
  const identifiant = demandeInstruite.demande.identifiant;
  await api(`/api/demandes-credit/${identifiant}/appliquer-simulation/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ montant: +$("#simulation-montant").value, duree_mois: +$("#simulation-duree").value }),
  });
  await ouvrirInstruction(identifiant);
};

$("#enregistrer-decision").onclick = async () => {
  const choisi = $$('input[name="decision"]').find(bouton => bouton.checked);
  if (!choisi) {
    $("#message-decision").textContent = "Sélectionnez une décision.";
    return;
  }
  try {
    const identifiant = demandeInstruite.demande.identifiant;
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
    chargerTableauBord();
  } catch (erreur) {
    $("#message-decision").textContent = erreur.message;
  }
};
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

$("#import-precedent").onclick = () => { etapeImport = Math.max(1, etapeImport - 1); afficherEtapeImport(); };
$("#import-suivant").onclick = () => { etapeImport = Math.min(NOMBRE_ETAPES_IMPORT, etapeImport + 1); afficherEtapeImport(); };

$("#confirmer-import").onclick = async () => {
  $("#message-import").textContent = "Import en cours…";
  try {
    const resultat = await api("/api/imports-csv/confirmer/", { method: "POST", body: donneesFichiers() });
    $("#message-import").textContent = `${resultat.clients_ajoutes} client(s) ajouté(s), ${resultat.credits_importes} crédit(s) importé(s).`;
    await charger();
    ouvrir("clients");
  } catch (erreur) {
    $("#message-import").textContent = erreur.message;
  }
};

$("#nouveau-produit").onclick = () => ouvrirFormulaireProduit();
$("#formulaire-produit").onsubmit = async evenement => {
  evenement.preventDefault();
  const identifiant = $("#produit-identifiant").value;
  try {
    await api(identifiant ? `/api/produits-credit/${identifiant}/` : "/api/produits-credit/creer/", {
      method: identifiant ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code: $("#produit-code").value,
        libelle: $("#produit-libelle").value,
        montant_min: +$("#produit-montant-min").value,
        montant_max: +$("#produit-montant-max").value,
        duree_min_mois: +$("#produit-duree-min").value,
        duree_max_mois: +$("#produit-duree-max").value,
        secteurs_vises: $("#produit-secteurs").value,
      }),
    });
    fermerDialogue("dialogue-produit");
    chargerProduits();
  } catch (erreur) {
    $("#message-produit").textContent = erreur.message;
  }
};

["#pf-filtre-secteur", "#pf-filtre-statut", "#pf-filtre-annee"].forEach(selecteur => {
  $(selecteur).onchange = () => chargerPortefeuille();
});

charger();
