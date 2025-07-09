// Mobile and tablet optimizations for MyStorage app

document.addEventListener('DOMContentLoaded', function() {
    // Check if it's a touch device
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    if (isTouchDevice) {
        document.body.classList.add('touch-device');
        
        // Add active state for touch feedback on buttons
        const buttons = document.querySelectorAll('button, .download-btn');
        buttons.forEach(button => {
            button.addEventListener('touchstart', function() {
                this.classList.add('active-touch');
            });
            button.addEventListener('touchend', function() {
                this.classList.remove('active-touch');
            });
        });
    }
    
    // Detect orientation changes and adjust UI accordingly
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            adjustUIForOrientation();
        }, 100);
    });
    
    // Initial orientation check
    adjustUIForOrientation();
    
    // Improve scrolling performance on mobile
    let ticking = false;
    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                // Optimize animations during scroll
                ticking = false;
            });
            ticking = true;
        }
    });
    
    // Fix viewport issues on mobile
    fixViewportHeight();
    window.addEventListener('resize', fixViewportHeight);
});

// Adjust UI elements based on screen orientation
function adjustUIForOrientation() {
    const isLandscape = window.innerWidth > window.innerHeight;
    
    if (isLandscape && window.innerHeight < 500) {
        // Compact mode for landscape on small devices
        document.body.classList.add('landscape-compact');
    } else {
        document.body.classList.remove('landscape-compact');
    }
}

// Fix the "100vh" issue on mobile browsers
function fixViewportHeight() {
    // Use the actual viewport height instead of 100vh
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
}
