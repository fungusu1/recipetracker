$(document).ready(function() {
  let ingredientCount = $('#ingredients-search-container .ingredient-search-item').length;

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

  function initializeAllSelect2() {
    $('#ingredients-search-container select').each(function() {
      $(this).select2({
        placeholder: "-- Select ingredient --",
        allowClear: true,
        width: '200px'
      });
    });
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
      updateIngredientOptions();
    });
    const removeBtn = $('<button type="button" class="remove-ingredient-btn">✕</button>');
    removeBtn.on('click', function() {
      if ($('#ingredients-search-container .ingredient-search-item').length > 1) {
        group.remove();
        moveSearchButton();
      } else {
        group.find('select').val('').trigger('change');
        group.find('input[type=number]').val('');
        group.find('.unit-label').text('');
      }
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
    }).on('change', function() {
      updateIngredientOptions();
    });
    moveSearchButton();
    updateIngredientOptions();
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

  function attachRemoveHandlers() {
    $('.remove-ingredient-btn').off('click').on('click', function() {
      const group = $(this).closest('.ingredient-search-item');
      // Only remove if it's not the first row
      if (group.index() > 0) {
        group.remove();
        moveSearchButton();
      }
    });
  }

  $('#ingredients-search-container select').each(function() {
    $(this).select2({
      placeholder: "-- Select ingredient --",
      allowClear: true,
      width: '200px'
    }).on('change', function() {
      updateIngredientOptions();
    });
  });
  updateIngredientOptions();
  attachRemoveHandlers();
  moveSearchButton();

  if (hasSearch && typeof recipeMissingAmounts !== 'undefined') {
    Object.keys(recipeMissingAmounts).forEach(function(recipeId) {
      var missingList = recipeMissingAmounts[recipeId];
      if (missingList.length > 0) {
        console.log('Recipe', recipeId, 'missing:', missingList.join(', '));
      }
    });
  }

  function updateIngredientOptions() {
    // Get all selected ingredient values (excluding empty)
    const selected = [];
    $('#ingredients-search-container select').each(function() {
      const val = $(this).val();
      if (val) selected.push(val);
    });

    $('#ingredients-search-container select').each(function() {
      const $select = $(this);
      const currentVal = $select.val();

      // For each option, disable if it's selected in another select
      $select.find('option').each(function() {
        const optionVal = $(this).val();
        if (
          optionVal &&
          optionVal !== currentVal &&
          selected.includes(optionVal)
        ) {
          $(this).attr('disabled', 'disabled');
        } else {
          $(this).removeAttr('disabled');
        }
      });

      // Refresh Select2
      $select.trigger('change.select2');
    });
  }
}); 
