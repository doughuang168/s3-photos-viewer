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

    ///////////
    // Initialize Intersection Observer
    const lazyLoadObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.onload = () => {
                        img.classList.add('loaded');
                        img.removeAttribute('data-src');
                    };
                    observer.unobserve(img);
                }
            }
        });
    }, {
        rootMargin: '200px', // Load slightly before entering viewport
        threshold: 0.01
    });

    // Observe all lazy-load images
    document.querySelectorAll('.lazy-load').forEach(img => {
        lazyLoadObserver.observe(img);
    });

    // Preload first 6 images immediately
    document.querySelectorAll('.lazy-load:nth-child(-n+6)').forEach(img => {
        img.src = img.dataset.src;
        img.classList.add('loaded');
        img.removeAttribute('data-src');
    });
    ///////////
});

// Modal functions
function openModal(imageUrl) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    
    // Reset all transformations, following extra 2 lines address Rotation State Persistence issue
    modalImg.style.transform = 'rotate(0deg)';
    modalImg.dataset.rotation = '0'; // Store rotation state in dataset
    //

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
