// Global variables
let currentImageIndex = 0;
let allFileUrls = [];

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Get all files from hidden div
    const fileListData = document.getElementById('fileListData');
    if (fileListData) {
        allFileUrls = JSON.parse(fileListData.getAttribute('data-files')); //Original implementation
        //allFileUrls = allFileUrls.map(file => file.trim().replace(/^\/+/, '')); //URL Normalization:
    }

    // Set up click handlers for file links
    document.querySelectorAll('.file-link').forEach((link, index) => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            currentImageIndex = index; // Set correct starting index
            openModal(this.getAttribute('data-url'));
        });
    });

    // Navigation buttons
    document.getElementById('prevButton')?.addEventListener('click', showPrevImage);
    document.getElementById('nextButton')?.addEventListener('click', showNextImage);

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        const modal = document.getElementById('imageModal');
        if (modal.style.display === "block") {
            if (e.key === 'ArrowLeft') showPrevImage();
            if (e.key === 'ArrowRight') showNextImage();
        }
    });
});

// Modal functions
function openModal(imageUrl) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    
    modal.style.display = "block";
    modalImg.src = imageUrl;
    updateButtonStates();
}

function closeModal() {
    document.getElementById('imageModal').style.display = "none";
}

// Navigation functions
function showNextImage() {
    if (currentImageIndex < allFileUrls.length - 1) {
        currentImageIndex++;
        updateModalImage();
    }
}

function showPrevImage() {
    if (currentImageIndex > 0) {
        currentImageIndex--;
        updateModalImage();
    }
}

// Original implementation
function updateModalImage() {
    const modalImg = document.getElementById('modalImage');
    modalImg.src = `/view/${allFileUrls[currentImageIndex]}`;
    updateButtonStates();
}

//Additional Improvements Visual Feedback:
//function updateModalImage() {
//    const modalImg = document.getElementById('modalImage');
//    modalImg.style.opacity = 0; // Fade out
//    setTimeout(() => {
//        modalImg.src = `/view/${allFileUrls[currentImageIndex]}`;
//        modalImg.style.opacity = 1; // Fade in
//        updateButtonStates();
//    }, 200);
//}

function updateButtonStates() {
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    
    prevButton.disabled = currentImageIndex <= 0;
    nextButton.disabled = currentImageIndex >= allFileUrls.length - 1;
}
