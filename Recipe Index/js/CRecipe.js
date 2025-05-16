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
      alert(data.error || "Could not add ingredient");
      return;
    }


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
  errorDiv.textContent = '';
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
    // Add new ingredient to all select2 dropdowns (do not select it)
    const newOption = new Option(data.name, data.name, false, false);
    $('.ingredient-select').each(function() {
      if ($(this).find(`option[value="${data.name}"]`).length === 0) {
        $(this).append(newOption.cloneNode(true));
      }
    });
    // Update the global ingredientUnits object
    if (window.ingredientUnits) {
      window.ingredientUnits[data.name] = data.default_unit || '';
    }
    updateUnitLabels();
    closeIngredientOverlay();
    document.getElementById('new-ingredient-name').value = '';
    document.getElementById('new-ingredient-unit').value = '';
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


  document.querySelectorAll('input[name="privacy"]').forEach(radio => {
    radio.addEventListener('change', function() {
      document.getElementById('shared-with-section').style.display =
        this.value === 'shared' ? 'block' : 'none';
    });
  });

  const checkedPrivacy = document.querySelector('input[name="privacy"]:checked');
  if (checkedPrivacy) {
    document.getElementById('shared-with-section').style.display =
      checkedPrivacy.value === 'shared' ? 'block' : 'none';
  }


  const instrContainer = document.getElementById('instructions-container');
  if (instrContainer) {
    const btns = instrContainer.querySelectorAll('.remove-btn');
    btns.forEach((btn, idx) => {
      if (idx > 0) {
        btn.classList.remove('hidden');
        btn.addEventListener('click', function() {
          removeInstructionField(btn);
        });
      }
    });
  }

  // SHARED USERS LOGIC
  const sharedUsers = [];
  const sharedList = document.getElementById('shared-users-list');
  const hiddenInput = document.getElementById('shared-user-ids');
  if (sharedList) {
    sharedList.querySelectorAll('li[data-user-id]').forEach(li => {
      const id = parseInt(li.getAttribute('data-user-id'));
      const name = li.querySelector('.shared-user-name').textContent.trim();
      sharedUsers.push({id, display_name: name});
    });
    if (hiddenInput) hiddenInput.value = sharedUsers.map(u => u.id).join(',');
    sharedList.querySelectorAll('.remove-btn').forEach(btn => {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        const li = btn.closest('li');
        const id = parseInt(li.getAttribute('data-user-id'));
        const idx = sharedUsers.findIndex(u => u.id === id);
        if (idx !== -1) sharedUsers.splice(idx, 1);
        li.remove();
        if (hiddenInput) hiddenInput.value = sharedUsers.map(u => u.id).join(',');
      });
    });
  }

  // Add shared user
  document.getElementById('add-shared-user-btn').addEventListener('click', async function() {
    const input = document.getElementById('shared-user-input');
    const errorDiv = document.getElementById('shared-user-error');
    const list = document.getElementById('shared-users-list');
    const hiddenInput = document.getElementById('shared-user-ids');
    const name = input.value.trim();
    errorDiv.textContent = '';
    if (!name) return;

    // Prevent duplicates
    if (sharedUsers.some(u => u.display_name.toLowerCase() === name.toLowerCase())) {
      errorDiv.textContent = 'Already added.';
      return;
    }

    // Prevent adding yourself
    if (window.currentUserDisplayName && name.toLowerCase() === window.currentUserDisplayName.toLowerCase()) {
      errorDiv.textContent = 'You cannot add yourself.';
      return;
    }

    try {
      const resp = await fetch('/api/find_user', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({display_name: name})
      });
      const data = await resp.json();
      if (!resp.ok) {
        errorDiv.textContent = data.error || 'User not found';
        return;
      }
      sharedUsers.push({id: data.id, display_name: data.display_name});
      // Update list
      const li = document.createElement('li');
      li.setAttribute('data-user-id', data.id);
      li.textContent = data.display_name + ' ';

      // Add delete button
      const delBtn = document.createElement('button');
      delBtn.textContent = '✕';
      delBtn.className = 'remove-btn';
      delBtn.style.marginLeft = '0.5em';
      delBtn.style.background = '#ef4444';
      delBtn.style.color = 'white';
      delBtn.style.border = 'none';
      delBtn.style.borderRadius = '0.25em';
      delBtn.style.cursor = 'pointer';
      delBtn.style.fontWeight = 'bold';
      delBtn.style.fontSize = '1em';
      delBtn.onclick = function(e) {
        e.preventDefault();
        const idx = sharedUsers.findIndex(u => u.id === data.id);
        if (idx !== -1) sharedUsers.splice(idx, 1);
        li.remove();
        if (hiddenInput) hiddenInput.value = sharedUsers.map(u => u.id).join(',');
      };

      li.appendChild(delBtn);
      list.appendChild(li);

      // Update hidden input
      hiddenInput.value = sharedUsers.map(u => u.id).join(',');
      input.value = '';

      const successDiv = document.getElementById('shared-user-success');
      successDiv.style.display = 'block';
      setTimeout(() => { successDiv.style.display = 'none'; }, 1500);
    } catch (err) {
      errorDiv.textContent = 'Error: ' + err.message;
    }
  });

  document.getElementById('shared-user-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      document.getElementById('add-shared-user-btn').click();
    }
  });
});
