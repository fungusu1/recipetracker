document.addEventListener('DOMContentLoaded', function() {
  reinitAllIngredientSelect2();
  setupPrivacyToggle();
  prefillIngredients();
  prefillInstructions();
  setupIngredientOverlay();
  setupSharedUserLogicI();

});

// Initialise select2

function initSelect2() {
  $('.ingredient-select').each(function () {
    if ($(this).next('.select2').length) {
      $(this).select2('destroy');
      $(this).next('.select2').remove();
    }
  });
  $('.ingredient-select').select2({
    placeholder: 'Select ingredient',
    allowClear: true,
    width: 'style'
  }).on('change', function () {
    updateIngredientOptions();
    updateUnitLabels();
  });
  updateIngredientOptions();
  updateUnitLabels();
}

// Setup prefilled information
  // Prefill Ingredients
function prefillIngredients() {
  const container = document.getElementById('ingredients-container');
  window.prefilledIngredients.forEach(({ name, quantity }) => {
    const div = document.createElement('div');
    div.className = 'ingredient-item';
    div.innerHTML = `
      <select name="ingredient_name" class="ingredient-select" required>
        ${Object.keys(window.ingredientUnits).map(i =>
          `<option value="${i}" ${i === name ? 'selected' : ''}>${i}</option>`
        ).join('')}
      </select>
      <input type="number" name="quantity" value="${quantity}" required>
      <span class="unit-label-outside">${window.ingredientUnits[name] || ''}</span>
      <button type="button" class="remove-btn">✕</button>
    `;
    div.querySelector('.remove-btn').addEventListener('click', () => {
      div.remove();
      updateIngredientOptions();
    });
    container.appendChild(div);
  });
  initSelect2();
}
  // Prefill Instructions
function prefillInstructions() {
  const container = document.getElementById('instructions-container');
  window.prefilledInstructions.forEach((text, i) => {
    const div = document.createElement('div');
    div.className = 'instruction-item';
    div.innerHTML = `
      <div class="item-label">${i + 1}.</div>
      <textarea name="instructions[]" required>${text}</textarea>
      <button type="button" class="remove-btn">✕</button>
    `;
    div.querySelector('.remove-btn').addEventListener('click', () => {
      div.remove();
      renumberInstructions(container);
    });
    container.appendChild(div);
  });
}

// Ingredient overlay
function setupIngredientOverlay() {
  document.getElementById('add-ingredient-btn').addEventListener('click', () => {
    document.getElementById('ingredient-overlay').classList.remove('hidden');
  });

  document.querySelector('#ingredient-overlay .overlay').addEventListener('click', (e) => {
    if (e.target.id === 'ingredient-overlay') closeIngredientOverlay();
  });

  document.querySelector('#ingredient-overlay .overlay-actions button:last-child')
    .addEventListener('click', closeIngredientOverlay);

  document.querySelector('#ingredient-overlay .overlay-actions button:first-child')
    .addEventListener('click', async () => {
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

        window.ingredientUnits[name] = unit;
        closeIngredientOverlay();
        addIngredientField(name);

      } catch (err) {
        errorDiv.textContent = 'Error: ' + err.message;
      }
    });
}

function closeIngredientOverlay() {
  const overlay = document.getElementById('ingredient-overlay');
  overlay.classList.add('remove');
}

function addIngredientField(selectedName = '') {
  const container = document.getElementById('ingredients-container');
  const div = document.createElement('div');
  div.className = 'ingredient-item';
  div.innerHTML = `
    <select name="ingredient_name" class="ingredient-select" required>
      ${Object.keys(window.ingredientUnits).map(i =>
        `<option value="${i}" ${i === selectedName ? 'selected' : ''}>${i}</option>`
      ).join('')}
    </select>
    <input type="number" name="quantity" required>
    <span class="unit-label-outside">${window.ingredientUnits[selectedName] || ''}</span>
    <button type="button" class="remove-btn">✕</button>
  `;
  div.querySelector('.remove-btn').addEventListener('click', () => {
    div.remove();
    updateIngredientOptions();
  });
  container.appendChild(div);
  initSelect2();
  updateIngredientOptions();
  updateUnitLabels();
}

// select2 Helpers
function updateIngredientOptions() {
  const selected = Array.from(document.querySelectorAll('.ingredient-select'))
    .map(sel => sel.value).filter(Boolean);

  document.querySelectorAll('.ingredient-select').forEach(sel => {
    const current = sel.value;
    Array.from(sel.options).forEach(opt => {
      opt.disabled = opt.value && opt.value !== current && selected.includes(opt.value);
    });
    $(sel).trigger('change.select2');
  });
}

function updateUnitLabels() {
  document.querySelectorAll('.ingredient-item').forEach(item => {
    const select = item.querySelector('.ingredient-select');
    const label = item.querySelector('.unit-label-outside');
    label.textContent = window.ingredientUnits?.[select?.value] || '';
  });
}

// Instructions
document.getElementById('add-instruction-btn').addEventListener('click', () => {
  const container = document.getElementById('instructions-container');
  const div = document.createElement('div');
  div.className = 'instruction-item';
  div.innerHTML = `
    <div class="item-label"></div>
    <textarea name="instructions[]" required></textarea>
    <button type="button" class="remove-btn">✕</button>
  `;
  div.querySelector('.remove-btn').addEventListener('click', () => {
    div.remove();
    renumberInstructions(container);
  });
  container.appendChild(div);
  renumberInstructions(container);
});

function renumberInstructions(container) {
  container.querySelectorAll('.instruction-item').forEach((item, idx) => {
    item.querySelector('.item-label').textContent = `${idx + 1}.`;
  });
}

// Shared users
function setupPrivacyToggle() {
  const radios = document.querySelectorAll('input[name="privacy"]');
  const section = document.getElementById('shared-with-section');
  radios.forEach(radio => {
    radio.addEventListener('change', () => {
      section.style.display = radio.value === 'shared' ? 'block' : 'none';
    });
  });

  // Show if shared was already selected
  document.querySelector('input[name="privacy"]:checked')?.value === 'shared' &&
    (section.style.display = 'block');
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
