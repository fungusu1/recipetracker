document.addEventListener('DOMContentLoaded', function () {
  initSelect2();
  setupPrivacyToggle();
  setupSharedUserLogic();
  setupIngredientOverlay();
  prefillIngredients();
  prefillInstructions();
  updateIngredientOptions();
  updateUnitLabels();

  document.getElementById('add-instruction-btn').addEventListener('click', () => {
    addInstructionField();
  });

  document.getElementById('add-ingredient-btn').addEventListener('click', () => {
    addIngredientField();
  });
});

function prefillIngredients() {
  const container = document.getElementById('ingredients-container');
  container.innerHTML = '';

  window.prefilledIngredients.forEach(({ name, quantity }) => {
    const div = document.createElement('div');
    div.className = 'ingredient-item flex-row';
    div.innerHTML = `
      <div class="flex-half">
        <select name="ingredients[]" class="ingredient-select textarea-wrapper" required>
          <option value="">Select ingredient</option>
          ${Object.keys(window.ingredientUnits).map(i =>
            `<option value="${i}" ${i === name ? 'selected' : ''}>${i}</option>`
          ).join('')}
        </select>
        <span class="unit-label"></span>
      </div>
      <div class="flex-half quantity-group">
        <input type="number" name="quantities[]" value="${quantity}" required class="quantity-input">
        <span class="unit-label-inside"></span>
        <span class="unit-label-outside hidden"></span>
      </div>
      <button type="button" class="remove-btn" onclick="removeIngredientField(this)">✕</button>
    `;
    container.appendChild(div);
  });

  reinitAllIngredientSelect2();
  updateIngredientOptions();
  updateUnitLabels();
}

function prefillInstructions() {
  const container = document.getElementById('instructions-container');
  container.innerHTML = '';
  window.prefilledInstructions.forEach((step, index) => {
    const div = document.createElement('div');
    div.className = 'instruction-item';
    div.innerHTML = `
      <div class="item-label">${index + 1}.</div>
      <textarea name="instructions" required rows="1" class="textarea-wrapper">${step}</textarea>
      <button type="button" class="remove-btn" onclick="removeInstructionField(this)">✕</button>
    `;
    container.appendChild(div);
  });
  renumberInstructions(container);
}

// Add ingredient field
function addIngredientField() {
  const container = document.getElementById('ingredients-container');
  const div = document.createElement('div');
  div.className = 'ingredient-item flex-row';

  div.innerHTML = `
    <div class="flex-half">
      <select name="ingredients[]" class="ingredient-select textarea-wrapper" required>
        <option value="">Select ingredient</option>
        ${Object.keys(window.ingredientUnits).map(i =>
          `<option value="${i}">${i}</option>`
        ).join('')}
      </select>
      <span class="unit-label"></span>
    </div>
    <div class="flex-half quantity-group">
      <input type="number" name="quantities[]" required class="quantity-input">
      <span class="unit-label-inside"></span>
      <span class="unit-label-outside hidden"></span>
    </div>
    <button type="button" class="remove-btn" onclick="removeIngredientField(this)">✕</button>
  `;
  container.appendChild(div);
  reinitAllIngredientSelect2();
  updateIngredientOptions();
  updateUnitLabels();
}

function removeIngredientField(btn) {
  const container = document.getElementById('ingredients-container');
  if (container.children.length > 1) {
    btn.parentElement.remove();
    updateIngredientOptions();
  }
}

function reinitAllIngredientSelect2() {
  $('.ingredient-select').each(function () {
    if ($(this).next('.select2').length) {
      $(this).select2('destroy');
      $(this).next('.select2').remove();
    }
    $(this).select2({
      placeholder: 'Select ingredient',
      allowClear: true,
      width: 'style'
    }).on('change', function () {
      updateIngredientOptions();
      updateUnitLabels();
    });
  });
}

function updateIngredientOptions() {
  const selected = Array.from(document.querySelectorAll('.ingredient-select'))
    .map(sel => sel.value)
    .filter(Boolean);

  document.querySelectorAll('.ingredient-select').forEach(sel => {
    const current = sel.value;
    Array.from(sel.options).forEach(opt => {
      opt.disabled = opt.value && opt.value !== current && selected.includes(opt.value);
    });
    $(sel).trigger('change.select2');
  });
}

function updateUnitLabels() {
  document.querySelectorAll('.ingredient-item').forEach((item, idx) => {
    const select = item.querySelector('select[name="ingredient_name"]');
    const inside = item.querySelector('.unit-label-inside');
    const outside = item.querySelector('.unit-label-outside');
    const unit = window.ingredientUnits?.[select?.value] || '';
    if (idx === 0) {
      inside.textContent = unit ? `(${unit})` : '';
      inside.classList.remove('hidden');
      outside.classList.add('hidden');
    } else {
      inside.textContent = '';
      inside.classList.add('hidden');
      outside.textContent = unit ? `(${unit})` : '';
      outside.classList.remove('hidden');
    }
  });
}

// Instructions
function addInstructionField() {
  const container = document.getElementById('instructions-container');
  const div = document.createElement('div');
  div.className = 'instruction-item';
  div.innerHTML = `
    <div class="item-label"></div>
    <textarea name="instructions" required rows="1" class="textarea-wrapper"></textarea>
    <button type="button" class="remove-btn" onclick="removeInstructionField(this)">✕</button>
  `;
  container.appendChild(div);
  renumberInstructions(container);
}

function removeInstructionField(btn) {
  const container = document.getElementById('instructions-container');
  if (container.children.length > 1) {
    btn.parentElement.remove();
    renumberInstructions(container);
  }
}

function renumberInstructions(container) {
  container.querySelectorAll('.instruction-item').forEach((item, i) => {
    item.querySelector('.item-label').textContent = `${i + 1}.`;
  });
}

// Shared users
function setupPrivacyToggle() {
  const radios = document.querySelectorAll('input[name="privacy"]');
  const section = document.getElementById('shared-with-section');
  radios.forEach(radio => {
    radio.addEventListener('change', () => {
      section.style.display = radio.value === '2' ? 'block' : 'none';
    });
  });

  if (document.querySelector('input[name="privacy"]:checked')?.value === '2') {
    section.style.display = 'block';
  }
}

function setupSharedUserLogic() {
  document.querySelectorAll('.remove-shared-user-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const li = btn.closest('li');
      const userId = btn.dataset.userId;
      li.remove();
      const hiddenInput = document.getElementById('shared-user-ids');
      hiddenInput.value = hiddenInput.value.split(',').filter(id => id !== userId).join(',');
    });
  });
}

// Overlay
function openIngredientOverlay() {
  const overlay = document.getElementById('ingredient-overlay');
  overlay.classList.remove('hidden');
  setTimeout(() => overlay.classList.add('show'), 10);
  document.getElementById('new-ingredient-name').value = '';
  document.getElementById('new-ingredient-unit').value = '';
  document.getElementById('ingredient-overlay-error')?.textContent = '';
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
    addIngredientField(name);
  } catch (err) {
    errorDiv.textContent = 'Error: ' + err.message;
  }
}

// for overlay
window.submitNewIngredient = submitNewIngredient;
window.closeIngredientOverlay = closeIngredientOverlay;
window.openIngredientOverlay = openIngredientOverlay;
