/**
 * LeadHunter Pro - JavaScript
 * Lead scraper interface interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    populateLeads();
    initScraper();
    initNavigation();
});

/**
 * Sample lead data
 */
const sampleLeads = [
    {
        name: 'Naples Fitness Center',
        category: 'Gym & Fitness',
        email: 'info@naplesfitness.com',
        phone: '(239) 555-0123',
        location: 'Naples, FL',
        painPoints: ['no-website', 'few-reviews'],
        score: 92
    },
    {
        name: 'Sunshine Dental Care',
        category: 'Dental Practice',
        email: 'contact@sunshinedental.com',
        phone: '(239) 555-0456',
        location: 'Naples, FL',
        painPoints: ['no-social'],
        score: 78
    },
    {
        name: 'Gulf Coast HVAC Services',
        category: 'HVAC',
        email: 'service@gulfcoasthvac.com',
        phone: '(239) 555-0789',
        location: 'Naples, FL',
        painPoints: ['no-website', 'no-social'],
        score: 95
    },
    {
        name: 'Paradise Plumbing Co',
        category: 'Plumbing',
        email: 'info@paradiseplumbing.com',
        phone: '(239) 555-1012',
        location: 'Bonita Springs, FL',
        painPoints: ['few-reviews'],
        score: 65
    },
    {
        name: 'Marco Island Realty',
        category: 'Real Estate',
        email: 'sales@marcoislandrealty.com',
        phone: '(239) 555-1345',
        location: 'Marco Island, FL',
        painPoints: ['no-website'],
        score: 88
    },
    {
        name: 'Southwest Legal Group',
        category: 'Law Firm',
        email: 'contact@swlegalgroup.com',
        phone: '(239) 555-1678',
        location: 'Fort Myers, FL',
        painPoints: ['no-social', 'few-reviews'],
        score: 72
    },
    {
        name: 'Everglades Medical Clinic',
        category: 'Medical',
        email: 'appointments@evergladesmed.com',
        phone: '(239) 555-1901',
        location: 'Naples, FL',
        painPoints: ['no-website'],
        score: 84
    },
    {
        name: 'Coastal CrossFit',
        category: 'Gym & Fitness',
        email: 'hello@coastalcrossfit.com',
        phone: '(239) 555-2234',
        location: 'Naples, FL',
        painPoints: ['few-reviews', 'no-social'],
        score: 69
    },
    {
        name: 'Palm City Orthodontics',
        category: 'Dental Practice',
        email: 'smile@palmcityortho.com',
        phone: '(239) 555-2567',
        location: 'Naples, FL',
        painPoints: ['no-website', 'few-reviews'],
        score: 91
    },
    {
        name: 'SunState Pool Services',
        category: 'Home Services',
        email: 'pools@sunstateservices.com',
        phone: '(239) 555-2890',
        location: 'Estero, FL',
        painPoints: ['no-social'],
        score: 56
    }
];

/**
 * Populate leads table
 */
function populateLeads() {
    const tableBody = document.getElementById('leads-table-body');
    if (!tableBody) return;

    sampleLeads.forEach(lead => {
        const row = document.createElement('tr');

        // Determine score class
        let scoreClass = 'low';
        if (lead.score >= 80) scoreClass = 'high';
        else if (lead.score >= 60) scoreClass = 'medium';

        // Create pain point tags
        const painTags = lead.painPoints.map(pain => {
            const labels = {
                'no-website': 'No Website',
                'few-reviews': '< 50 Reviews',
                'no-social': 'No Social'
            };
            return `<span class="pain-tag ${pain}">${labels[pain]}</span>`;
        }).join('');

        row.innerHTML = `
            <td><input type="checkbox"></td>
            <td>
                <div class="business-name">${lead.name}</div>
                <div class="business-category">${lead.category}</div>
            </td>
            <td>
                <div class="contact-email">${lead.email}</div>
                <div class="contact-phone">${lead.phone}</div>
            </td>
            <td>${lead.location}</td>
            <td>${painTags}</td>
            <td>
                <div class="lead-score">
                    <div class="score-bar">
                        <div class="score-fill ${scoreClass}" style="width: ${lead.score}%"></div>
                    </div>
                    <span class="score-value">${lead.score}</span>
                </div>
            </td>
            <td>
                <div class="action-btns">
                    <button class="action-btn" title="Add to Campaign">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                    </button>
                    <button class="action-btn" title="View Details">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                    </button>
                    <button class="action-btn" title="Export">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="7 10 12 15 17 10"/>
                            <line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                    </button>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

/**
 * Initialize scraper functionality
 */
function initScraper() {
    const startBtn = document.getElementById('start-scrape-btn');
    const progressSection = document.getElementById('scrape-progress');
    const progressBar = document.getElementById('progress-bar');

    if (!startBtn || !progressSection) return;

    // Initially hide progress
    progressSection.style.display = 'none';

    startBtn.addEventListener('click', () => {
        // Validate inputs
        const industry = document.getElementById('industry-select').value;
        const location = document.getElementById('location-input').value;

        if (!industry || !location) {
            alert('Please select an industry and enter a location');
            return;
        }

        // Show progress
        progressSection.style.display = 'block';
        progressSection.classList.add('active');

        // Update title
        const industryText = document.getElementById('industry-select').options[
            document.getElementById('industry-select').selectedIndex
        ].text;
        progressSection.querySelector('.progress-title').textContent =
            `Scraping: ${industryText} in ${location}`;

        // Simulate scraping progress
        simulateScrape();
    });
}

/**
 * Simulate scraping progress
 */
function simulateScrape() {
    const progressBar = document.getElementById('progress-bar');
    const foundCount = document.getElementById('found-count');
    const verifiedCount = document.getElementById('verified-count');
    const emailsCount = document.getElementById('emails-count');
    const phonesCount = document.getElementById('phones-count');
    const statusEl = document.querySelector('.progress-status');

    let progress = 0;
    let found = 0;
    let verified = 0;
    let emails = 0;
    let phones = 0;

    // Target values
    const targetFound = 124;
    const targetVerified = 98;
    const targetEmails = 87;
    const targetPhones = 112;

    const interval = setInterval(() => {
        progress += Math.random() * 3;

        if (progress >= 100) {
            progress = 100;
            found = targetFound;
            verified = targetVerified;
            emails = targetEmails;
            phones = targetPhones;

            statusEl.textContent = 'Completed';
            statusEl.style.background = 'rgba(34, 197, 94, 0.15)';
            statusEl.style.color = '#22c55e';

            document.getElementById('scrape-progress').classList.remove('active');

            clearInterval(interval);
        } else {
            // Increment counts proportionally
            found = Math.floor((progress / 100) * targetFound);
            verified = Math.floor((progress / 100) * targetVerified);
            emails = Math.floor((progress / 100) * targetEmails);
            phones = Math.floor((progress / 100) * targetPhones);
        }

        // Update UI
        progressBar.style.width = progress + '%';
        foundCount.textContent = found;
        verifiedCount.textContent = verified;
        emailsCount.textContent = emails;
        phonesCount.textContent = phones;

    }, 100);
}

/**
 * Initialize navigation
 */
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

/**
 * Select all checkbox functionality
 */
const selectAllCheckbox = document.getElementById('select-all');
if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('#leads-table-body input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = e.target.checked);
    });
}

/**
 * Initialize animated counters for stats
 */
function animateCounters() {
    const statValues = document.querySelectorAll('.stat-value');

    statValues.forEach(el => {
        const text = el.textContent;
        const isPercent = text.includes('%');
        const value = parseFloat(text.replace(/[,%]/g, ''));

        if (!isNaN(value)) {
            let current = 0;
            const increment = value / 30;
            const isInteger = !isPercent && Number.isInteger(value);

            const timer = setInterval(() => {
                current += increment;
                if (current >= value) {
                    current = value;
                    clearInterval(timer);
                }

                if (isPercent) {
                    el.textContent = current.toFixed(1) + '%';
                } else if (isInteger) {
                    el.textContent = Math.floor(current).toLocaleString();
                } else {
                    el.textContent = current.toLocaleString();
                }
            }, 30);
        }
    });
}

// Run counter animation on load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(animateCounters, 200);
});

/**
 * Export functionality (demo)
 */
document.querySelectorAll('.btn-secondary').forEach(btn => {
    if (btn.textContent.includes('Export')) {
        btn.addEventListener('click', () => {
            // Simulate export
            const originalText = btn.innerHTML;
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="animate-spin">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                Exporting...
            `;
            btn.disabled = true;

            setTimeout(() => {
                btn.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Downloaded!
                `;

                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }, 1500);
            }, 1500);
        });
    }
});

// Add spin animation for loading state
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .animate-spin {
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);
