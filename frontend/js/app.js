/**
 * Financial Chatbot Main Application
 */

document.addEventListener('DOMContentLoaded', initializeApp);

// Global variables
let selectedStocks = [];
let isAPIHealthy = false;

/**
 * Initialize the application
 */
async function initializeApp() {
    // Set up event listeners
    setupEventListeners();
    
    // Get available stocks
    await loadStocks();
    
    // Check API health
    await checkAPIHealth();
}

/**
 * Check if the API is available and healthy
 */
async function checkAPIHealth() {
    try {
        showLoading(true);
        const health = await api.checkHealth();
        
        if (health.status === 'ok') {
            isAPIHealthy = true;
            
            // Update data freshness if available
            if (health.timestamp) {
                updateDataFreshness(health.timestamp);
            }
            
            // Hide loading and show success message
            showLoading(false);
            console.log('API is healthy');
        } else {
            handleAPIUnavailable();
        }
    } catch (error) {
        handleAPIUnavailable();
    }
}

/**
 * Handle when API is unavailable
 */
function handleAPIUnavailable() {
    isAPIHealthy = false;
    showLoading(false);
    showError('Could not connect to the backend API. Please make sure the server is running.');
    disableSendButton(true);
}

/**
 * Load available stocks from the API
 */
async function loadStocks() {
    try {
        // Show loading indicator in the stock list
        document.getElementById('stockList').innerHTML = '<div class="loading-stocks">Loading stocks...</div>';
        
        // Fetch stocks from API
        const stocks = await api.getStocks();
        
        // Create stock list items with click handler
        createStockList(stocks, handleStockItemClick);
    } catch (error) {
        console.error('Error loading stocks:', error);
        document.getElementById('stockList').innerHTML = '<div class="loading-stocks">Failed to load stocks. Please reload the page.</div>';
    }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Send message button
    document.getElementById('sendButton').addEventListener('click', sendMessage);
    
    // Message input (Enter key)
    document.getElementById('messageInput').addEventListener('keydown', event => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Update data button
    document.getElementById('updateDataBtn').addEventListener('click', updateData);
    
    // Clear selection button
    document.getElementById('clearSelectionBtn').addEventListener('click', clearSelection);
    
    // Suggestion items
    document.querySelectorAll('.suggestion').forEach(suggestion => {
        suggestion.addEventListener('click', () => {
            document.getElementById('messageInput').value = suggestion.dataset.text;
            document.getElementById('messageInput').focus();
        });
    });
}

/**
 * Handle clicking on a stock item
 * @param {Event} event - Click event
 */
function handleStockItemClick(event) {
    const stockItem = event.currentTarget;
    const symbol = stockItem.dataset.symbol;
    
    if (stockItem.classList.contains('selected')) {
        // Remove from selection
        stockItem.classList.remove('selected');
        selectedStocks = selectedStocks.filter(s => s !== symbol);
    } else {
        // Add to selection
        stockItem.classList.add('selected');
        selectedStocks.push(symbol);
    }
    
    console.log('Selected stocks:', selectedStocks);
}

/**
 * Clear stock selection
 */
function clearSelection() {
    clearStockSelection();
    selectedStocks = [];
    console.log('Selection cleared');
}

/**
 * Send a message to the AI
 */
async function sendMessage() {
    if (!isAPIHealthy) {
        showError('Cannot send messages because the API is unavailable.');
        return;
    }
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Get selected stocks
    selectedStocks = getSelectedStocks();
    
    // Check if stocks are selected
    if (selectedStocks.length === 0) {
        showError('Please select at least one stock from the sidebar before asking questions.');
        return;
    }
    
    // Add user message to chat
    addMessage(message, true);
    
    // Clear input
    messageInput.value = '';
    
    // Get collect fresh data option
    const collectFresh = document.getElementById('freshDataCheck').checked;
    
    // Show loading indicator
    showLoading(true);
    
    try {
        // Query the AI
        const response = await api.queryAi(message, selectedStocks, collectFresh);
        
        // Hide loading indicator
        showLoading(false);
        
        if (response.success) {
            // Add AI response to chat
            addMessage(response.answer);
            
            // Update data freshness if available
            if (response.timestamp) {
                updateDataFreshness(response.timestamp);
            }
        } else {
            // Show error message
            showError(response.message || 'Failed to get response from AI.');
        }
    } catch (error) {
        // Hide loading indicator
        showLoading(false);
        
        // Show error message
        showError(`Error: ${error.message || 'Failed to communicate with the API.'}`);
    }
}

/**
 * Update data for selected stocks
 */
async function updateData() {
    if (!isAPIHealthy) {
        showError('Cannot update data because the API is unavailable.');
        return;
    }
    
    // Get selected stocks
    selectedStocks = getSelectedStocks();
    
    // Check if stocks are selected
    if (selectedStocks.length === 0) {
        showError('Please select at least one stock before updating data.');
        return;
    }
    
    // Show loading indicator
    showLoading(true);
    
    // Add message to chat
    addMessage(`Updating data for ${selectedStocks.join(', ')}...`);
    
    try {
        // Update data
        const response = await api.updateData(selectedStocks);
        
        // Hide loading indicator
        showLoading(false);
        
        if (response.success) {
            // Show success message
            addMessage(`Data successfully updated for ${selectedStocks.join(', ')}.`);
            
            // Update data freshness if available
            if (response.timestamp) {
                updateDataFreshness(response.timestamp);
            }
        } else {
            // Show error message
            showError(response.message || 'Failed to update data.');
        }
    } catch (error) {
        // Hide loading indicator
        showLoading(false);
        
        // Show error message
        showError(`Error updating data: ${error.message || 'Unknown error'}`);
    }
}