/* Produits de crédit et informations de l'institution.

   L'écran des règles a été retiré : il affichait un catalogue codé en dur,
   alors que les règles applicables appartiennent désormais aux cadres
   d'analyse configurés par l'institution. */

import {
  $, api, boutonIcone, creer, fermerDialogue, ICONE_CORBEILLE, ICONE_CRAYON,
  listeDonnees, montant, ouvrirDialogue,
} from "./noyau.js";
import { enregistrerChargeur } from "./navigation.js";

export function brancherParametrage() {
  enregistrerChargeur("produits", chargerProduits);
  enregistrerChargeur("institution", chargerInstitution);

  $("#nouveau-produit").onclick = () => ouvrirFormulaireProduit();
  $("#formulaire-produit").onsubmit = enregistrerProduit;
  $("#modifier-institution").onclick = () => ouvrirDialogue("dialogue-institution");
  $("#formulaire-institution").onsubmit = enregistrerInstitution;
}

/* ---------- Produits ---------- */

async function chargerProduits() {
  const donnees = await api("/api/produits-credit/");
  const corps = $("#liste-produits");
  corps.replaceChildren();

  if (!donnees.produits.length) {
    corps.innerHTML = '<tr><td colspan="6" class="etat-vide">Aucun produit configuré. Ajoutez ceux de votre institution.</td></tr>';
    return;
  }

  donnees.produits.forEach(produit => {
    const bornesMontant = produit.montant_max
      ? `${montant(produit.montant_min)} à ${montant(produit.montant_max)}` : "non bornés";
    const bornesDuree = produit.duree_max_mois
      ? `${produit.duree_min_mois} à ${produit.duree_max_mois} mois` : "non bornées";
    const ligne = creer("tr");
    ligne.insertAdjacentHTML("beforeend", `
      <td class="principale">${produit.code}</td>
      <td>${produit.libelle}</td>
      <td class="montant">${bornesMontant}</td>
      <td>${bornesDuree}</td>
      <td>${produit.secteurs_vises || "—"}</td>`);

    const actions = creer("td", { className: "actions-tableau" });
    const modifier = boutonIcone("modifier", "Modifier", ICONE_CRAYON);
    const supprimer = boutonIcone("supprimer", "Supprimer", ICONE_CORBEILLE);
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

async function enregistrerProduit(evenement) {
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
}

/* ---------- Règles ---------- */


/* ---------- Institution ---------- */

export async function chargerInstitution() {
  const donnees = await api("/api/institution/");
  const institution = donnees.institution;

  $("#nom-marque").textContent = institution.sigle || "CIF";
  $("#marque-logo").textContent = (institution.sigle || "C")[0];
  $("#entete-sigle").textContent = institution.nom;
  $("#detail-institution").innerHTML = listeDonnees([
    ["Nom", institution.nom],
    ["Sigle", institution.sigle],
    ["Ville", institution.ville || "—"],
    ["Pays", institution.pays],
  ]);
  $("#resume-institution-accueil").innerHTML = listeDonnees([
    ["Institution", institution.nom],
    ["Localisation", [institution.ville, institution.pays].filter(Boolean).join(", ") || "—"],
  ]);
  for (const champ of ["nom", "sigle", "ville", "pays"]) {
    $("#institution-" + champ).value = institution[champ] || "";
  }
}

async function enregistrerInstitution(evenement) {
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
    chargerInstitution();
  } catch (erreur) {
    $("#message-institution").textContent = erreur.message;
  }
}
