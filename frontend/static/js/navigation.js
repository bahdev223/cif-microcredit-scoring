/* Navigation entre écrans. Chaque module enregistre le chargeur de ses vues :
   la navigation n'a donc pas à connaître le contenu des écrans. */

import { $, $$, fermerTiroir } from "./noyau.js";

const TITRES = {
  "vue-ensemble": ["Vue d'ensemble", "Votre portefeuille ce matin."],
  portefeuille: ["Portefeuille", "Crédits suivis par l'institution."],
  demandes: ["Demandes de crédit", "Dossiers à instruire et décisions prises."],
  "nouvelle-demande-vue": ["Nouvelle demande", "Constitution du dossier."],
  instruction: ["Instruction du dossier", "Analyse, simulation et décision."],
  clients: ["Clients", "Personnes suivies par l'institution."],
  "fiche-client": ["Dossier client", "Situation, activité et parcours."],
  retards: ["Retards", "Échéances impayées et recouvrement."],
  importer: ["Importer des données", "Chargement et contrôle d'un lot CSV."],
  qualite: ["Qualité des données", "Anomalies du dernier lot contrôlé."],
  produits: ["Produits de crédit", "Produits proposés par l'institution."],
  institution: ["Institution", "Informations de votre organisation."],
  audit: ["Journal d'audit", "Traçabilité des opérations."],
};

const chargeurs = new Map();

export function enregistrerChargeur(vue, chargeur) {
  chargeurs.set(vue, chargeur);
}

export function ouvrir(vue) {
  fermerTiroir();
  $$(".vue").forEach(section => section.classList.toggle("vue-masque", section.id !== vue));
  $$(".barre-laterale nav button").forEach(bouton => bouton.classList.toggle("nav-actif", bouton.dataset.vue === vue));

  const [titre, description] = TITRES[vue] || ["", ""];
  $("#titre-vue").textContent = titre;
  $("#description-vue").textContent = description;
  window.scrollTo({ top: 0 });

  chargeurs.get(vue)?.();
}

export function brancherNavigation() {
  $$("[data-vue]").forEach(element => (element.onclick = () => ouvrir(element.dataset.vue)));
}
