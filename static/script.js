// Navigation variables at the top of the file
let currentImageIndex = 0;
let allImageElements = [];

// Modified openModal function
function openModal(imgElement) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    
    // Store all image elements if not already stored
    if (allImageElements.length === 0) {
        allImageElements = Array.from(document.querySelectorAll('.thumbnail'));
    }
    
    // Find current index
    currentImageIndex = allImageElements.indexOf(imgElement);
    
    modal.style.display = "block";
    modalImg.src = imgElement.src.replace('/thumbnails', '');
    
    // Update button states
    updateButtonStates();
}

// Navigation functions
function showNextImage() {
    if (currentImageIndex < allImageElements.length - 1) {
        currentImageIndex++;
        const imgElement = allImageElements[currentImageIndex];
        document.getElementById('modalImage').src = imgElement.src.replace('/thumbnails', '');
        updateButtonStates();
    }
}

function showPrevImage() {
    if (currentImageIndex > 0) {
        currentImageIndex--;
        const imgElement = allImageElements[currentImageIndex];
        document.getElementById('modalImage').src = imgElement.src.replace('/thumbnails', '');
        updateButtonStates();
    }
}

function updateButtonStates() {
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    
    prevButton.disabled = currentImageIndex <= 0;
    nextButton.disabled = currentImageIndex >= allImageElements.length - 1;
}

// Update the thumbnail click handler
document.querySelectorAll('.thumbnail').forEach(thumbnail => {
    thumbnail.addEventListener('click', function() {
        openModal(this); // Pass the clicked image element
    });
});

// Add event listeners for navigation buttons
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('prevButton')?.addEventListener('click', showPrevImage);
    document.getElementById('nextButton')?.addEventListener('click', showNextImage);
    
    // Keyboard navigation
    document.addEventListener('keydown', function(event) {
        const modal = document.getElementById('imageModal');
        if (modal.style.display === "block") {
            if (event.key === 'ArrowLeft') {
                showPrevImage();
            } else if (event.key === 'ArrowRight') {
                showNextImage();
            }
        }
    });
});
