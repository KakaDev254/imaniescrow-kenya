// Main JavaScript for SecureEscrow Kenya
(function() {
    'use strict';
    
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        
        // ===== Mobile Navigation Toggle =====
        initMobileNav();
        
        // ===== Mobile Dropdown Toggle =====
        initDropdowns();
        
        // ===== Close Messages =====
        initMessages();
        
        // ===== Active Link Highlighting =====
        highlightActiveLink();
        
    });
    
    // Initialize Mobile Navigation
    function initMobileNav() {
        const navToggle = document.getElementById('navToggle');
        const navMenu = document.getElementById('navMenu');
        
        // Check if elements exist
        if (!navToggle || !navMenu) {
            console.error('Navigation elements not found!');
            return;
        }
        
        console.log('Mobile nav initialized successfully');
        
        // Toggle menu on hamburger click
        navToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('Hamburger clicked!');
            
            // Toggle menu visibility
            navMenu.classList.toggle('active');
            
            // Toggle hamburger animation
            navToggle.classList.toggle('active');
            
            // Update accessibility attribute
            const isExpanded = navMenu.classList.contains('active');
            navToggle.setAttribute('aria-expanded', isExpanded);
            
            console.log('Menu is now:', isExpanded ? 'open' : 'closed');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (navMenu.classList.contains('active')) {
                const isClickInsideMenu = navMenu.contains(event.target);
                const isClickOnToggle = navToggle.contains(event.target);
                
                if (!isClickInsideMenu && !isClickOnToggle) {
                    console.log('Clicked outside, closing menu');
                    closeMobileMenu();
                }
            }
        });
        
        // Close menu when pressing Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && navMenu.classList.contains('active')) {
                console.log('Escape pressed, closing menu');
                closeMobileMenu();
            }
        });
        
        // Close menu when clicking a navigation link (only on mobile)
        const navLinks = navMenu.querySelectorAll('.nav-link:not(.dropdown-toggle)');
        navLinks.forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    console.log('Nav link clicked on mobile, closing menu');
                    closeMobileMenu();
                }
            });
        });
        
        // Function to close mobile menu
        function closeMobileMenu() {
            navMenu.classList.remove('active');
            navToggle.classList.remove('active');
            navToggle.setAttribute('aria-expanded', 'false');
            
            // Also close any open dropdowns
            const openDropdowns = document.querySelectorAll('.nav-dropdown.active');
            openDropdowns.forEach(function(dropdown) {
                dropdown.classList.remove('active');
            });
        }
    }
    
    // Initialize Dropdown Menus
    function initDropdowns() {
        const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
        
        dropdownToggles.forEach(function(toggle) {
            toggle.addEventListener('click', function(e) {
                // Only handle differently on mobile
                if (window.innerWidth <= 768) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const dropdown = this.closest('.nav-dropdown');
                    
                    if (!dropdown) {
                        console.error('Dropdown parent not found!');
                        return;
                    }
                    
                    console.log('Dropdown toggled on mobile');
                    
                    // Close other dropdowns
                    const allDropdowns = document.querySelectorAll('.nav-dropdown.active');
                    allDropdowns.forEach(function(activeDropdown) {
                        if (activeDropdown !== dropdown) {
                            activeDropdown.classList.remove('active');
                        }
                    });
                    
                    // Toggle current dropdown
                    dropdown.classList.toggle('active');
                }
            });
        });
    }
    
    // Initialize Messages
    function initMessages() {
        // Close message buttons
        const messageCloseButtons = document.querySelectorAll('.message-close');
        messageCloseButtons.forEach(function(button) {
            button.addEventListener('click', function() {
                const message = this.closest('.message');
                if (message) {
                    message.style.opacity = '0';
                    message.style.transition = 'opacity 0.3s ease';
                    setTimeout(function() {
                        message.remove();
                    }, 300);
                }
            });
        });
        
        // Auto-hide messages after 5 seconds
        setTimeout(function() {
            const messages = document.querySelectorAll('.message');
            messages.forEach(function(message) {
                message.style.opacity = '0';
                message.style.transition = 'opacity 0.3s ease';
                setTimeout(function() {
                    message.remove();
                }, 300);
            });
        }, 5000);
    }
    
    // Highlight Active Navigation Link
    function highlightActiveLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(function(link) {
            const linkPath = link.getAttribute('href');
            if (linkPath === currentPath) {
                link.classList.add('active-link');
            } else if (currentPath.startsWith(linkPath) && linkPath !== '/') {
                // Handle nested paths
                link.classList.add('active-link');
            }
        });
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        const navMenu = document.getElementById('navMenu');
        const navToggle = document.getElementById('navToggle');
        
        if (window.innerWidth > 768 && navMenu && navToggle) {
            // Reset mobile menu state when resizing to desktop
            if (navMenu.classList.contains('active')) {
                console.log('Resized to desktop, closing mobile menu');
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            }
            
            // Close all mobile dropdowns
            const openDropdowns = document.querySelectorAll('.nav-dropdown.active');
            openDropdowns.forEach(function(dropdown) {
                dropdown.classList.remove('active');
            });
        }
    });
    
})();

// ===== Utility Functions (Global Scope) =====

// Toggle mobile menu (can be called from HTML onclick)
function toggleMobileMenu() {
    const navMenu = document.getElementById('navMenu');
    const navToggle = document.getElementById('navToggle');
    
    if (navMenu && navToggle) {
        console.log('Toggle mobile menu called from onclick');
        navMenu.classList.toggle('active');
        navToggle.classList.toggle('active');
        
        const isExpanded = navMenu.classList.contains('active');
        navToggle.setAttribute('aria-expanded', isExpanded);
    } else {
        console.error('Cannot toggle menu - elements not found');
    }
}

// Toggle dropdown on mobile (can be called from HTML onclick)
function toggleDropdown(event) {
    if (window.innerWidth <= 768) {
        event.preventDefault();
        event.stopPropagation();
        
        const dropdown = event.target.closest('.nav-dropdown');
        
        if (dropdown) {
            console.log('Toggle dropdown called from onclick');
            
            // Close other dropdowns
            document.querySelectorAll('.nav-dropdown.active').forEach(function(activeDropdown) {
                if (activeDropdown !== dropdown) {
                    activeDropdown.classList.remove('active');
                }
            });
            
            // Toggle current dropdown
            dropdown.classList.toggle('active');
        }
    }
}

// Close message (can be called from HTML onclick)
function closeMessage(button) {
    const message = button.closest('.message');
    if (message) {
        message.style.opacity = '0';
        message.style.transition = 'opacity 0.3s ease';
        setTimeout(function() {
            message.remove();
        }, 300);
    }
}

// Debug function - check if elements exist
function debugNav() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    console.log('=== Navigation Debug ===');
    console.log('Nav Toggle found:', !!navToggle);
    console.log('Nav Menu found:', !!navMenu);
    console.log('Window width:', window.innerWidth);
    console.log('Menu classes:', navMenu ? navMenu.classList.toString() : 'N/A');
    console.log('Toggle classes:', navToggle ? navToggle.classList.toString() : 'N/A');
    console.log('=======================');
    
    alert('Check browser console (F12) for debug info');
}

// Run debug on load
window.addEventListener('load', function() {
    console.log('Page fully loaded');
    debugNav();
});