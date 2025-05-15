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

  // Set page title and basic details
  document.title = recipe.title;
  document.getElementById('title').textContent = recipe.title;
  document.getElementById('description').textContent = recipe.description;
  document.getElementById('cookTime').textContent = recipe.cook_time;
  document.getElementById('servings').textContent = recipe.servings;
  document.getElementById('viewCount').textContent = recipe.views;

  // Author link
  const authorLink = document.getElementById('authorLink');
  authorLink.href = `/profile/${recipe.author_id}`;
  authorLink.textContent = recipe.author_name;

  // Privacy
  const privacyMap = { 0: "Private", 1: "Public", 2: "Shared" };
  document.getElementById('privacy').textContent = privacyMap[recipe.privacy] || "Unknown";

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

  // Image(s)
  const imageContainer = document.getElementById('imageContainer');
  if (Array.isArray(recipe.image_urls)) {
    recipe.image_urls.forEach(url => {
      const img = document.createElement('img');
      img.src = url;
      img.alt = "Recipe Image";
      img.className = "recipe-image";
      imageContainer.appendChild(img);
    });
  } else if (recipe.image_url) {
    const img = document.createElement('img');
    img.src = recipe.image_url;
    img.alt = "Recipe Image";
    img.className = "recipe-image";
    imageContainer.appendChild(img);
  }

  // Reviews
  const reviewsContainer = document.getElementById('reviewsContainer');
  if (recipe.reviews && recipe.reviews.length > 0) {
    recipe.reviews.forEach(review => {
      const reviewDiv = document.createElement('div');
      reviewDiv.className = 'review';

      // Star rating
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

      // Review meta
      const metaP = document.createElement('p');
      metaP.className = 'review-meta';
      metaP.textContent = `By ${review.username} on ${new Date(review.date).toLocaleDateString()}`;

      // Review comment
      const commentP = document.createElement('p');
      commentP.textContent = review.comment;

      reviewDiv.appendChild(starsDiv);
      reviewDiv.appendChild(metaP);
      reviewDiv.appendChild(commentP);
      reviewsContainer.appendChild(reviewDiv);
    });
  } else {
    reviewsContainer.innerHTML = '<p>No reviews yet.</p>';
  }

  // Show Edit button if user is owner
  if (recipe.is_owner) {
    const btn = document.getElementById('editBtn');
    btn.classList.remove('hidden');
    btn.onclick = () => location.href = `/edit?id=${recipe.id}`;
  }
}

// Get recipe ID from URL and display
(async () => {
  const recipeId = new URLSearchParams(window.location.search).get('id');
  const recipe = await getRecipeById(recipeId);
  displayRecipe(recipe);
})();
