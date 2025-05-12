async function getRecipeById(id) {
  try {
    const response = await fetch(`/api/recipes/${id}`);
    if (!response.ok) {
      throw new Error('Recipe not found');
    }
    return await response.json();
  } catch (error) {
    console.error(error);
    return null;
  }
}

function displayRecipe(recipe) {
  if (!recipe) {
    document.body.innerHTML = "<h2>Recipe not found.</h2>";
    return;
  }

  document.title = recipe.title;
  document.getElementById('title').textContent = recipe.title;
  document.getElementById('description').textContent = recipe.description;
  document.getElementById('cookTime').textContent = recipe.cook_time;
  document.getElementById('servings').textContent = recipe.servings;
  document.getElementById('privacy').textContent = recipe.privacy;

  // Ingredients
  const ingList = document.getElementById('ingredients');
  recipe.ingredients.forEach(ing => {
    const li = document.createElement('li');
    li.textContent = ing;
    ingList.appendChild(li);
  });

  // Instructions
  const instList = document.getElementById('instructions');
  recipe.instructions.forEach(step => {
    const li = document.createElement('li');
    li.textContent = step;
    instList.appendChild(li);
  });

  // Image
  if (recipe.image_url) {
    const img = document.createElement('img');
    img.src = recipe.image_url;
    img.alt = "Recipe Image";
    img.className = "recipe-image";
    document.getElementById('imageContainer').appendChild(img);
  }

  // Reviews
  const reviewsContainer = document.getElementById('reviewsContainer');
  if (recipe.reviews && recipe.reviews.length > 0) {
    recipe.reviews.forEach(review => {
      const reviewDiv = document.createElement('div');
      reviewDiv.className = 'review';

      const starsDiv = document.createElement('div');
      starsDiv.className = 'stars';

      for (let i = 0; i < review.rating; i++) {
        const star = document.createElement('span');
        star.className = 'star';
        star.textContent = '★';
        starsDiv.appendChild(star);
      }

      for (let i = 0; i < 5 - review.rating; i++) {
        const star = document.createElement('span');
        star.className = 'star';
        star.style.color = '#ccc';
        star.textContent = '★';
        starsDiv.appendChild(star);
      }

      const commentP = document.createElement('p');
      commentP.textContent = review.comment;

      reviewDiv.appendChild(starsDiv);
      reviewDiv.appendChild(commentP);
      reviewsContainer.appendChild(reviewDiv);
    });
  } else {
    reviewsContainer.innerHTML = '<p>No reviews yet.</p>';
  }
}

// Get recipe ID from URL
const urlParams = new URLSearchParams(window.location.search);
const recipeId = urlParams.get('id');
const recipe = getRecipeById(recipeId);
displayRecipe(recipe);
