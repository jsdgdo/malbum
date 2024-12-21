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