/**
 * UI Components for the Financial Chatbot
 */

/**
 * Add a message to the chat
 * @param {string} text - Message text
 * @param {boolean} isUser - Whether the message is from the user
 * @returns {HTMLElement} - The message element
 */
function addMessage(text, isUser = false) {
    const chatMessages = document.getElementById('chatMessages');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    // Allow markdown-style formatting for bot messages
    if (!isUser) {
        // Convert markdown-style tables to HTML tables
        text = convertMarkdownTables(text);
        
        // Convert markdown-style lists to HTML lists
        text = convertMarkdownLists(text);
        
        // Convert line breaks to <br> tags
        text = text.replace(/\n/g, '<br>');
    }
    
    messageEl.innerHTML = text;
    chatMessages.appendChild(messageEl);
    
    // Scroll to the bottom of the chat
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageEl;
}

/**
 * Convert markdown-style tables to HTML tables
 * @param {string} text - Text that may contain markdown tables
 * @returns {string} - Text with markdown tables converted to HTML
 */
function convertMarkdownTables(text) {
    // If no tables, return text as is
    if (!text.includes('|')) return text;
    
    const lines = text.split('\n');
    let inTable = false;
    let tableHTML = '<table>';
    let result = [];
    
    for (let line of lines) {
        // Check if line is part of a table
        if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
            if (!inTable) {
                inTable = true;
                tableHTML = '<table>';
            }
            
            // Process table row
            const cells = line.split('|').slice(1, -1);
            let isHeader = false;
            
            // Check if next line is a separator row (---|---|---)
            const nextLineIndex = lines.indexOf(line) + 1;
            if (nextLineIndex < lines.length) {
                const nextLine = lines[nextLineIndex];
                if (nextLine.includes('|') && nextLine.replace(/\|/g, '').trim().replace(/[^-]/g, '') === '') {
                    isHeader = true;
                }
            }
            
            // Add row to table
            tableHTML += '<tr>';
            for (let cell of cells) {
                const tag = isHeader ? 'th' : 'td';
                tableHTML += `<${tag}>${cell.trim()}</${tag}>`;
            }
            tableHTML += '</tr>';
            
            // Skip separator row if this was a header row
            if (isHeader) {
                lines[nextLineIndex] = '';
            }
        } else {
            // End of table
            if (inTable) {
                inTable = false;
                tableHTML += '</table>';
                result.push(tableHTML);
            } else {
                result.push(line);
            }
        }
    }
    
    // Close any open table
    if (inTable) {
        tableHTML += '</table>';
        result.push(tableHTML);
    }
    
    return result.join('\n');
}

/**
 * Convert markdown-style lists to HTML lists
 * @param {string} text - Text that may contain markdown lists
 * @returns {string} - Text with markdown lists converted to HTML
 */
function convertMarkdownLists(text) {
    // If no lists, return text as is
    if (!text.includes('- ') && !text.includes('* ')) return text;
    
    const lines = text.split('\n');
    let inList = false;
    let listHTML = '<ul>';
    let result = [];
    
    for (let line of lines) {
        // Check if line is part of a list
        if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
            if (!inList) {
                inList = true;
                listHTML = '<ul>';
            }
            
            // Process list item
            const content = line.trim().substring(2);
            listHTML += `<li>${content}</li>`;
        } else {
            // End of list
            if (inList) {
                inList = false;
                listHTML += '</ul>';
                result.push(listHTML);
            } 
            result.push(line);
        }
    }
    
    // Close any open list
    if (inList) {
        listHTML += '</ul>';
        result.push(listHTML);
    }
    
    return result.join('\n');
}

/**
 * Show a loading indicator
 * @param {boolean} show - Whether to show or hide the indicator
 */
function showLoading(show = true) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (show) {
        loadingIndicator.classList.add('visible');
    } else {
        loadingIndicator.classList.remove('visible');
    }
}

/**
 * Create stock list items
 * @param {Array} stocks - Array of stock objects
 * @param {Function} clickHandler - Function to handle click events
 */
function createStockList(stocks, clickHandler) {
    const stockList = document.getElementById('stockList');
    stockList.innerHTML = ''; // Clear existing items
    
    stocks.forEach(stock => {
        const stockItem = document.createElement('div');
        stockItem.className = 'stock-item';
        stockItem.dataset.symbol = stock.symbol;
        
        stockItem.innerHTML = `
            <span class="stock-symbol">${stock.symbol}</span>
            <span>${stock.name}</span>
        `;
        
        stockItem.addEventListener('click', clickHandler);
        stockList.appendChild(stockItem);
    });
}

/**
 * Show an error message
 * @param {string} message - Error message
 * @param {number} duration - Duration in milliseconds
 */
function showError(message, duration = 5000) {
    const chatMessages = document.getElementById('chatMessages');
    
    const alertEl = document.createElement('div');
    alertEl.className = 'alert alert-error';
    alertEl.textContent = message;
    
    chatMessages.appendChild(alertEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Remove after duration
    setTimeout(() => {
        alertEl.style.opacity = '0';
        setTimeout(() => alertEl.remove(), 300);
    }, duration);
}

/**
 * Show a success message
 * @param {string} message - Success message
 * @param {number} duration - Duration in milliseconds
 */
function showSuccess(message, duration = 3000) {
    const chatMessages = document.getElementById('chatMessages');
    
    const alertEl = document.createElement('div');
    alertEl.className = 'alert alert-success';
    alertEl.textContent = message;
    
    chatMessages.appendChild(alertEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Remove after duration
    setTimeout(() => {
        alertEl.style.opacity = '0';
        setTimeout(() => alertEl.remove(), 300);
    }, duration);
}

/**
 * Update the data freshness indicator
 * @param {string} timestamp - ISO timestamp string
 */
function updateDataFreshness(timestamp) {
    const dataFreshnessEl = document.getElementById('dataFreshness');
    
    if (!timestamp) {
        dataFreshnessEl.textContent = 'Data last updated: Never';
        return;
    }
    
    const date = new Date(timestamp);
    dataFreshnessEl.textContent = `Data last updated: ${date.toLocaleString()}`;
}

/**
 * Disable or enable the send button
 * @param {boolean} disabled - Whether to disable the button
 */
function disableSendButton(disabled = true) {
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = disabled;
}

/**
 * Clear all selected stocks
 */
function clearStockSelection() {
    const selectedStocks = document.querySelectorAll('.stock-item.selected');
    selectedStocks.forEach(item => {
        item.classList.remove('selected');
    });
}

/**
 * Get currently selected stock symbols
 * @returns {Array} - Array of selected stock symbols
 */
function getSelectedStocks() {
    const selectedStocks = document.querySelectorAll('.stock-item.selected');
    return Array.from(selectedStocks).map(item => item.dataset.symbol);
}