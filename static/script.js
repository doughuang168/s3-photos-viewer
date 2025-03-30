// Global variables
let currentImageIndex = 0;
let allFileUrls = [];
// Global variable to track rotation per image
let imageRotations = new Map();

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
    
});

// Modal functions
//
function openModal(imageUrl) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    
    // Reset to saved rotation state or 0
    const rotation = imageRotations.get(imageUrl) || 0;
    modalImg.style.transform = `rotate(${rotation}deg)`;
    modalImg.dataset.rotation = rotation.toString();
    modalImg.dataset.currentImage = imageUrl; // Track current image
    
    modal.style.display = "block";
    modalImg.src = imageUrl;
    updateButtonStates();
}

function rotateImage() {
    const modalImg = document.getElementById('modalImage');
    const currentImage = modalImg.dataset.currentImage;
    const currentRotation = parseInt(modalImg.dataset.rotation || '0');
    const newRotation = (currentRotation + 90) % 360;
    
    // Update both display and stored rotation
    modalImg.style.transform = `rotate(${newRotation}deg)`;
    modalImg.dataset.rotation = newRotation.toString();
    imageRotations.set(currentImage, newRotation);
	
    // Show temporary indicator
    const indicator = document.createElement('div');
    indicator.className = 'rotation-indicator';
    indicator.textContent = `Rotated ${newRotation}°`;
    document.getElementById('imageModal').appendChild(indicator);
    
    setTimeout(() => {
        indicator.style.display = 'block';
        setTimeout(() => {
            indicator.style.opacity = '0';
            setTimeout(() => indicator.remove(), 300);
        }, 1000);
    }, 10);
    //
}

function closeModal() {
    document.getElementById('imageModal').style.display = "none";
}

// Navigation functions
//
// Update navigation functions to preserve rotation
function showNextImage() {
    const modalImg = document.getElementById('modalImage');
    const currentImage = modalImg.dataset.currentImage;
    const currentRotation = imageRotations.get(currentImage) || 0;
    
    if (currentImageIndex < allFileUrls.length - 1) {
        currentImageIndex++;
        const nextImage = `/view/${allFileUrls[currentImageIndex]}`;
        
        // Preserve rotation if image was viewed before
        const nextRotation = imageRotations.get(nextImage) || 0;
        modalImg.style.transform = `rotate(${nextRotation}deg)`;
        modalImg.dataset.rotation = nextRotation.toString();
        modalImg.dataset.currentImage = nextImage;
        
        modalImg.src = nextImage;
        updateButtonStates();
    }
}

function showPrevImage() {
    const modalImg = document.getElementById('modalImage');
    const currentImage = modalImg.dataset.currentImage;
    const currentRotation = imageRotations.get(currentImage) || 0;

    if (currentImageIndex > 0) {
        currentImageIndex--;
        const prevImage = `/view/${allFileUrls[currentImageIndex]}`;

        // Preserve rotation if image was viewed before
        const prevRotation = imageRotations.get(prevImage) || 0;
        modalImg.style.transform = `rotate(${prevRotation}deg)`;
        modalImg.dataset.rotation = prevRotation.toString();
        modalImg.dataset.currentImage = prevImage;

        modalImg.src = prevImage;
        updateButtonStates();
    }
}
//
// Original implementation
function updateModalImage() {
    const modalImg = document.getElementById('modalImage');
    modalImg.src = `/view/${allFileUrls[currentImageIndex]}`;
    updateButtonStates();
}

function updateButtonStates() {
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    
    prevButton.disabled = currentImageIndex <= 0;
    nextButton.disabled = currentImageIndex >= allFileUrls.length - 1;
}
