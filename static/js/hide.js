// Function to get cookie value
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to set cookie
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

// Function to hide/show post
function hidePost(postId) {
    const element = document.querySelector(`.toHide[data-post-id="${postId}"]`);
    const button = element.querySelector('.hide-button');
    
    if (!element) return;

    // Get current hidden posts from cookie
    let hiddenPosts = getCookie('hiddenPosts');
    hiddenPosts = hiddenPosts ? JSON.parse(hiddenPosts) : [];

    if (element.classList.contains('hidden')) {
        // Show the post
        element.classList.remove('hidden');
        button.textContent = 'Ocultar';
        // Remove from hidden posts
        hiddenPosts = hiddenPosts.filter(id => id !== postId);
    } else {
        // Hide the post
        element.classList.add('hidden');
        button.textContent = 'Mostrar';
        // Add to hidden posts if not already there
        if (!hiddenPosts.includes(postId)) {
            hiddenPosts.push(postId);
        }
    }

    // Save updated hidden posts to cookie
    setCookie('hiddenPosts', JSON.stringify(hiddenPosts), 30); // Store for 30 days
}

// Apply hidden state on page load
document.addEventListener('DOMContentLoaded', function() {
    const hiddenPosts = getCookie('hiddenPosts');
    if (hiddenPosts) {
        const hiddenPostIds = JSON.parse(hiddenPosts);
        hiddenPostIds.forEach(postId => {
            const element = document.querySelector(`.toHide[data-post-id="${postId}"]`);
            if (element) {
                element.classList.add('hidden');
                const button = element.querySelector('.hide-button');
                if (button) {
                    button.textContent = 'Mostrar';
                }
            }
        });
    }

    // Handle content warning toggles separately
    const toggleButtons = document.querySelectorAll('#toggle-blur');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const overlay = this.closest('.blur-overlay');
            if (overlay) {
                overlay.classList.toggle('active');
                this.textContent = overlay.classList.contains('active') 
                    ? 'Mostrar contenido' 
                    : 'Ocultar contenido';
            }
        });
    });
});

function getHiddenPhotos() {
  const hiddenPhotos = document.cookie
    .split('; ')
    .find(row => row.startsWith('hidden_photos='))
    ?.split('=')[1];
  return hiddenPhotos ? JSON.parse(decodeURIComponent(hiddenPhotos)) : [];
}

function setHiddenPhotos(hiddenPhotos) {
  document.cookie = `hidden_photos=${encodeURIComponent(JSON.stringify(hiddenPhotos))}; path=/`;
}

function toggleHidden(photoId) {
  const hiddenPhotos = getHiddenPhotos();

  if (hiddenPhotos.includes(photoId)) {
    const index = hiddenPhotos.indexOf(photoId);
    hiddenPhotos.splice(index, 1);
  } else {
    hiddenPhotos.push(photoId);
  }

  setHiddenPhotos(hiddenPhotos);
  applyHiddenState();
}

function applyHiddenState() {
  const hiddenPhotos = getHiddenPhotos();

  document.querySelectorAll('.toHide').forEach(container => {
    const photoId = container.dataset.photoId;

    if (hiddenPhotos.includes(photoId)) {
      container.classList.add('blurred');
      container.querySelector('.hide-button').innerText = 'Mostrar';
    } else {
      container.classList.remove('blurred');
      container.querySelector('.hide-button').innerText = 'Ocultar';
    }
  });
}

// Apply the hidden state when the DOM is loaded
document.addEventListener('DOMContentLoaded', applyHiddenState);

// Also apply the hidden state when the page becomes visible again
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') {
    applyHiddenState();
  }
});

function followUser(username, domain, actorUrl) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const button = document.querySelector(`button[data-action="follow"][onclick*="${username}"]`);
    const spinner = button.querySelector('.spinner-border');
    const buttonText = button.querySelector('.button-text');
    
    // Disable button and show spinner
    button.disabled = true;
    spinner.classList.remove('d-none');
    buttonText.textContent = 'Siguiendo...';
    
    fetch(`/usuario/${username}@${domain}/follow/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'actor_url': actorUrl,
            'remote_username': username,
            'remote_domain': domain
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            // Reset button state
            button.disabled = false;
            spinner.classList.add('d-none');
            buttonText.textContent = 'Seguir';
            alert(data.error || 'Error al seguir al usuario');
        }
    })
    .catch(error => {
        // Reset button state
        button.disabled = false;
        spinner.classList.add('d-none');
        buttonText.textContent = 'Seguir';
        console.error('Error:', error);
        alert('Error al procesar la solicitud');
    });
}

function unfollowUser(username, domain) {
    if (confirm('¿Estás seguro de que quieres dejar de seguir a este usuario?')) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const button = document.querySelector(`button[data-action="unfollow"][onclick*="${username}"]`);
        const spinner = button.querySelector('.spinner-border');
        const buttonText = button.querySelector('.button-text');
        
        // Disable button and show spinner
        button.disabled = true;
        spinner.classList.remove('d-none');
        buttonText.textContent = 'Dejando de seguir...';
        
        fetch(`/usuario/${username}@${domain}/unfollow/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                // Reset button state
                button.disabled = false;
                spinner.classList.add('d-none');
                buttonText.textContent = 'Dejar de seguir';
                alert(data.error || 'Error al dejar de seguir al usuario');
            }
        })
        .catch(error => {
            // Reset button state
            button.disabled = false;
            spinner.classList.add('d-none');
            buttonText.textContent = 'Dejar de seguir';
            console.error('Error:', error);
            alert('Error al procesar la solicitud');
        });
    }
}