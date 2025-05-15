// Initialize select2 on all ingredient selects on page load
$(document).ready(function() {
  $('.ingredient-select').each(function() {
    if ($(this).next('.select2').length) {
      $(this).select2('destroy');
      $(this).next('.select2').remove();
    }
  });
  $('.ingredient-select').select2({
    placeholder: 'Select ingredient',
    allowClear: true,
    width: 'style'
  }).on('change', function() {
    updateIngredientOptions();
    updateUnitLabels();
  });
  updateIngredientOptions();
  updateUnitLabels();
});

// Prevent duplicate ingredient selection across all selects
function updateIngredientOptions() {
  const selected = [];
  document.querySelectorAll('.ingredient-select').forEach(sel => {
    if (sel.value) selected.push(sel.value);
  });
  document.querySelectorAll('.ingredient-select').forEach(sel => {
    const currentVal = sel.value;
    Array.from(sel.options).forEach(opt => {
      if (opt.value && opt.value !== currentVal && selected.includes(opt.value)) {
        opt.disabled = true;
      } else {
        opt.disabled = false;
      }
    });
    $(sel).trigger('change.select2');
  });
}

function reinitAllIngredientSelect2() {
  $('.ingredient-select').each(function() {
    if ($(this).next('.select2').length) {
      $(this).select2('destroy');
      $(this).next('.select2').remove();
    }
    $(this).select2({
      placeholder: 'Select ingredient',
      allowClear: true,
      width: 'style'
    }).on('change', function() {
      updateIngredientOptions();
      updateUnitLabels();
    });
  });
  updateUnitLabels();
}

$(document).ready(function() {
  reinitAllIngredientSelect2();
  updateIngredientOptions();
  updateUnitLabels();
});

// called by the ＋ Add Ingredient button
function addIngredientField() {
  const container = document.getElementById('ingredients-container');
  const template = container.querySelector('.ingredient-item');
  const clone    = template.cloneNode(true);

  const oldSelect2 = clone.querySelector('.select2');
  if (oldSelect2) oldSelect2.remove();

  const select = clone.querySelector('select[name="ingredient_name"]');
  if (select) {
    if ($(select).next('.select2').length) {
      $(select).select2('destroy');
      $(select).next('.select2').remove();
    }
    select.value = '';
    $(select).select2({
      placeholder: 'Select ingredient',
      allowClear: true,
      width: 'style'
    }).on('change', function() {
      updateIngredientOptions();
      updateUnitLabels();
    });
  }
  clone.querySelector('input[name="quantity"]').value        = '';
  clone.querySelector('.remove-btn').classList.remove('hidden');


  clone.querySelector('.remove-btn')
       .addEventListener('click', () => {
         removeIngredientField(clone.querySelector('.remove-btn'));
         updateIngredientOptions();
         updateUnitLabels();
       });

  container.appendChild(clone);
  reinitAllIngredientSelect2();
  updateIngredientOptions();
  updateUnitLabels();
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
    const data = await resp.json();

    if (!resp.ok) {
      // show the API's error message in a simple popup
      alert(data.error || "Could not add ingredient");
      return;
    }

    // success: add to datalist
    const dl  = document.getElementById('ingredient-list');
    const opt = document.createElement('option');
    opt.value = data.name;
    dl.appendChild(opt);

  } catch (err) {
    alert("Error adding ingredient: " + err.message);
  }
}


function addField(containerId, fieldName) {
  const container = document.getElementById(containerId);
  const template  = container.querySelector('.instruction-item');
  const clone     = template.cloneNode(true);


  const ta = clone.querySelector(`textarea[name="${fieldName}"]`);
  ta.value = '';


  const btn = clone.querySelector('.remove-btn');
  btn.classList.remove('hidden');


  container.appendChild(clone);
  renumberInstructions(container);


  btn.addEventListener('click', () => {
    removeInstructionField(btn);
  });
}

function removeInstructionField(btn) {
  const container = document.getElementById('instructions-container');
  if (container.children.length > 1) {
    btn.parentElement.remove();
    renumberInstructions(container);
  }
}

function renumberInstructions(container) {
  container
    .querySelectorAll('.instruction-item')
    .forEach((item, idx) => {
      item.querySelector('.item-label').textContent = (idx + 1) + '.';
    });
}

function updateUnitLabels() {
  const items = document.querySelectorAll('.ingredient-item');
  items.forEach((item, idx) => {
    const select = item.querySelector('select[name="ingredient_name"]');
    const unitLabelInside = item.querySelector('.unit-label-inside');
    const unitLabelOutside = item.querySelector('.unit-label-outside');
    const unit = window.ingredientUnits?.[select?.value] || '';
    if (idx === 0) {
      // First row
      if (unitLabelInside) unitLabelInside.textContent = unit ? `(${unit})` : '';
      if (unitLabelInside) unitLabelInside.classList.remove('hidden');
      if (unitLabelOutside) unitLabelOutside.classList.add('hidden');
    } else {
      // Other rows
      if (unitLabelInside) unitLabelInside.textContent = '';
      if (unitLabelInside) unitLabelInside.classList.add('hidden');
      if (unitLabelOutside) {
        unitLabelOutside.textContent = unit ? `(${unit})` : '';
        unitLabelOutside.classList.remove('hidden');
      }
    }
  });
}

function openIngredientOverlay() {
  const overlay = document.getElementById('ingredient-overlay');
  overlay.classList.remove('hidden');
  setTimeout(() => overlay.classList.add('show'), 10);
  document.getElementById('new-ingredient-name').value = '';
  document.getElementById('new-ingredient-unit').value = '';
  document.getElementById('ingredient-overlay-error').textContent = '';
}
function closeIngredientOverlay() {
  const overlay = document.getElementById('ingredient-overlay');
  overlay.classList.remove('show');
  setTimeout(() => overlay.classList.add('hidden'), 300);
}
async function submitNewIngredient() {
  const name = document.getElementById('new-ingredient-name').value.trim();
  const unit = document.getElementById('new-ingredient-unit').value.trim();
  const errorDiv = document.getElementById('ingredient-overlay-error');
  if (!name) {
    errorDiv.textContent = 'Please enter an ingredient name.';
    return;
  }
  try {
    const resp = await fetch('/api/base_ingredients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, default_unit: unit })
    });
    const data = await resp.json();
    if (!resp.ok) {
      errorDiv.textContent = data.error || 'Could not add ingredient';
      return;
    }
    closeIngredientOverlay();
    window.location.reload();
  } catch (err) {
    errorDiv.textContent = 'Error adding ingredient: ' + err.message;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const overlay = document.getElementById('ingredient-overlay');
  if (overlay) {
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) {
        closeIngredientOverlay();
      }
    });
  }
});
