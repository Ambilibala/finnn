/**
 * Financial Chatbot API Client
 * Handles communication with the backend API
 */

class ApiClient {
    constructor(baseUrl = 'http://localhost:5000/api') {
        this.baseUrl = baseUrl;
    }

    /**
     * Make a GET request to the API
     * @param {string} endpoint - API endpoint
     * @param {Object} params - Query parameters
     * @returns {Promise<Object>} - Response data
     */
    async get(endpoint, params = {}) {
        try {
            // Build query string from params
            const queryString = Object.keys(params).length 
                ? '?' + new URLSearchParams(params).toString() 
                : '';
            
            const response = await fetch(`${this.baseUrl}/${endpoint}${queryString}`);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `API error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error in GET ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Make a POST request to the API
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request body data
     * @returns {Promise<Object>} - Response data
     */
    async post(endpoint, data = {}) {
        try {
            const response = await fetch(`${this.baseUrl}/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `API error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error in POST ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Check the API health status
     * @returns {Promise<Object>} - Health status data
     */
    async checkHealth() {
        return this.get('health');
    }

    /**
     * Get available stocks list
     * @returns {Promise<Array>} - List of stock objects
     */
    async getStocks() {
        return this.get('stocks');
    }

    /**
     * Update data for selected stocks
     * @param {Array<string>} symbols - List of stock symbols
     * @param {Object} options - Update options
     * @returns {Promise<Object>} - Update result
     */
    async updateData(symbols, options = {}) {
        const data = {
            symbols,
            collect_news: options.collectNews !== false,
            collect_financials: options.collectFinancials !== false,
            collect_historical: options.collectHistorical !== false
        };
        
        return this.post('update-data', data);
    }

    /**
     * Send a query to the AI
     * @param {string} query - User query
     * @param {Array<string>} symbols - List of relevant stock symbols
     * @param {boolean} collectFresh - Whether to collect fresh data
     * @returns {Promise<Object>} - AI response
     */
    async queryAi(query, symbols = [], collectFresh = false) {
        const data = {
            query,
            symbols,
            collect_fresh: collectFresh
        };
        
        return this.post('query', data);
    }

    /**
     * Get historical prices for a symbol
     * @param {string} symbol - Stock symbol
     * @returns {Promise<Object>} - Historical price data
     */
    async getHistoricalPrices(symbol) {
        return this.get('historical-prices', { symbol });
    }

    /**
     * Get company news
     * @param {string} symbol - Stock symbol
     * @returns {Promise<Object>} - Company news data
     */
    async getCompanyNews(symbol) {
        return this.get('company-news', { symbol });
    }

    /**
     * Get stock prices
     * @param {Array<string>} symbols - List of stock symbols
     * @returns {Promise<Object>} - Stock price data
     */
    async getStockPrices(symbols = []) {
        return this.get('stock-prices', { 
            symbols: symbols.join(',') 
        });
    }
}

// Create a global API client instance
const api = new ApiClient();