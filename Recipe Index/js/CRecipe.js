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
    const data = await resp.json();

    if (!resp.ok) {
      // show the API’s error message in a simple popup
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

// called by the ＋ Add Step button
function addField(containerId, fieldName) {
  const container = document.getElementById(containerId);
  const template  = container.querySelector('.instruction-item');
  const clone     = template.cloneNode(true);

  // clear out the textarea
  const ta = clone.querySelector(`textarea[name="${fieldName}"]`);
  ta.value = '';

  // show its remove button
  const btn = clone.querySelector('.remove-btn');
  btn.classList.remove('hidden');

  // renumber all steps, including the new one
  container.appendChild(clone);
  renumberInstructions(container);

  // wire its remove button
  btn.addEventListener('click', () => {
    removeInstructionField(btn);
  });
}

// Called by the ＋ Add Image button
function addImageField() {
  const container = document.getElementById('images-container');
  const template = container.querySelector('.image-item');
  const clone = template.cloneNode(true);

  // Reset values for the new field
  const fileInput = clone.querySelector('input[type="file"]');
  fileInput.value = ''; // Clear file input

  // Show the remove button
  const removeBtn = clone.querySelector('.remove-btn');
  removeBtn.classList.remove('hidden');

  // Reset the primary image radio button
  const primaryRadio = clone.querySelector('input[type="radio"]');
  primaryRadio.checked = false;

  // Get the next index for the radio button value (if required)
  const index = container.children.length;
  primaryRadio.value = index;

  // Wire up the remove button functionality
  removeBtn.addEventListener('click', () => removeImageField(removeBtn));

  container.appendChild(clone);
}

// Remove an image field
function removeImageField(btn) {
  const container = document.getElementById('images-container');
  if (container.children.length > 1) {
    btn.parentElement.remove();
  }
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

document.addEventListener("DOMContentLoaded", () => {
  const ingredientSelect = document.getElementById("ingredient-select");
  if (ingredientSelect) {
    $(ingredientSelect).select2({
      placeholder: "Choose ingredients",
      allowClear: true
    });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const sharedSelect = document.getElementById("shared_users");
  if (sharedSelect) {
    $(sharedSelect).select2({
      placeholder: "Select users to share with",
      allowClear: true
    });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const privacySelect = document.getElementById("privacy");
  const sharedUsersContainer = document.getElementById("shared-users-container");

  privacySelect.addEventListener("change", () => {
    sharedUsersContainer.style.display = privacySelect.value === "2" ? "block" : "none";
  });

  // Trigger it on load
  privacySelect.dispatchEvent(new Event("change"));
});
