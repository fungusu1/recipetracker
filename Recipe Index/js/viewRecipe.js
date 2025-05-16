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

  // Hide review form if current user is the author
  if (recipe.current_user_id && recipe.author && recipe.current_user_id === recipe.author.id) {
    const reviewFormContainer = document.querySelector('.review-form-container');
    if (reviewFormContainer) reviewFormContainer.style.display = 'none';
  }

  // Hide edit button if not the owner
  const editBtn = document.getElementById('editRecipeBtn');
  if (!recipe.current_user_id || !recipe.author || recipe.current_user_id !== recipe.author.id) {
    if (editBtn) editBtn.style.display = 'none';
  } else {
    if (editBtn) editBtn.style.display = '';
  }
  
  document.title = recipe.title;
  document.getElementById('title').textContent = recipe.title;
  document.getElementById('description').textContent = recipe.description;
  document.getElementById('cookTime').textContent = recipe.cook_time;
  document.getElementById('servings').textContent = recipe.servings;

  // Author and Views Row
  const authorViewsRow = document.getElementById('authorViewsRow');
  authorViewsRow.innerHTML = '';

  if (recipe.author) {
    // Create author link
    const authorLink = document.createElement('a');
    authorLink.href = `/profile/${recipe.author.id}`;
    authorLink.className = 'author-link';

    // Profile picture
    const authorPic = document.createElement('img');
    authorPic.src = recipe.author.profile_pic_url || '/images/profile_placeholder.jpg';
    authorPic.alt = `${recipe.author.name}'s profile picture`;
    authorPic.className = 'author-pic';

    // Author name
    const authorName = document.createElement('span');
    authorName.textContent = recipe.author.name;

    authorLink.appendChild(authorPic);
    authorLink.appendChild(authorName);

    const authorLabel = document.createElement('span');
    authorLabel.textContent = 'Author:';
    authorLabel.className = 'author-label';
    authorViewsRow.appendChild(authorLabel);
    authorViewsRow.appendChild(authorLink);
  }

  // Separator and views
  const separator = document.createElement('span');
  separator.textContent = '||';
  separator.className = 'separator';
  authorViewsRow.appendChild(separator);

  const viewsSpan = document.createElement('span');
  viewsSpan.className = 'views-label';
  viewsSpan.textContent = `Views: ${recipe.view_count}`;
  authorViewsRow.appendChild(viewsSpan);

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
  reviewsContainer.innerHTML = '';
  let reviewsToShow = recipe.reviews || [];
  // Sort reviews by created_at descending (latest first)
  reviewsToShow.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  let showingAll = false;
  function renderReviews(limit = 3) {
    reviewsContainer.innerHTML = '';
    const reviews = showingAll ? reviewsToShow : reviewsToShow.slice(0, limit);
    if (reviews.length > 0) {
      reviews.forEach(review => {
        const reviewDiv = document.createElement('div');
        reviewDiv.className = 'review';
        // Header: profile pic, username, date
        const headerDiv = document.createElement('div');
        headerDiv.className = 'review-header';
        const userLink = document.createElement('a');
        userLink.href = `/profile?id=${review.user.id}`;
        userLink.className = 'review-user-link';
        const userPic = document.createElement('img');
        userPic.src = review.user.profile_pic_url || '/images/profile_placeholder.jpg';
        userPic.alt = `${review.user.display_name}'s profile picture`;
        userPic.className = 'review-user-pic';
        const userName = document.createElement('span');
        userName.textContent = review.user.display_name;
        userName.className = 'review-username';
        userLink.appendChild(userPic);
        userLink.appendChild(userName);
        const sep = document.createElement('span');
        sep.textContent = ' || ';
        sep.className = 'review-separator';
        const dateSpan = document.createElement('span');
        dateSpan.textContent = review.created_at;
        dateSpan.className = 'review-date';
        headerDiv.appendChild(userLink);
        headerDiv.appendChild(sep);
        headerDiv.appendChild(dateSpan);
        // Stars
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
        const headerStarsRow = document.createElement('div');
        headerStarsRow.className = 'review-header-stars-row';
        headerStarsRow.appendChild(headerDiv);
        headerStarsRow.appendChild(starsDiv);
        // Comment
        const commentP = document.createElement('p');
        commentP.textContent = review.comment;
        reviewDiv.appendChild(headerStarsRow);
        reviewDiv.appendChild(commentP);
        reviewsContainer.appendChild(reviewDiv);
      });
      if (!showingAll && reviewsToShow.length > 3) {
        const showMoreBtn = document.createElement('button');
        showMoreBtn.textContent = 'Show More';
        showMoreBtn.className = 'print-button review-post-btn';
        showMoreBtn.style.marginTop = '10px';
        showMoreBtn.onclick = function() {
          showingAll = true;
          renderReviews();
        };
        reviewsContainer.appendChild(showMoreBtn);
      }
    } else {
      reviewsContainer.innerHTML = '<p>No reviews yet.</p>';
    }
  }
  renderReviews();
}

// Get recipe ID from URL
(async () => {
  const recipeId = new URLSearchParams(window.location.search).get('id');
  const recipe = await getRecipeById(recipeId);
  displayRecipe(recipe);
})();

// Review Form Stars Logic
const reviewStarsDiv = document.getElementById('reviewStars');
let selectedRating = 0;

function renderReviewStars() {
  reviewStarsDiv.innerHTML = '';
  for (let i = 1; i <= 5; i++) {
    const star = document.createElement('span');
    star.className = 'review-star' + (i <= selectedRating ? ' filled' : '');
    star.textContent = '★';
    star.dataset.value = i;
    star.addEventListener('click', () => {
      selectedRating = i;
      renderReviewStars();
    });
    reviewStarsDiv.appendChild(star);
  }
}
renderReviewStars();

// Limit textarea to fit the box visually
const reviewText = document.getElementById('reviewText');
reviewText.addEventListener('input', function() {
  if (this.value.length > 500) {
    this.value = this.value.slice(0, 500);
  }
});

// Post Button (no backend yet)
document.getElementById('postReviewBtn').addEventListener('click', async function() {
  if (selectedRating === 0) {
    showFlashMessage('Please select a star rating.', 'error');
    return;
  }
  if (!reviewText.value.trim()) {
    showFlashMessage('Please write a review.', 'error');
    return;
  }

  const recipeId = new URLSearchParams(window.location.search).get('id');
  const response = await fetch(`/api/recipes/${recipeId}/reviews`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      rating: selectedRating,
      comment: reviewText.value.trim()
    })
  });

  if (!response.ok) {
    const data = await response.json();
    showFlashMessage(data.error || 'Failed to post review.', 'error');
    return;
  }

  const newReview = await response.json();
  window.location.reload();
});

function showFlashMessage(msg, type = 'error') {
  let flash = document.getElementById('flash-message');
  if (!flash) {
    flash = document.createElement('div');
    flash.id = 'flash-message';
    document.body.prepend(flash);
  }
  flash.textContent = msg;
  flash.className = 'flash-message ' + type;
  flash.style.display = 'block';
  setTimeout(() => { flash.style.display = 'none'; }, 3500);
}
