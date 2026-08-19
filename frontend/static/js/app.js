/* Point d'entrée : assemble les modules et démarre l'application. */

import { $, $$, api, brancherOnglets, brancherTiroir, fermerDialogue } from "./noyau.js";
import { brancherNavigation, ouvrir } from "./navigation.js";
import { brancherPilotage, chargerVueEnsemble } from "./pilotage.js";
import { brancherClients, ouvrirFicheClient } from "./clients.js";
import { brancherCredit, demarrerDemande, chargerDemandes } from "./credit.js";
import { brancherInstruction, ouvrirInstruction } from "./instruction.js";
import { brancherExploitation } from "./exploitation.js";
import { brancherDonnees } from "./donnees.js?v=20260819-2";
import { brancherParametrage, chargerInstitution } from "./parametrage.js";

async function rafraichir() {
  await Promise.all([chargerInstitution(), chargerVueEnsemble()]);
}

brancherNavigation();
brancherOnglets();
brancherTiroir();

brancherPilotage({ instruction: ouvrirInstruction, fiche: ouvrirFicheClient });
brancherClients({ nouvelleDemande: demarrerDemande });
brancherCredit({ instruction: ouvrirInstruction, fiche: ouvrirFicheClient });
brancherInstruction({ fiche: ouvrirFicheClient });
brancherExploitation({ fiche: ouvrirFicheClient });
brancherDonnees({ rafraichir });
brancherParametrage();

$("#actualiser").onclick = () => rafraichir();

$$("[data-fermer]").forEach(element => (element.onclick = () => fermerDialogue(element.dataset.fermer)));
$$(".dialogue").forEach(dialogue => (dialogue.onclick = evenement => {
  if (evenement.target === dialogue) fermerDialogue(dialogue.id);
}));
document.addEventListener("keydown", evenement => {
  if (evenement.key !== "Escape") return;
  $$(".dialogue:not(.masque)").forEach(dialogue => fermerDialogue(dialogue.id));
});

/* Les boutons « Instruire » présents dans les listes rendues en HTML brut. */
document.addEventListener("click", evenement => {
  const bouton = evenement.target.closest("[data-instruire]");
  if (bouton) ouvrirInstruction(+bouton.dataset.instruire);
});

/* Les listes des lots d'import, chargées une fois au démarrage. */
async function chargerLotsImport() {
  const lots = await api("/api/imports-csv/lots/");
  $("#lot-reference").replaceChildren(...lots.lots.map(lot => new Option(lot.libelle, lot.code)));
  $("#fichiers-attendus").replaceChildren(
    ...lots.fichiers_attendus.map(nom => Object.assign(document.createElement("span"), { textContent: nom })),
  );
}

await Promise.all([rafraichir(), chargerLotsImport()]);
ouvrir("vue-ensemble");
