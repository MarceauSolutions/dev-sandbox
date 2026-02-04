// FBA Restock Decision Calculator

document.addEventListener('DOMContentLoaded', () => {
    calculate();

    // Auto-recalculate on input change
    document.querySelectorAll('input').forEach(input => {
        input.addEventListener('input', calculate);
    });
});

function calculate() {
    // Get input values
    const currentInventory = parseFloat(document.getElementById('current-inventory').value) || 0;
    const dailyVelocity = parseFloat(document.getElementById('daily-velocity').value) || 0;
    const unitCost = parseFloat(document.getElementById('unit-cost').value) || 0;
    const salePrice = parseFloat(document.getElementById('sale-price').value) || 0;
    const storageFee = parseFloat(document.getElementById('storage-fee').value) || 0;
    const unitSize = parseFloat(document.getElementById('unit-size').value) || 0;
    const shippingCost = parseFloat(document.getElementById('shipping-cost').value) || 0;
    const leadTime = parseFloat(document.getElementById('lead-time').value) || 14;

    // Calculate current status
    const daysOfStock = dailyVelocity > 0 ? Math.floor(currentInventory / dailyVelocity) : 999;

    // Calculate stockout date
    const stockoutDate = new Date();
    stockoutDate.setDate(stockoutDate.getDate() + daysOfStock);
    const stockoutDateStr = stockoutDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

    // Determine status and risk
    let status, risk, statusClass;
    if (daysOfStock <= 7) {
        status = 'CRITICAL';
        risk = 'CRITICAL';
        statusClass = 'critical';
    } else if (daysOfStock <= 14) {
        status = 'WARNING';
        risk = 'HIGH';
        statusClass = 'warning';
    } else if (daysOfStock <= 30) {
        status = 'MONITOR';
        risk = 'MEDIUM';
        statusClass = 'warning';
    } else {
        status = 'OK';
        risk = 'LOW';
        statusClass = 'ok';
    }

    // Calculate recommended order quantity
    const targetDays = 60; // Target 60 days of stock
    const safetyStock = Math.ceil(dailyVelocity * leadTime); // Safety stock for lead time
    const targetStock = Math.ceil(dailyVelocity * targetDays);
    const orderQty = Math.max(0, targetStock - currentInventory + safetyStock);

    // Round to nearest 10 for cleaner orders
    const roundedOrderQty = Math.ceil(orderQty / 10) * 10;

    // Calculate costs
    const productCost = roundedOrderQty * unitCost;
    const totalShippingCost = roundedOrderQty * shippingCost;
    const monthlyStorageCostPerUnit = storageFee * unitSize;
    const storageCostFor60Days = (roundedOrderQty * monthlyStorageCostPerUnit * 2); // 2 months
    const totalOrderCost = productCost + totalShippingCost;

    // Calculate expected revenue from order
    const expectedRevenue = roundedOrderQty * salePrice;

    // Calculate stockout costs
    const lostSalesDays = leadTime;
    const lostSalesRevenue = lostSalesDays * dailyVelocity * salePrice;
    const amazonFeeRate = 0.22; // Approximately 22% for FBA fees
    const profitMarginRate = (salePrice - unitCost - (salePrice * amazonFeeRate)) / salePrice;
    const lostProfit = lostSalesRevenue * profitMarginRate;
    const rankingLoss = 500; // Estimated ranking recovery cost
    const totalLoss = lostProfit + rankingLoss;

    // Profit projection for 60 days
    const projectedUnits = targetDays * dailyVelocity;
    const projectedRevenue = projectedUnits * salePrice;
    const projectedCOGS = projectedUnits * unitCost;
    const projectedFees = projectedRevenue * amazonFeeRate;
    const projectedProfit = projectedRevenue - projectedCOGS - projectedFees - storageCostFor60Days;
    const profitMargin = (projectedProfit / projectedRevenue * 100);

    // Update UI - Current Status
    document.getElementById('days-of-stock').textContent = daysOfStock;
    document.getElementById('stockout-date').textContent = stockoutDateStr;
    document.getElementById('stockout-risk').textContent = risk;

    const statusBadge = document.getElementById('status-badge');
    statusBadge.textContent = status;
    statusBadge.className = 'status-badge ' + statusClass;

    // Update UI - Recommendation
    document.getElementById('order-qty').textContent = roundedOrderQty;
    document.getElementById('target-days').textContent = targetDays + ' days';
    document.getElementById('order-cost').textContent = formatCurrency(totalOrderCost);
    document.getElementById('expected-revenue').textContent = formatCurrency(expectedRevenue);

    // Update UI - Cost Analysis (Order)
    document.getElementById('product-cost-order').textContent = formatCurrency(productCost);
    document.getElementById('shipping-cost-order').textContent = formatCurrency(totalShippingCost);
    document.getElementById('storage-cost-order').textContent = formatCurrency(storageCostFor60Days);
    document.getElementById('total-cost-order').textContent = formatCurrency(totalOrderCost + storageCostFor60Days);

    // Update UI - Cost Analysis (Stockout)
    document.getElementById('lost-sales').textContent = formatCurrency(lostSalesRevenue);
    document.getElementById('lost-profit').textContent = formatCurrency(lostProfit);
    document.getElementById('ranking-loss').textContent = formatCurrency(rankingLoss);
    document.getElementById('total-loss').textContent = formatCurrency(totalLoss);

    // Update UI - Profit Projection
    document.getElementById('proj-revenue').textContent = formatCurrency(projectedRevenue);
    document.getElementById('proj-cogs').textContent = '-' + formatCurrency(projectedCOGS);
    document.getElementById('proj-fees').textContent = '-' + formatCurrency(projectedFees);
    document.getElementById('proj-storage').textContent = '-' + formatCurrency(storageCostFor60Days);
    document.getElementById('proj-profit').textContent = formatCurrency(projectedProfit);
    document.getElementById('proj-margin').textContent = profitMargin.toFixed(1) + '%';
}

function formatCurrency(value) {
    return '$' + value.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}
