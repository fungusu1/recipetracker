function addField(containerId, inputName) {
    const container = document.getElementById(containerId);
    const wrapper = document.createElement('div');
    wrapper.className = "ingredient-item";
  
    const index = container.childElementCount + 1;
  
    const label = document.createElement('div');
    label.className = "item-label";
    label.innerText = index + '.';
  
    const input = document.createElement('textarea');
    input.rows = 1;
    input.name = inputName;
    input.required = true;
    input.maxLength = 200;
    input.className = "textarea-wrapper";
  
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.innerText = '✕';
    removeBtn.className = "remove-btn hidden";
  
    input.addEventListener('focus', () => {
      if (container.childElementCount > 1) {
        removeBtn.classList.remove('hidden');
      }
    });
  
    input.addEventListener('blur', () => {
      setTimeout(() => {
        if (!wrapper.contains(document.activeElement)) {
          removeBtn.classList.add('hidden');
        }
      }, 100);
    });
  
    removeBtn.onclick = () => {
      if (container.childElementCount > 1) {
        container.removeChild(wrapper);
        updateNumbering(container);
      }
    };
  
    wrapper.appendChild(label);
    wrapper.appendChild(input);
    wrapper.appendChild(removeBtn);
    container.appendChild(wrapper);
  
    updateNumbering(container);
  }
  
  function updateNumbering(container) {
    Array.from(container.children).forEach((wrapper, index) => {
      const label = wrapper.querySelector('div');
      if (label) label.innerText = (index + 1) + '.';
    });
  }