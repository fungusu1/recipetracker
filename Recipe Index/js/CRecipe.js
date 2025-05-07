// called by the ＋ Add Ingredient button
function addIngredientField() {
  const container = document.getElementById('ingredients-container');
  const template = container.querySelector('.ingredient-item');
  const clone    = template.cloneNode(true);

  // reset values & show remove button
  clone.querySelector('input[name="ingredient_name"]').value = '';
  clone.querySelector('input[name="quantity"]').value        = '';
  clone.querySelector('.remove-btn').classList.remove('hidden');

  // wire its remove button
  clone.querySelector('.remove-btn')
       .addEventListener('click', () => removeIngredientField(clone.querySelector('.remove-btn')));

  container.appendChild(clone);
}

// remove a row (only if >1 left)
function removeIngredientField(btn) {
  const container = document.getElementById('ingredients-container');
  if (container.children.length > 1) {
    btn.parentElement.remove();
  }
}

// prompt for a brand-new base ingredient & append it to the <datalist>
async function promptNewIngredient() {
  const name = prompt("Enter new ingredient name:");
  if (!name) return;
  const unit = prompt("Enter default unit (e.g. g, tsp):", "");

  try {
    const resp = await fetch('/api/base_ingredients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, default_unit: unit })
    });
    if (!resp.ok) throw new Error(resp.statusText);
    const ingr = await resp.json();

    // add to datalist
    const dl = document.getElementById('ingredient-list');
    const opt = document.createElement('option');
    opt.value = ingr.name;
    dl.appendChild(opt);
  } catch (err) {
    alert("Could not add new ingredient: " + err.message);
  }
}
