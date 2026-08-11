// Main JavaScript for SecureEscrow Kenya
(function() {
    'use strict';
    
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        initMobileNav();
        initDropdowns();
        initMessages();
        highlightActiveLink();
    });
    
    // Initialize Mobile Navigation
    function initMobileNav() {
        const navToggle = document.getElementById('navToggle');
        const navMenu = document.getElementById('navMenu');
        
        if (!navToggle || !navMenu) return;
        
        // Toggle menu on hamburger click
        navToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
            navToggle.setAttribute('aria-expanded', navMenu.classList.contains('active'));
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (navMenu.classList.contains('active') && 
                !navMenu.contains(event.target) && 
                !navToggle.contains(event.target)) {
                closeMobileMenu();
            }
        });
        
        // Close menu when pressing Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && navMenu.classList.contains('active')) {
                closeMobileMenu();
            }
        });
        
        // Close menu when clicking a navigation link on mobile
        const navLinks = navMenu.querySelectorAll('.nav-link:not(.dropdown-toggle)');
        navLinks.forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    closeMobileMenu();
                }
            });
        });
        
        function closeMobileMenu() {
            navMenu.classList.remove('active');
            navToggle.classList.remove('active');
            navToggle.setAttribute('aria-expanded', 'false');
            
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
                if (window.innerWidth <= 768) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const dropdown = this.closest('.nav-dropdown');
                    if (!dropdown) return;
                    
                    const allDropdowns = document.querySelectorAll('.nav-dropdown.active');
                    allDropdowns.forEach(function(activeDropdown) {
                        if (activeDropdown !== dropdown) {
                            activeDropdown.classList.remove('active');
                        }
                    });
                    
                    dropdown.classList.toggle('active');
                }
            });
        });
    }
    
    // Initialize Messages
    function initMessages() {
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
                link.classList.add('active-link');
            }
        });
    }
    
    // Handle window resize - reset mobile menu on desktop
    window.addEventListener('resize', function() {
        const navMenu = document.getElementById('navMenu');
        const navToggle = document.getElementById('navToggle');
        
        if (window.innerWidth > 768 && navMenu && navToggle) {
            if (navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            }
            
            const openDropdowns = document.querySelectorAll('.nav-dropdown.active');
            openDropdowns.forEach(function(dropdown) {
                dropdown.classList.remove('active');
            });
        }
    });
    
})();