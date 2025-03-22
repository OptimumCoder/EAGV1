document.addEventListener('DOMContentLoaded', function() {
    const API_URL = 'http://127.0.0.1:5002/api/stocks';
    const content = document.getElementById('content');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const lastUpdate = document.getElementById('lastUpdate');
    const refreshBtn = document.getElementById('refreshBtn');
    const RUPEE = '\u20B9'; // Unicode for Indian Rupee symbol

    function formatNumber(num) {
        return new Intl.NumberFormat('en-IN').format(num);
    }

    function formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    function formatPriceChange(change) {
        const formatted = change.toFixed(2);
        return `${formatted > 0 ? '+' : ''}${formatted}%`;
    }

    function updateStats(stats) {
        document.getElementById('totalStocks').textContent = stats.total_analyzed;
        document.getElementById('successfulFetches').textContent = stats.successful_fetches;
        document.getElementById('avgPrice').textContent = `${RUPEE} ${formatNumber(stats.avg_price.toFixed(2))}`;
        document.getElementById('avgVolume').textContent = formatNumber(Math.round(stats.avg_volume));
        document.getElementById('totalValue').textContent = `${RUPEE} ${formatNumber(stats.total_value.toFixed(2))}`;
        document.getElementById('avgPriceChange').textContent = formatPriceChange(stats.avg_price_change);
        document.getElementById('dateRange').textContent = stats.date_range;
    }

    function createTableRow(stock) {
        const row = document.createElement('tr');
        
        // Check if there's an error for this stock
        if (stock.Error) {
            row.innerHTML = `
                <td>${stock.Symbol}</td>
                <td colspan="7" class="error-message">${stock.Error}</td>
            `;
            return row;
        }
        
        const priceChangeClass = stock['Price Change (%)'] >= 0 ? 'price-change-positive' : 'price-change-negative';
        
        row.innerHTML = `
            <td>${stock.Symbol}</td>
            <td>${RUPEE} ${formatNumber(stock['Current Price'])}</td>
            <td>${RUPEE} ${formatNumber(stock['Open'])}</td>
            <td>${RUPEE} ${formatNumber(stock['High'])}</td>
            <td>${RUPEE} ${formatNumber(stock['Low'])}</td>
            <td>${formatNumber(stock['Volume'])}</td>
            <td>${RUPEE} ${formatNumber(stock['Value'])}</td>
            <td class="${priceChangeClass}">${formatPriceChange(stock['Price Change (%)'])}</td>
        `;
        return row;
    }

    function sortTable(columnIndex, isNumeric = true) {
        const tbody = document.getElementById('stockTableBody');
        const rows = Array.from(tbody.getElementsByTagName('tr'));
        const headers = document.getElementsByTagName('th');
        const currentHeader = headers[columnIndex];
        const isAscending = !currentHeader.classList.contains('th-sort-asc');

        // Remove sorting classes from all headers
        Array.from(headers).forEach(header => {
            header.classList.remove('th-sort-asc', 'th-sort-desc');
        });

        // Add sorting class to current header
        currentHeader.classList.add(isAscending ? 'th-sort-asc' : 'th-sort-desc');

        rows.sort((a, b) => {
            let aValue = a.cells[columnIndex].textContent;
            let bValue = b.cells[columnIndex].textContent;

            if (isNumeric) {
                // Update regex to include Rupee symbol
                aValue = parseFloat(aValue.replace(/[₹\u20B9,%\s]/g, ''));
                bValue = parseFloat(bValue.replace(/[₹\u20B9,%\s]/g, ''));
            }

            if (aValue < bValue) return isAscending ? -1 : 1;
            if (aValue > bValue) return isAscending ? 1 : -1;
            return 0;
        });

        rows.forEach(row => tbody.appendChild(row));
    }

    function setupTableSorting() {
        const headers = document.getElementsByTagName('th');
        Array.from(headers).forEach((header, index) => {
            header.addEventListener('click', () => {
                const isNumeric = index !== 0; // All columns except Symbol are numeric
                sortTable(index, isNumeric);
            });
        });
    }

    function showError(message) {
        error.textContent = message;
        error.style.display = 'block';
        loading.style.display = 'none';
        content.style.display = 'none';
    }

    async function fetchStockData() {
        loading.style.display = 'block';
        content.style.display = 'none';
        error.style.display = 'none';

        try {
            console.log('Fetching data from:', API_URL);
            const response = await fetch(API_URL, {
                mode: 'cors',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received data:', data);

            if (!data || !data.stocks) {
                throw new Error('Invalid data format received');
            }

            const tableBody = document.getElementById('stockTableBody');
            tableBody.innerHTML = '';

            // Update date information
            if (data.stocks.length > 0 && data.stocks[0].Date_Range) {
                document.getElementById('dateRange').textContent = data.stocks[0].Date_Range;
            }
            document.getElementById('updateTime').textContent = data.update_time;

            data.stocks.forEach(stock => {
                tableBody.appendChild(createTableRow(stock));
            });

            if (data.stats) {
                updateStats(data.stats);
            }
            
            loading.style.display = 'none';
            content.style.display = 'block';
            setupTableSorting();
        } catch (err) {
            console.error('Error details:', err);
            let errorMessage = 'Error loading data: ';
            if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
                errorMessage += `Cannot connect to server at ${API_URL}. Please ensure the Flask server is running.`;
            } else {
                errorMessage += `${err.message}. Please check if the server is running at ${API_URL}`;
            }
            showError(errorMessage);
        }
    }

    refreshBtn.addEventListener('click', fetchStockData);
    fetchStockData(); // Initial load
}); 