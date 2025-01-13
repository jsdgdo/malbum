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

function followUser(username, isLocal) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const followBtn = document.querySelector(`[data-username="${username}"]`);
    
    if (!followBtn) {
        console.error('Follow button not found');
        return;
    }
    
    fetch(`/usuario/follow/${username}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update button text and state
            if (followBtn.textContent.trim() === 'Seguir') {
                followBtn.textContent = 'Dejar de seguir';
                followBtn.classList.remove('btn-primary');
                followBtn.classList.add('btn-secondary');
            } else {
                followBtn.textContent = 'Seguir';
                followBtn.classList.remove('btn-secondary');
                followBtn.classList.add('btn-primary');
            }
        } else {
            alert(data.error || 'Error al seguir/dejar de seguir al usuario');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al procesar la solicitud');
    });
}