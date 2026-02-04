// FBA Analytics Dashboard - Charts

document.addEventListener('DOMContentLoaded', () => {
    initRevenueChart();
    initCategoryChart();
});

function initRevenueChart() {
    const ctx = document.getElementById('revenueChart').getContext('2d');

    const labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue',
                data: [5200, 6100, 5800, 7747],
                borderColor: '#00a8e8',
                backgroundColor: 'rgba(0, 168, 232, 0.15)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#00a8e8',
                pointBorderColor: '#232f3e',
                pointBorderWidth: 2,
                pointRadius: 4
            }, {
                label: 'Profit',
                data: [1560, 1952, 1798, 2532],
                borderColor: '#00c853',
                backgroundColor: 'rgba(0, 200, 83, 0.15)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#00c853',
                pointBorderColor: '#232f3e',
                pointBorderWidth: 2,
                pointRadius: 4
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
                    backgroundColor: '#232f3e',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.raw.toLocaleString();
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
                        color: '#b8c5d4'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.08)'
                    },
                    ticks: {
                        color: '#b8c5d4',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function initCategoryChart() {
    const ctx = document.getElementById('categoryChart').getContext('2d');

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Home & Kitchen', 'Electronics', 'Sports', 'Beauty'],
            datasets: [{
                data: [42, 28, 18, 12],
                backgroundColor: [
                    '#00a8e8',
                    '#ff9900',
                    '#00c853',
                    '#ffc107'
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        color: '#b8c5d4',
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#232f3e',
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
}
