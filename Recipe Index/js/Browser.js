$(document).ready(function() {
  let ingredientCount = 1;

  const searchBtn = $('<button type="submit" class="search-btn">Search</button>');

  function moveSearchButton() {
    searchBtn.detach();
    const lastGroup = $('#ingredients-search-container .ingredient-search-item').last();
    if (lastGroup.length) {
      const removeBtn = lastGroup.find('.remove-ingredient-btn');
      if (removeBtn.length) {
        removeBtn.after(searchBtn);
      } else {
        lastGroup.find('.unit-label').after(searchBtn);
      }
    }
  }

  function createIngredientGroup(idx) {
    const group = $(
      `<div class="ingredient-search-item">
        <label for="ingredient-${idx}">Ingredient:</label>
        <select id="ingredient-${idx}" name="ingredient[]">
          <option value="">-- Select ingredient --</option>
        </select>
        <span class="amount-group">
          <label for="amount-${idx}" class="amount-label">Amount:</label>
          <input type="number" id="amount-${idx}" name="servings[]" min="1" placeholder="e.g. 4">
          <span class="unit-label"></span>
        </span>
      </div>`
    );
    for (const name in ingredientUnits) {
      group.find('select').append(`<option value="${name}">${name}</option>`);
    }

    group.find('select').on('change', function() {
      const selected = $(this).val();
      const unit = ingredientUnits[selected] || '';
      group.find('.unit-label').text(unit ? '(' + unit + ')' : '');
    });
    // Remove button
    const removeBtn = $('<button type="button" class="remove-ingredient-btn">✕</button>');
    removeBtn.on('click', function() {
      group.remove();
      moveSearchButton();
    });
    group.find('.unit-label').after(removeBtn);
    return group;
  }

  // Add new ingredient group
  $('#add-ingredient-btn').on('click', function() {
    const group = createIngredientGroup(ingredientCount++);
    $('#ingredients-search-container').append(group);

    group.find('select').select2({
      placeholder: "-- Select ingredient --",
      allowClear: true,
      width: '200px'
    });
    moveSearchButton();
  });

  function getQueryParams() {
    const params = {};
    window.location.search.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(str,key,value) {
      key = decodeURIComponent(key.replace(/\[\]$/, ''));
      value = decodeURIComponent(value);
      if (!params[key]) params[key] = [];
      params[key].push(value);
    });
    return params;
  }

  const params = getQueryParams();
  const ingredients = params['ingredient'] || [];
  const servings = params['servings'] || [];
  console.log("User search input:");
  for (let i = 0; i < ingredients.length; i++) {
    if (ingredients[i]) {
      console.log(`Ingredient: ${ingredients[i]}, Amount: ${servings[i] || "(none)"}`);
    }
  }
  const hasSearch = ingredients.some(i => i && i.trim() !== "");


  if (ingredients.length > 0) {
    $('#ingredients-search-container').empty();
    for (let i = 0; i < ingredients.length; i++) {
      const group = createIngredientGroup(i);
      $('#ingredients-search-container').append(group);

      const $select = group.find('select');
      $select.select2({
        placeholder: "-- Select ingredient --",
        allowClear: true,
        width: '200px'
      });

      setTimeout(() => {
        $select.val(ingredients[i]);
        $select.trigger('change');
        $select.trigger({
          type: 'select2:select',
          params: {
            data: { id: ingredients[i], text: ingredients[i] }
          }
        });
      }, 50);

      if (params['servings'] && params['servings'][i]) group.find('input[type=number]').val(params['servings'][i]);
    }
    ingredientCount = ingredients.length;
    moveSearchButton();
  } else {
    const firstGroup = $('#ingredients-search-container .ingredient-search-item').first();
    firstGroup.find('select').select2({
      placeholder: "-- Select ingredient --",
      allowClear: true,
      width: '200px'
    });
    firstGroup.find('select').on('change', function() {
      const selected = $(this).val();
      const unit = ingredientUnits[selected] || '';
      firstGroup.find('.unit-label').text(unit ? '(' + unit + ')' : '');
    });
    moveSearchButton();
  }

  if (hasSearch && typeof recipeMissingAmounts !== 'undefined') {
    Object.keys(recipeMissingAmounts).forEach(function(recipeId) {
      var missingList = recipeMissingAmounts[recipeId];
      if (missingList.length > 0) {
        console.log('Recipe', recipeId, 'missing:', missingList.join(', '));
      }
    });
  }
}); 