/**
 * Shared Navigation Component for Marceau Solutions
 * Include this script in any page to add consistent navigation
 *
 * Usage:
 * 1. Add <link rel="stylesheet" href="nav-styles.css"> in <head>
 * 2. Add <script src="nav-component.js"></script> before </body>
 * 3. Add <div id="site-nav"></div> where you want the nav
 * 4. Add <div id="site-footer"></div> where you want the footer
 */

(function() {
    // Configuration - Update these URLs as needed
    const config = {
        baseUrl: 'https://marceausolutions.com',
        localBase: '', // Use relative paths for local dev
        pages: {
            home: '/',
            about: '/about.html',
            contact: '/contact.html',
            caseStudies: '/case-studies.html',
            terms: '/terms.html',
            privacy: '/privacy.html',
            fitness: '/setup_form.html',
            amazon: '/amazon-seller.html',
            medtech: '/medtech.html',
            interviewPrep: 'https://interview-prep-pptx-production.up.railway.app/app',
            allSolutions: '/solutions.html'
        }
    };

    // Detect if we're on a local file or deployed
    const isLocal = window.location.protocol === 'file:' || window.location.hostname === 'localhost';
    const base = isLocal ? config.localBase : config.baseUrl;

    // Navigation HTML
    const navHTML = `
    <nav class="site-nav">
        <div class="nav-container">
            <a href="${base}/" class="logo">
                <span class="logo-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 6v6l4 2"/>
                    </svg>
                </span>
                <span class="logo-text">Marceau Solutions</span>
            </a>

            <button class="mobile-toggle" onclick="toggleMobileMenu()">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            </button>

            <div class="nav-menu" id="navMenu">
                <a href="${base}/about.html" class="nav-link">About</a>

                <div class="dropdown">
                    <button class="dropdown-toggle" onclick="toggleDropdown(this)">
                        Industries
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </button>
                    <div class="dropdown-menu">
                        <a href="${base}/setup_form.html" class="dropdown-item">
                            <div class="dropdown-item-title">Fitness & Influencers</div>
                            <div class="dropdown-item-desc">AI tools for content creators and coaches</div>
                        </a>
                        <a href="${base}/amazon-seller.html" class="dropdown-item">
                            <div class="dropdown-item-title">Amazon Sellers</div>
                            <div class="dropdown-item-desc">Inventory and pricing optimization</div>
                        </a>
                        <a href="${base}/medtech.html" class="dropdown-item">
                            <div class="dropdown-item-title">MedTech & Device Companies</div>
                            <div class="dropdown-item-desc">Healthcare automation solutions</div>
                        </a>
                        <a href="https://interview-prep-pptx-production.up.railway.app/app" class="dropdown-item">
                            <div class="dropdown-item-title">Interview Prep</div>
                            <div class="dropdown-item-desc">AI-powered interview preparation assistant</div>
                        </a>
                        <div class="dropdown-divider"></div>
                        <a href="${base}/solutions.html" class="dropdown-item">
                            <div class="dropdown-item-title" style="color: #fbbf24;">All Solutions</div>
                            <div class="dropdown-item-desc">View all AI automation services</div>
                        </a>
                    </div>
                </div>

                <a href="${base}/contact.html" class="nav-link">Contact</a>
                <a href="${base}/case-studies.html" class="nav-link">Case Studies</a>

                <a href="${base}/setup_form.html" class="nav-cta">Get Started</a>
            </div>
        </div>
    </nav>
    `;

    // Footer HTML
    const footerHTML = `
    <footer class="site-footer">
        <div class="footer-container">
            <div class="footer-brand">
                <a href="${base}/" class="logo">
                    <span style="color: #fbbf24;">M</span> Marceau Solutions
                </a>
                <p>Custom AI automation built for your industry. Stop wasting time on repetitive tasks.</p>
            </div>

            <div class="footer-section">
                <h4>Solutions</h4>
                <a href="${base}/setup_form.html" class="footer-link">Fitness & Influencers</a>
                <a href="${base}/amazon-seller.html" class="footer-link">Amazon Sellers</a>
                <a href="${base}/medtech.html" class="footer-link">MedTech & Devices</a>
                <a href="https://interview-prep-pptx-production.up.railway.app/app" class="footer-link">Interview Prep</a>
            </div>

            <div class="footer-section">
                <h4>Company</h4>
                <a href="${base}/about.html" class="footer-link">About Us</a>
                <a href="${base}/case-studies.html" class="footer-link">Case Studies</a>
                <a href="${base}/contact.html" class="footer-link">Contact</a>
            </div>

            <div class="footer-section">
                <h4>Contact</h4>
                <a href="mailto:wmarceau@marceausolutions.com" class="footer-link">wmarceau@marceausolutions.com</a>
                <a href="tel:+18552399364" class="footer-link">+1 (855) 239-9364</a>
            </div>
        </div>

        <div class="footer-bottom">
            <p>&copy; ${new Date().getFullYear()} Marceau Solutions LLC. All rights reserved.</p>
            <div class="footer-legal">
                <a href="${base}/terms.html">Terms of Service</a>
                <a href="${base}/terms.html#privacy">Privacy Policy</a>
                <a href="${base}/terms.html#sms">SMS Terms</a>
            </div>
        </div>
    </footer>
    `;

    // Insert navigation
    function insertNav() {
        const navContainer = document.getElementById('site-nav');
        if (navContainer) {
            navContainer.innerHTML = navHTML;
        } else {
            // If no container, insert at the start of body
            document.body.insertAdjacentHTML('afterbegin', navHTML);
        }
    }

    // Insert footer
    function insertFooter() {
        const footerContainer = document.getElementById('site-footer');
        if (footerContainer) {
            footerContainer.innerHTML = footerHTML;
        } else {
            // If no container, insert at the end of body
            document.body.insertAdjacentHTML('beforeend', footerHTML);
        }
    }

    // Mobile menu toggle
    window.toggleMobileMenu = function() {
        const menu = document.getElementById('navMenu');
        menu.classList.toggle('active');
    };

    // Dropdown toggle for mobile
    window.toggleDropdown = function(btn) {
        if (window.innerWidth <= 900) {
            const dropdown = btn.closest('.dropdown');
            dropdown.classList.toggle('active');
        }
    };

    // Highlight current page in nav
    function highlightCurrentPage() {
        const currentPath = window.location.pathname;
        const links = document.querySelectorAll('.site-nav .nav-link, .site-nav .dropdown-item');

        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.endsWith(href.replace(base, ''))) {
                link.classList.add('active');
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            insertNav();
            insertFooter();
            highlightCurrentPage();
        });
    } else {
        insertNav();
        insertFooter();
        highlightCurrentPage();
    }
})();
