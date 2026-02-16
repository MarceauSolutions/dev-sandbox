/**
 * Business Analytics Dashboard - JavaScript
 * Interactive charts and data visualization
 */

document.addEventListener('DOMContentLoaded', () => {
    initDate();
    initCharts();
    populateOrders();
    populateProducts();
    populateActivity();
    initTabs();
});

/**
 * Set current date
 */
function initDate() {
    const dateEl = document.getElementById('current-date');
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateEl.textContent = now.toLocaleDateString('en-US', options);
}

/**
 * Initialize charts
 */
function initCharts() {
    initRevenueChart();
    initTrafficChart();
}

/**
 * Revenue Chart
 */
function initRevenueChart() {
    const ctx = document.getElementById('revenueChart').getContext('2d');

    const gradient = ctx.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.3)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Revenue',
                data: [4200, 5100, 4800, 6200, 5800, 7100, 8200],
                borderColor: '#6366f1',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#6366f1',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }, {
                label: 'Last Week',
                data: [3800, 4200, 4500, 5100, 5200, 6200, 7000],
                borderColor: '#d1d5db',
                borderWidth: 2,
                fill: false,
                tension: 0.4,
                pointRadius: 0,
                borderDash: [5, 5]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return '$' + context.raw.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#9ca3af'
                    }
                },
                y: {
                    grid: {
                        color: '#f3f4f6'
                    },
                    ticks: {
                        color: '#9ca3af',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

/**
 * Traffic Sources Chart
 */
function initTrafficChart() {
    const ctx = document.getElementById('trafficChart').getContext('2d');

    const data = [
        { label: 'Direct', value: 35, color: '#6366f1' },
        { label: 'Organic Search', value: 28, color: '#22c55e' },
        { label: 'Social Media', value: 22, color: '#0ea5e9' },
        { label: 'Referral', value: 15, color: '#f59e0b' }
    ];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.label),
            datasets: [{
                data: data.map(d => d.value),
                backgroundColor: data.map(d => d.color),
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.raw + '%';
                        }
                    }
                }
            }
        }
    });

    // Create custom legend
    const legendEl = document.getElementById('traffic-legend');
    data.forEach(item => {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <span class="legend-color" style="background: ${item.color}"></span>
            <span>${item.label}: ${item.value}%</span>
        `;
        legendEl.appendChild(legendItem);
    });
}

/**
 * Populate recent orders
 */
function populateOrders() {
    const orders = [
        { id: '#ORD-7291', customer: 'Sarah Mitchell', amount: '$1,249.00', status: 'completed' },
        { id: '#ORD-7290', customer: 'James Chen', amount: '$890.00', status: 'processing' },
        { id: '#ORD-7289', customer: 'Emily Rodriguez', amount: '$2,100.00', status: 'completed' },
        { id: '#ORD-7288', customer: 'Michael Brown', amount: '$450.00', status: 'pending' },
        { id: '#ORD-7287', customer: 'Lisa Anderson', amount: '$1,850.00', status: 'completed' }
    ];

    const tableBody = document.getElementById('orders-table');
    orders.forEach(order => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="order-id">${order.id}</span></td>
            <td>${order.customer}</td>
            <td>${order.amount}</td>
            <td><span class="status-badge ${order.status}">${order.status}</span></td>
        `;
        tableBody.appendChild(row);
    });
}

/**
 * Populate top products
 */
function populateProducts() {
    const products = [
        { name: 'Website Development', sales: 284, revenue: '$28,400', emoji: '🌐' },
        { name: 'SEO Optimization', sales: 196, revenue: '$19,600', emoji: '📈' },
        { name: 'Social Media Marketing', sales: 142, revenue: '$14,200', emoji: '📱' },
        { name: 'Content Writing', sales: 98, revenue: '$9,800', emoji: '✍️' }
    ];

    const listEl = document.getElementById('products-list');
    products.forEach(product => {
        const item = document.createElement('div');
        item.className = 'product-item';
        item.innerHTML = `
            <div class="product-image">${product.emoji}</div>
            <div class="product-info">
                <span class="product-name">${product.name}</span>
                <span class="product-sales">${product.sales} sales</span>
            </div>
            <span class="product-revenue">${product.revenue}</span>
        `;
        listEl.appendChild(item);
    });
}

/**
 * Populate activity feed
 */
function populateActivity() {
    const activities = [
        { type: 'order', text: '<strong>New order</strong> #ORD-7291 from Sarah Mitchell', time: '2 minutes ago' },
        { type: 'payment', text: '<strong>Payment received</strong> for order #ORD-7289', time: '15 minutes ago' },
        { type: 'user', text: '<strong>New customer</strong> James Chen registered', time: '1 hour ago' },
        { type: 'order', text: '<strong>New order</strong> #ORD-7288 from Michael Brown', time: '2 hours ago' },
        { type: 'payment', text: '<strong>Payment received</strong> for order #ORD-7285', time: '3 hours ago' }
    ];

    const feedEl = document.getElementById('activity-feed');
    activities.forEach(activity => {
        const item = document.createElement('div');
        item.className = 'activity-item';

        let iconSvg = '';
        if (activity.type === 'order') {
            iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>';
        } else if (activity.type === 'payment') {
            iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>';
        } else {
            iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
        }

        item.innerHTML = `
            <div class="activity-icon ${activity.type}">${iconSvg}</div>
            <div class="activity-content">
                <span class="activity-text">${activity.text}</span>
                <span class="activity-time">${activity.time}</span>
            </div>
        `;
        feedEl.appendChild(item);
    });
}

/**
 * Tab switching
 */
function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            // In a real app, this would update the chart data
        });
    });
}

/**
 * Animate numbers
 */
function animateValue(element, start, end, duration) {
    const startTimestamp = Date.now();
    const step = () => {
        const progress = Math.min((Date.now() - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value.toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Add animated counter on page load
document.querySelectorAll('.stat-value').forEach(el => {
    const text = el.textContent;
    const isPrice = text.startsWith('$');
    const isPercent = text.endsWith('%');
    let value = parseFloat(text.replace(/[$,%]/g, '').replace(/,/g, ''));

    if (!isNaN(value)) {
        el.textContent = isPrice ? '$0' : isPercent ? '0%' : '0';
        setTimeout(() => {
            animateValue(el, 0, value, 1000);
            if (isPrice) {
                el.textContent = '$' + value.toLocaleString();
            } else if (isPercent) {
                el.textContent = value + '%';
            }
        }, 100);
    }
});
