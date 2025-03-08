from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
import logging
from dotenv import load_dotenv
from financial_data_collector import FinancialDataCollector, FinancialAIAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

app = Flask(__name__, static_folder='../frontend',static_url_path='')
CORS(app)  # Enable CORS for all routes

# Initialize Financial AI Agent
try:
    agent = FinancialAIAgent()
    logger.info("Financial AI Agent initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Financial AI Agent: {e}")
    agent = None

@app.route('/')
def index():
    """Serve the index.html file"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "agent_initialized": agent is not None
    })

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """Return list of available stocks"""
    stocks = [
        {"symbol": "AAPL", "name": "Apple"},
        {"symbol": "MSFT", "name": "Microsoft"},
        {"symbol": "GOOGL", "name": "Google"},
        {"symbol": "AMZN", "name": "Amazon"},
        {"symbol": "TSLA", "name": "Tesla"},
        {"symbol": "META", "name": "Meta"},
        {"symbol": "NVDA", "name": "NVIDIA"},
        {"symbol": "INTC", "name": "Intel"},
        {"symbol": "IBM", "name": "IBM"},
        {"symbol": "WMT", "name": "Walmart"},
        {"symbol": "TGT", "name": "Target"},
        {"symbol": "COST", "name": "Costco"},
        {"symbol": "NKE", "name": "Nike"},
        {"symbol": "PEP", "name": "PepsiCo"},
        {"symbol": "KO", "name": "Coca-Cola"},
        {"symbol": "AMD", "name": "AMD"},
        {"symbol": "JPM", "name": "JPMorgan"},
        {"symbol": "BAC", "name": "Bank of America"},
        {"symbol": "V", "name": "Visa"},
        {"symbol": "MA", "name": "Mastercard"}
    ]
    return jsonify(stocks)

@app.route('/api/update-data', methods=['POST'])
def update_data():
    """Update financial data for the specified stocks"""
    if agent is None:
        return jsonify({
            "success": False,
            "message": "Financial AI Agent not initialized"
        }), 500
        
    data = request.json
    symbols = data.get('symbols', [])
    
    if not symbols:
        return jsonify({
            "success": False,
            "message": "No symbols provided"
        }), 400
    
    try:
        # Initialize collector if needed
        agent.initialize_collector()
        
        # Collect fresh data
        agent.collect_fresh_data(
            symbols, 
            collect_news=data.get('collect_news', True),
            collect_financials=data.get('collect_financials', True),
            collect_historical=data.get('collect_historical', True)
        )
        
        return jsonify({
            "success": True,
            "message": f"Successfully updated data for {', '.join(symbols)}",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error updating data: {e}")
        return jsonify({
            "success": False,
            "message": f"Error updating data: {str(e)}"
        }), 500

@app.route('/api/query', methods=['POST'])
def query_ai():
    """Query the Financial AI Agent"""
    if agent is None:
        return jsonify({
            "success": False,
            "message": "Financial AI Agent not initialized"
        }), 500
        
    data = request.json
    query = data.get('query', '')
    symbols = data.get('symbols', [])
    collect_fresh = data.get('collect_fresh', False)
    
    if not query:
        return jsonify({
            "success": False,
            "message": "No query provided"
        }), 400
    
    try:
        logger.info(f"Processing query: '{query}' for symbols: {symbols}")
        
        # Get answer from AI agent
        answer = agent.answer_financial_question(
            query=query,
            symbols=symbols,
            collect_fresh=collect_fresh
        )
        
        logger.info(f"Query processed successfully")
        
        return jsonify({
            "success": True,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({
            "success": False,
            "message": f"Error processing query: {str(e)}"
        }), 500

@app.route('/api/historical-prices', methods=['GET'])
def get_historical_prices():
    """Get historical prices for a symbol"""
    if agent is None:
        return jsonify({
            "success": False,
            "message": "Financial AI Agent not initialized"
        }), 500
        
    symbol = request.args.get('symbol')
    
    if not symbol:
        return jsonify({
            "success": False,
            "message": "No symbol provided"
        }), 400
    
    try:
        # Get historical prices
        df = agent.get_historical_prices(symbol)
        
        if df is None:
            return jsonify({
                "success": False,
                "message": f"No historical data found for {symbol}"
            }), 404
        
        # Convert to JSON-friendly format
        historical_data = df.to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "symbol": symbol,
            "data": historical_data
        })
    except Exception as e:
        logger.error(f"Error fetching historical prices: {e}")
        return jsonify({
            "success": False,
            "message": f"Error fetching historical prices: {str(e)}"
        }), 500

@app.route('/api/company-news', methods=['GET'])
def get_company_news():
    """Get latest news for a company"""
    if agent is None:
        return jsonify({
            "success": False,
            "message": "Financial AI Agent not initialized"
        }), 500
        
    symbol = request.args.get('symbol')
    
    if not symbol:
        return jsonify({
            "success": False,
            "message": "No symbol provided"
        }), 400
    
    try:
        # Get latest news
        df = agent.get_latest_news(symbol)
        
        if df is None:
            return jsonify({
                "success": False,
                "message": f"No news found for {symbol}"
            }), 404
        
        # Convert to JSON-friendly format
        news_data = df.to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "symbol": symbol,
            "data": news_data
        })
    except Exception as e:
        logger.error(f"Error fetching company news: {e}")
        return jsonify({
            "success": False,
            "message": f"Error fetching company news: {str(e)}"
        }), 500

@app.route('/api/stock-prices', methods=['GET'])
def get_stock_prices():
    """Get latest stock prices"""
    if agent is None:
        return jsonify({
            "success": False,
            "message": "Financial AI Agent not initialized"
        }), 500
        
    symbols = request.args.get('symbols', '').split(',')
    symbols = [s.strip() for s in symbols if s.strip()]
    
    try:
        # Get latest stock prices
        df = agent.get_latest_stock_prices(symbols if symbols else None)
        
        if df is None:
            return jsonify({
                "success": False,
                "message": "No stock price data found"
            }), 404
        
        # Convert to JSON-friendly format
        price_data = df.to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "data": price_data
        })
    except Exception as e:
        logger.error(f"Error fetching stock prices: {e}")
        return jsonify({
            "success": False,
            "message": f"Error fetching stock prices: {str(e)}"
        }), 500
@app.route('/api/test-data-collection')
def test_data_collection():
    try:
        agent.initialize_collector()
        agent.collect_fresh_data(['AAPL'])
        return jsonify({"success": True, "message": "Data collection test successful"})
    except Exception as e:
        logger.error(f"Test data collection error: {e}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Financial Chatbot server on port {port}")
    #app.run(debug=True, host='0.0.0.0', port=port)
    app.run(debug=True, host='0.0.0.0', port=5000)