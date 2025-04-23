const recipes_placeholder = [
    { title: "recipe 1", image: "../resources/profile_placeholder.jpg", rating: 0 },
    { title: "recipe 2", image: "../resources/profile_placeholder.jpg", rating: 0 },
    { title: "recipe 3", image: "../resources/profile_placeholder.jpg", rating: 0 },
    { title: "recipe 4", image: "../resources/profile_placeholder.jpg", rating: 0 },
    { title: "recipe 5", image: "../resources/profile_placeholder.jpg", rating: 0 },
    { title: "recipe 6", image: "../resources/profile_placeholder.jpg", rating: 0 },
    { title: "recipe 7", image: "../resources/profile_placeholder.jpg", rating: 0 },
    { title: "recipe 8", image: "../resources/profile_placeholder.jpg", rating: 0 },
    { title: "recipe 9", image: "../resources/profile_placeholder.jpg", rating: 0 }
]

const singleRowAmount = 4;
let expanded = false;
const createdCards = [];    

// Recipe card rendering
function makeCard(recipe) {
    const card = document.createElement('div');
    card.className = 'recipe-card';

    const img = document.createElement('img');
    img.src = recipe.image;
    img.alt = recipe.title;

    const title = document.createElement('h3');
    title.textContent = recipe.title;

    const rating = document.createElement('div');
    rating.className = 'recipe-rating';
    rating.textContent = `Rating: ${recipe.rating} / 5`;

    card.appendChild(img);
    card.appendChild(title);
    card.appendChild(rating);

    return card;

}

function renderInitial() {
    const recipeGrid = document.getElementById("recipeGrid");

    for (let i = 0; i < singleRowAmount; i++) {
        const card = makeCard(recipes_placeholder[i]);
        recipeGrid.appendChild(card);
        createdCards.push(card);
    }
}

function expandHandler() {
    expanded = !expanded;
    const btn = document.getElementById("expandBtn");
    const recipeGrid = document.getElementById("recipeGrid");

    btn.textContent = expanded ? "Show Less" : "Expand";
    if (expanded) {
        for (let i = singleRowAmount; i < recipes_placeholder.length; i++) {
            if (!createdCards[i]) {
                const card = makeCard(recipes_placeholder[i]);
                createdCards[i] = card;
                recipeGrid.appendChild(card);
            } else {
                createdCards[i].style.display = '';
            }
        }
    } else {
        for (let i = singleRowAmount; i < createdCards.length; i++) {
            if (createdCards[i]) {
                createdCards[i].style.display = 'none';
            }
        }
    }
}

document.getElementById("expandBtn").addEventListener('click', expandHandler);

// Initial load
renderInitial()