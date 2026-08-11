const form = document.querySelector('#credit-form');
const result = document.querySelector('#result');
const historyList = document.querySelector('#history-list');
let latest = null;

const format = (value) => new Intl.NumberFormat('fr-FR').format(value) + ' FCFA';
const renderList = (selector, values) => {
  document.querySelector(selector).innerHTML = values.length
    ? values.map((item) => `<li>${item}</li>`).join('')
    : '<li>Aucun element particulier.</li>';
};

function analyse(values) {
  const capacity = values.income - values.expenses;
  const installment = values.amount / 12;
  let risk = 45;
  const positives = [];
  const negatives = [];
  const rules = [];

  if (capacity >= installment * 2) { risk -= 18; positives.push("Capacite mensuelle confortable par rapport a l'echeance estimee."); }
  else if (capacity >= installment) { risk -= 5; positives.push('Capacite mensuelle suffisante mais a surveiller.'); }
  else { risk += 25; negatives.push("Capacite mensuelle inferieure a l'echeance estimee."); rules.push('R01 - capacite de remboursement insuffisante'); }
  if (values.businessAge >= 24) { risk -= 10; positives.push('Activite exercee depuis au moins 24 mois.'); }
  else if (values.businessAge < 12) { risk += 12; negatives.push('Activite recente : recul limite sur les revenus.'); rules.push('R02 - anciennete faible'); }
  if (values.latePayments === 0) { risk -= 8; positives.push('Aucun retard de paiement renseigne.'); }
  else { risk += values.latePayments === 1 ? 12 : 25; negatives.push('Retards precedents declares.'); rules.push('R03 - historique de retard'); }
  if (values.tontine === 'good') { risk -= 7; positives.push('Cotisations tontine regulieres.'); }
  else if (values.tontine === 'none') { risk += 4; negatives.push('Information tontine indisponible.'); }

  risk = Math.max(5, Math.min(95, Math.round(risk)));
  const quality = [values.income, values.expenses, values.businessAge, values.amount].every(Number.isFinite) && values.name.trim() ? 'Bonne : les champs essentiels sont renseignes.' : 'Incomplete : verifier le dossier avant toute decision.';
  if (!rules.length) rules.push('Aucune regle bloquante declenchee');
  return { risk, positives, negatives, rules, quality, capacity, installment };
}

function display(assessment, values) {
  const label = assessment.risk < 30 ? 'Risque faible' : assessment.risk < 60 ? 'Risque modere' : 'Risque eleve';
  const recommendation = assessment.risk < 30 ? 'A examiner favorablement par l\'agent.' : assessment.risk < 60 ? 'Demander une verification complementaire avant decision.' : 'A ne pas valider sans analyse humaine approfondie.';
  document.querySelector('#risk-label').textContent = label;
  document.querySelector('#risk-score').textContent = assessment.risk;
  document.querySelector('#recommendation').textContent = recommendation;
  document.querySelector('#data-quality').textContent = assessment.quality;
  renderList('#positive-factors', assessment.positives);
  renderList('#negative-factors', assessment.negatives);
  renderList('#rules', assessment.rules);
  result.classList.remove('hidden');
  const item = document.createElement('li');
  item.textContent = `${values.name} - ${label.toLowerCase()} (${assessment.risk}/100) - demande ${format(values.amount)}`;
  if (historyList.textContent.includes('Aucune analyse')) historyList.innerHTML = '';
  historyList.prepend(item);
}

function valuesFromForm() {
  return { name: document.querySelector('#name').value, sector: document.querySelector('#sector').value, amount: Number(document.querySelector('#amount').value), income: Number(document.querySelector('#income').value), expenses: Number(document.querySelector('#expenses').value), businessAge: Number(document.querySelector('#business-age').value), latePayments: Number(document.querySelector('#late-payments').value), tontine: document.querySelector('#tontine').value };
}
form.addEventListener('submit', (event) => { event.preventDefault(); latest = valuesFromForm(); display(analyse(latest), latest); });
document.querySelector('#simulate').addEventListener('click', () => { if (!latest) return; document.querySelector('#amount').value = Math.round(latest.amount * .8 / 5000) * 5000; latest = valuesFromForm(); display(analyse(latest), latest); });
document.querySelector('#clear-history').addEventListener('click', () => { historyList.innerHTML = '<li>Aucune analyse dans cette session.</li>'; });
