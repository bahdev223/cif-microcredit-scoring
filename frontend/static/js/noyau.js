/* Fonctions communes à tous les écrans : accès au DOM, appels API, formats,
   dialogues, onglets et tiroir latéral. Aucun écran ne redéfinit ces briques. */

export const $ = selecteur => document.querySelector(selecteur);
export const $$ = selecteur => [...document.querySelectorAll(selecteur)];

export function creer(balise, proprietes = {}) {
  return Object.assign(document.createElement(balise), proprietes);
}

export async function api(url, options = {}) {
  const reponse = await fetch(url, options);
  const donnees = await reponse.json();
  if (!reponse.ok) throw new Error(donnees.erreur || "Opération impossible");
  return donnees;
}

/* ---------- Formats ---------- */

export const nombre = valeur => new Intl.NumberFormat("fr-FR").format(valeur || 0);
export const montant = valeur => nombre(Math.round(valeur || 0)) + " F";

export function pourcentage(valeur, decimales = 0) {
  if (valeur === null || valeur === undefined) return "—";
  return (valeur * 100).toFixed(decimales).replace(".", ",") + " %";
}

export function date(texte) {
  if (!texte) return "—";
  const [annee, mois, jour] = texte.slice(0, 10).split("-");
  return `${jour}/${mois}/${annee}`;
}

export function horodatage(texte) {
  if (!texte) return "—";
  const moment = new Date(texte);
  return `${date(texte)} ${String(moment.getHours()).padStart(2, "0")}:${String(moment.getMinutes()).padStart(2, "0")}`;
}

export function taille(octets) {
  return octets >= 1024 * 1024
    ? (octets / (1024 * 1024)).toFixed(1).replace(".", ",") + " Mo"
    : Math.max(1, Math.round(octets / 1024)) + " Ko";
}

export function initiales(nom) {
  return (nom || "").split(" ").filter(Boolean).slice(0, 2).map(mot => mot[0].toUpperCase()).join("");
}

export const classe = valeur => (valeur || "inconnu").toLowerCase();

/** Valeur d'indicateur formatée selon le type annoncé par le moteur. */
export function valeurIndicateur(indicateur) {
  if (indicateur.valeur === null || indicateur.valeur === undefined) return "—";
  if (indicateur.format === "montant") return montant(indicateur.valeur);
  if (indicateur.format === "pourcentage") return pourcentage(indicateur.valeur);
  if (indicateur.format === "nombre") return nombre(indicateur.valeur);
  if (indicateur.format === "jours") return indicateur.valeur ? `${indicateur.valeur} jours` : "aucun";
  if (indicateur.format === "mois") return indicateur.valeur ? `${indicateur.valeur} mois` : "non renseignée";
  return indicateur.valeur;
}

/* ---------- Fragments réutilisables ---------- */

export function ligneDonnees(libelle, valeur, classes = "") {
  return `<div class="${classes}"><span class="libelle">${libelle}</span><span class="valeur ${classes.includes("negatif") ? "negatif" : ""}">${valeur}</span></div>`;
}

export function listeDonnees(lignes) {
  return lignes.map(([libelle, valeur, classes]) => ligneDonnees(libelle, valeur, classes || "")).join("");
}

export function listePoints(points, sensParDefaut = "attention") {
  if (!points.length) return '<p class="sous-titre">Aucun élément relevé.</p>';
  return points.map(point => {
    const sens = point.sens === "absent" ? "absent" : sensParDefaut;
    const marque = sens === "favorable" ? "✓" : sens === "absent" ? "○" : "⚠";
    return `<div class="point ${sens}"><span class="marque">${marque}</span><span>${point.texte}${
      point.origine ? ` <span class="secondaire">${point.origine}</span>` : ""}</span></div>`;
  }).join("");
}

export function etatVide(message) {
  return `<p class="etat-vide">${message}</p>`;
}

/* ---------- Icônes ---------- */

export const ICONE_OEIL = '<svg viewBox="0 0 24 24"><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.6"/></svg>';
export const ICONE_CRAYON = '<svg viewBox="0 0 24 24"><path d="m4 16.5-.8 4.3 4.3-.8L19 8.5 15.5 5 4 16.5Z"/><path d="m13.8 6.7 3.5 3.5"/></svg>';
export const ICONE_CORBEILLE = '<svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3m-8 0 1 13h8l1-13M10 11v5m4-5v5"/></svg>';
export const ICONE_DOSSIER = '<svg viewBox="0 0 24 24"><path d="M4 6.5A1.5 1.5 0 0 1 5.5 5h4l2 2.5h7A1.5 1.5 0 0 1 20 9v8.5A1.5 1.5 0 0 1 18.5 19h-13A1.5 1.5 0 0 1 4 17.5Z"/><path d="M8.5 12.5h7M8.5 15.5h4"/></svg>';

export function boutonIcone(classes, libelle, icone) {
  const bouton = creer("button", { className: "action-icone " + classes, type: "button", title: libelle, innerHTML: icone });
  bouton.setAttribute("aria-label", libelle);
  return bouton;
}

/* ---------- Dialogues ---------- */

export function ouvrirDialogue(identifiant) {
  $("#" + identifiant).classList.remove("masque");
  document.body.style.overflow = "hidden";
}

export function fermerDialogue(identifiant) {
  $("#" + identifiant).classList.add("masque");
  document.body.style.overflow = "";
}

/* ---------- Onglets ---------- */

export function brancherOnglets() {
  $$("[data-onglets]").forEach(groupe => {
    const boutons = [...groupe.querySelectorAll("button")];
    boutons.forEach(bouton => {
      bouton.onclick = () => {
        boutons.forEach(autre => {
          autre.classList.toggle("onglet-actif", autre === bouton);
          $("#" + autre.dataset.panneau).classList.toggle("masque", autre !== bouton);
        });
      };
    });
  });
}

export function activerPremierOnglet(groupe) {
  const boutons = [...document.querySelector(`[data-onglets="${groupe}"]`).querySelectorAll("button")];
  boutons[0]?.click();
}

/* ---------- Tiroir latéral ---------- */

let actionTiroir = null;

export function ouvrirTiroir({ surtexte, titre, sousTitre, contenu, action }) {
  $("#tiroir-surtexte").textContent = surtexte || "Détail";
  $("#tiroir-titre").textContent = titre;
  $("#tiroir-sous-titre").textContent = sousTitre || "";
  $("#tiroir-corps").innerHTML = contenu;
  actionTiroir = action || null;
  $("#tiroir-ouvrir-dossier").classList.toggle("masque", !action);
  $("#tiroir").classList.remove("masque");
  $("#voile-tiroir").classList.remove("masque");
}

export function fermerTiroir() {
  $("#tiroir").classList.add("masque");
  $("#voile-tiroir").classList.add("masque");
}

export function brancherTiroir() {
  $("#fermer-tiroir").onclick = fermerTiroir;
  $("#voile-tiroir").onclick = fermerTiroir;
  $("#tiroir-ouvrir-dossier").onclick = () => {
    const action = actionTiroir;
    fermerTiroir();
    action?.();
  };
}
