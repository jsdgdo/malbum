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

  document.querySelectorAll('.card').forEach(container => {
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

function unfollow(username, domain) {
    if (confirm('¿Estás seguro de que quieres dejar de seguir a este usuario?')) {
        fetch('/usuario/unfollow/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `username=${username}&domain=${domain}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al dejar de seguir: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al dejar de seguir');
        });
    }
}