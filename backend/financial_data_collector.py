import os
import pandas as pd
import glob
import time
import requests
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
import logging
import json
from dotenv import load_dotenv

# Import Google Generative AI for Gemini
import google.generativeai as genai

class FinancialDataCollector:
    """
    A class to collect financial data from various APIs and save it to disk.
    """
    def __init__(self, fmp_api_key=None, finnhub_api_key=None):
        """
        Initialize the collector with API keys and create necessary directories.

        Args:
            fmp_api_key (str, optional): API key for Financial Modeling Prep API.
                If not provided, will try to get from environment variable.
            finnhub_api_key (str, optional): API key for Finnhub API.
                If not provided, will try to get from environment variable.
        """
        # Load environment variables
        load_dotenv()

        # Use provided keys or get from environment
        self.fmp_api_key = fmp_api_key or os.getenv('FMP_API_KEY')
        self.finnhub_api_key = finnhub_api_key or os.getenv('FINNHUB_API_KEY')

        # Validate we have API keys
        if not self.fmp_api_key:
            raise ValueError("FMP API key is required. Provide as parameter or set FMP_API_KEY environment variable.")
        if not self.finnhub_api_key:
            raise ValueError("Finnhub API key is required. Provide as parameter or set FINNHUB_API_KEY environment variable.")

        # Set up API base URLs
        self.fmp_base_url = "https://financialmodelingprep.com/api/v3"
        self.finnhub_base_url = "https://finnhub.io/api/v1"

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("financial_data_collector.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Create data directories
        self.data_dir = "financial_data"
        self.prices_dir = f"{self.data_dir}/prices"
        self.historical_dir = f"{self.data_dir}/historical"
        self.company_news_dir = f"{self.data_dir}/company_news"
        self.articles_dir = f"{self.data_dir}/articles"
        self.financials_dir = f"{self.data_dir}/financials"

        for directory in [self.data_dir, self.prices_dir, self.historical_dir,
                          self.company_news_dir, self.articles_dir, self.financials_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"Created directory: {directory}")

    def _handle_rate_limit(self, response):
        """
        Handle rate limiting from APIs.

        Args:
            response (requests.Response): The API response to check

        Returns:
            bool: True if rate limited, False otherwise
        """
        # Check if we're being rate limited
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            self.logger.warning(f"Rate limited. Waiting {retry_after} seconds before retrying.")
            time.sleep(retry_after)
            return True
        return False

    def get_stock_quotes(self, symbols, output_format='csv'):
        """
        Get real-time stock quotes from FMP.

        Args:
            symbols (list): List of stock symbols to fetch quotes for
            output_format (str): Output format ('csv' or 'html')

        Returns:
            str: Path to saved file, or None if error
        """
        today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        symbols_str = ','.join(symbols)
        endpoint = f"{self.fmp_base_url}/quote/{symbols_str}"
        params = {'apikey': self.fmp_api_key}

        try:
            self.logger.info(f"Fetching quotes for {symbols_str}")
            response = requests.get(endpoint, params=params, timeout=30)

            if self._handle_rate_limit(response):
                # Retry after waiting for rate limit
                return self.get_stock_quotes(symbols, output_format)

            if response.status_code != 200:
                self.logger.error(f"Error fetching quotes: {response.status_code}")
                return None

            data = response.json()

            if not data:
                self.logger.warning(f"No quote data returned")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Save data
            file_path = f"{self.prices_dir}/quotes_{today}"
            if output_format.lower() == 'csv':
                df.to_csv(f"{file_path}.csv", index=False)
                self.logger.info(f"Saved quotes to {file_path}.csv")
                return f"{file_path}.csv"
            else:
                df.to_html(f"{file_path}.html", index=False)
                self.logger.info(f"Saved quotes to {file_path}.html")
                return f"{file_path}.html"

        except requests.exceptions.Timeout:
            self.logger.error("Request timed out while fetching quotes")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error while fetching quotes")
            return None
        except Exception as e:
            self.logger.error(f"Exception while fetching quotes: {e}")
            return None

    def get_historical_prices(self, symbol, output_format='csv'):
        """
        Get historical daily prices from FMP.

        Args:
            symbol (str): Stock symbol to fetch historical prices for
            output_format (str): Output format ('csv' or 'html')

        Returns:
            str: Path to saved file, or None if error
        """
        today = datetime.now().strftime('%Y-%m-%d')
        endpoint = f"{self.fmp_base_url}/historical-price-full/{symbol}"
        params = {'apikey': self.fmp_api_key}

        try:
            self.logger.info(f"Fetching historical prices for {symbol}")
            response = requests.get(endpoint, params=params, timeout=30)

            if self._handle_rate_limit(response):
                # Retry after waiting for rate limit
                return self.get_historical_prices(symbol, output_format)

            if response.status_code != 200:
                self.logger.error(f"Error fetching historical prices: {response.status_code}")
                return None

            data = response.json()

            if not data or 'historical' not in data:
                self.logger.warning(f"No historical data returned for {symbol}")
                return None

            # Convert to DataFrame
            historical_data = data['historical']
            df = pd.DataFrame(historical_data)

            # Save data
            file_path = f"{self.historical_dir}/{symbol}_historical_{today}"
            if output_format.lower() == 'csv':
                df.to_csv(f"{file_path}.csv", index=False)
                self.logger.info(f"Saved historical prices to {file_path}.csv")
                return f"{file_path}.csv"
            else:
                df.to_html(f"{file_path}.html", index=False)
                self.logger.info(f"Saved historical prices to {file_path}.html")
                return f"{file_path}.html"

        except Exception as e:
            self.logger.error(f"Exception while fetching historical prices: {e}")
            return None

    def get_fmp_articles(self, limit=50, output_format='csv'):
        """
        Get FMP articles which are accessible on free tier.

        Args:
            limit (int): Maximum number of articles to fetch
            output_format (str): Output format ('csv' or 'html')

        Returns:
            str: Path to saved file, or None if error
        """
        today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        endpoint = f"{self.fmp_base_url}/fmp/articles"
        params = {'apikey': self.fmp_api_key, 'limit': limit}

        try:
            self.logger.info(f"Fetching FMP articles (limit: {limit})")
            response = requests.get(endpoint, params=params, timeout=30)

            if self._handle_rate_limit(response):
                # Retry after waiting for rate limit
                return self.get_fmp_articles(limit, output_format)

            if response.status_code != 200:
                self.logger.error(f"Error fetching FMP articles: {response.status_code}")
                return None

            data = response.json()

            if not data or 'content' not in data:
                self.logger.warning(f"No article data returned")
                return None

            # Convert to DataFrame
            articles = data['content']
            df = pd.DataFrame(articles)

            # Save data
            file_path = f"{self.articles_dir}/fmp_articles_{today}"
            if output_format.lower() == 'csv':
                df.to_csv(f"{file_path}.csv", index=False)
                self.logger.info(f"Saved FMP articles to {file_path}.csv")
                return f"{file_path}.csv"
            else:
                df.to_html(f"{file_path}.html", index=False)
                self.logger.info(f"Saved FMP articles to {file_path}.html")
                return f"{file_path}.html"

        except Exception as e:
            self.logger.error(f"Exception while fetching FMP articles: {e}")
            return None

    def get_company_news(self, symbol, from_date, to_date, output_format='csv'):
        """
        Get company news from Finnhub.

        Args:
            symbol (str): Stock symbol to fetch news for
            from_date (str): Start date in format 'YYYY-MM-DD'
            to_date (str): End date in format 'YYYY-MM-DD'
            output_format (str): Output format ('csv' or 'html')

        Returns:
            str: Path to saved file, or None if error
        """
        today = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        endpoint = f"{self.finnhub_base_url}/company-news"
        params = {
            'symbol': symbol,
            'from': from_date,
            'to': to_date,
            'token': self.finnhub_api_key
        }

        try:
            self.logger.info(f"Fetching company news for {symbol} from {from_date} to {to_date}")
            response = requests.get(endpoint, params=params, timeout=30)

            if self._handle_rate_limit(response):
                # Retry after waiting for rate limit
                return self.get_company_news(symbol, from_date, to_date, output_format)

            if response.status_code != 200:
                self.logger.error(f"Error fetching company news: {response.status_code}")
                return None

            data = response.json()

            if not data:
                self.logger.warning(f"No company news returned for {symbol}")
                return None

            # Process news data
            processed_data = []
            for item in data[:100]:  # Limit to 100 news items
                processed_data.append({
                    'symbol': symbol,
                    'datetime': datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                    'headline': item.get('headline', ''),
                    'source': item.get('source', ''),
                    'summary': item.get('summary', ''),
                    'url': item.get('url', '')
                })

            # Convert to DataFrame
            df = pd.DataFrame(processed_data)

            # Save data
            file_path = f"{self.company_news_dir}/{symbol}_news_{today}"
            if output_format.lower() == 'csv':
                df.to_csv(f"{file_path}.csv", index=False)
                self.logger.info(f"Saved company news to {file_path}.csv")
                return f"{file_path}.csv"
            else:
                df.to_html(f"{file_path}.html", index=False)
                self.logger.info(f"Saved company news to {file_path}.html")
                return f"{file_path}.html"

        except Exception as e:
            self.logger.error(f"Exception while fetching company news for {symbol}: {e}")
            return None

    def get_basic_financials(self, symbol, output_format='csv'):
        """
        Get basic financials from Finnhub.

        Args:
            symbol (str): Stock symbol to fetch financials for
            output_format (str): Output format ('csv' or 'html')

        Returns:
            str: Path to saved file, or None if error
        """
        today = datetime.now().strftime('%Y-%m-%d')
        endpoint = f"{self.finnhub_base_url}/stock/metric"
        params = {
            'symbol': symbol,
            'metric': 'all',
            'token': self.finnhub_api_key
        }

        try:
            self.logger.info(f"Fetching basic financials for {symbol}")
            response = requests.get(endpoint, params=params, timeout=30)

            if self._handle_rate_limit(response):
                # Retry after waiting for rate limit
                return self.get_basic_financials(symbol, output_format)

            if response.status_code != 200:
                self.logger.error(f"Error fetching basic financials: {response.status_code}")
                return None

            data = response.json()

            if not data or 'metric' not in data:
                self.logger.warning(f"No financial data returned for {symbol}")
                return None

            # Process metrics data
            metrics = data['metric']
            # Flatten the metrics dictionary
            df = pd.DataFrame([metrics])

            # Save data
            file_path = f"{self.financials_dir}/{symbol}_financials_{today}"
            if output_format.lower() == 'csv':
                df.to_csv(f"{file_path}.csv", index=False)
                self.logger.info(f"Saved basic financials to {file_path}.csv")
                return f"{file_path}.csv"
            else:
                df.to_html(f"{file_path}.html", index=False)
                self.logger.info(f"Saved basic financials to {file_path}.html")
                return f"{file_path}.html"

        except Exception as e:
            self.logger.error(f"Exception while fetching basic financials for {symbol}: {e}")
            return None


class FinancialAIAgent:
    """
    An AI agent that retrieves and analyzes financial data from documents collected by
    the FinancialDataCollector, using Google's Gemini API.
    """

    def __init__(self, gemini_api_key=None, data_dir="financial_data"):
        """
        Initialize the AI agent with necessary API keys and data directories.

        Args:
            gemini_api_key (str, optional): Google Gemini API key for AI capabilities.
                If not provided, will try to get from environment variable.
            data_dir (str): Directory where financial data is stored
        """
        # Load environment variables
        load_dotenv()

        # Set up the Gemini API key
        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("Gemini API key is required. Provide as parameter or set GEMINI_API_KEY environment variable.")

        # Initialize Gemini
        genai.configure(api_key=self.gemini_api_key)

        # Create a generation config for more consistent responses
        self.generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

        # Set up the Gemini model
        # self.model = genai.GenerativeModel(
        #     model_name="gemini-pro",
        #     generation_config=self.generation_config
        # )

        # # Option 1: Try with the new API version model name
        # self.model = genai.GenerativeModel(
        # model_name="models/gemini-pro",  # Add "models/" prefix
        # generation_config=self.generation_config
        # )

        # # Option 2: Use the latest 1.0 model
        # self.model = genai.GenerativeModel(
        #     model_name="gemini-1.0-pro",  # Try this model name
        #     generation_config=self.generation_config
        # )

        # Option 3: Use gemini-1.5-pro if available
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",  # Try this model name
            generation_config=self.generation_config
        )

        # Set up data directories
        self.data_dir = data_dir
        self.prices_dir = f"{self.data_dir}/prices"
        self.historical_dir = f"{self.data_dir}/historical"
        self.company_news_dir = f"{self.data_dir}/company_news"
        self.articles_dir = f"{self.data_dir}/articles"
        self.financials_dir = f"{self.data_dir}/financials"

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("financial_ai_agent.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Initialize the data collector for fresh data if needed
        self.collector = None  # Will be initialized on demand

    def initialize_collector(self, fmp_api_key=None, finnhub_api_key=None):
        """
        Initialize the FinancialDataCollector if needed.

        Args:
            fmp_api_key (str, optional): API key for Financial Modeling Prep API
            finnhub_api_key (str, optional): API key for Finnhub API
        """
        if self.collector is None:
            self.logger.info("Initializing FinancialDataCollector")
            self.collector = FinancialDataCollector(fmp_api_key, finnhub_api_key)

    def get_latest_data_file(self, directory: str, symbol: Optional[str] = None, file_type: str = ".csv") -> Optional[str]:
        """
        Find the most recent data file in the specified directory.

        Args:
            directory (str): Directory to search in
            symbol (str, optional): Stock symbol to filter by
            file_type (str): File extension to filter by

        Returns:
            str or None: Path to the most recent file, or None if no files found
        """
        if symbol:
            pattern = f"{directory}/{symbol}_*{file_type}"
        else:
            pattern = f"{directory}/*{file_type}"

        files = glob.glob(pattern)
        if not files:
            return None

        # Sort files by modification time, most recent first
        files.sort(key=os.path.getmtime, reverse=True)
        return files[0]

    def get_latest_stock_prices(self, symbols: List[str] = None) -> Optional[pd.DataFrame]:
        """
        Get the most recent stock price data.

        Args:
            symbols (list, optional): List of stock symbols to filter by

        Returns:
            DataFrame or None: Most recent stock price data, or None if not found
        """
        latest_file = self.get_latest_data_file(self.prices_dir)
        if not latest_file:
            self.logger.warning("No stock price data found")
            return None

        try:
            df = pd.read_csv(latest_file)

            # Filter by symbols if provided
            if symbols:
                df = df[df['symbol'].isin(symbols)]

            return df
        except Exception as e:
            self.logger.error(f"Error reading stock price data: {e}")
            return None

    def get_historical_prices(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get historical price data for a specific symbol.

        Args:
            symbol (str): Stock symbol to get historical data for

        Returns:
            DataFrame or None: Historical price data, or None if not found
        """
        latest_file = self.get_latest_data_file(self.historical_dir, symbol)
        if not latest_file:
            self.logger.warning(f"No historical data found for {symbol}")
            return None

        try:
            return pd.read_csv(latest_file)
        except Exception as e:
            self.logger.error(f"Error reading historical data for {symbol}: {e}")
            return None

    def get_latest_news(self, symbol: str = None) -> Optional[pd.DataFrame]:
        """
        Get the most recent news articles.

        Args:
            symbol (str, optional): Stock symbol to filter news by

        Returns:
            DataFrame or None: News articles, or None if not found
        """
        if symbol:
            latest_file = self.get_latest_data_file(self.company_news_dir, symbol)
        else:
            latest_file = self.get_latest_data_file(self.articles_dir)

        if not latest_file:
            self.logger.warning(f"No news articles found{' for ' + symbol if symbol else ''}")
            return None

        try:
            return pd.read_csv(latest_file)
        except Exception as e:
            self.logger.error(f"Error reading news articles: {e}")
            return None

    def get_company_financials(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get financial metrics for a specific company.

        Args:
            symbol (str): Stock symbol to get financials for

        Returns:
            DataFrame or None: Financial metrics, or None if not found
        """
        latest_file = self.get_latest_data_file(self.financials_dir, symbol)
        if not latest_file:
            self.logger.warning(f"No financial data found for {symbol}")
            return None

        try:
            return pd.read_csv(latest_file)
        except Exception as e:
            self.logger.error(f"Error reading financial data for {symbol}: {e}")
            return None

    def collect_fresh_data(self, symbols: List[str], collect_news: bool = True,
                       collect_financials: bool = True, collect_historical: bool = True):
        """
        Collect fresh data for specified symbols.

        Args:
            symbols (list): List of stock symbols to collect data for
            collect_news (bool): Whether to collect news articles
            collect_financials (bool): Whether to collect financial metrics
            collect_historical (bool): Whether to collect historical prices

        Returns:
            None
        """
        self.initialize_collector()

        # Collect real-time quotes
        self.collector.get_stock_quotes(symbols)

        if collect_news:
            # Get general articles
            self.collector.get_fmp_articles()

            # Get company-specific news
            from_date = (datetime.now().replace(day=1)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')

            for symbol in symbols:
                self.collector.get_company_news(symbol, from_date, to_date)

        if collect_financials:
            for symbol in symbols:
                self.collector.get_basic_financials(symbol)

        if collect_historical:
            for symbol in symbols:
                self.collector.get_historical_prices(symbol)

    def query_ai_with_context(self, query: str, context_data: Union[pd.DataFrame, List[Dict], str]) -> str:
        """
        Query Google's Gemini AI with provided context data.

        Args:
            query (str): The question to ask the AI
            context_data: Data to provide as context (DataFrame, list, or string)

        Returns:
            str: AI's response to the query
        """
        # Convert context_data to string if it's not already
        if isinstance(context_data, pd.DataFrame):
            context = context_data.to_string(index=False)
        elif isinstance(context_data, list):
            context = json.dumps(context_data, indent=2)
        else:
            context = str(context_data)

        try:
            # Create the prompt for Gemini
            prompt = f"""You are a helpful financial analysis assistant. You analyze financial data and provide insights based on the given context.

            Context data:
            {context}

            Question: {query}

            Provide a thorough analysis based on the financial data. If exact values are mentioned, make sure they match the context data.
            """

            # Generate a response from Gemini
            response = self.model.generate_content(prompt)

            # Return the AI's response
            return response.text
        except Exception as e:
            self.logger.error(f"Error querying Gemini AI: {e}")
            return f"Error querying Gemini AI: {e}"

    def answer_financial_question(self, query: str, symbols: List[str] = None,
                               collect_fresh: bool = False) -> str:
        """
        Answer a financial question using the most relevant data.

        Args:
            query (str): The financial question to answer
            symbols (list, optional): Stock symbols relevant to the question
            collect_fresh (bool): Whether to collect fresh data before answering

        Returns:
            str: AI's answer to the question
        """
        self.logger.info(f"Processing question: {query}")

        # Collect fresh data if requested
        if collect_fresh and symbols:
            self.logger.info(f"Collecting fresh data for symbols: {symbols}")
            self.collect_fresh_data(symbols)

        # Determine the type of question to select appropriate data
        question_lower = query.lower()

        # Initialize context data as a string
        context_data = "No relevant data found for your question."

        # Check for price-related questions
        if any(term in question_lower for term in ['price', 'stock', 'quote', 'market', 'trading']):
            if symbols:
                # Get specific stock prices
                prices_df = self.get_latest_stock_prices(symbols)
                if prices_df is not None and not prices_df.empty:
                    context_data = prices_df

                # Add historical data for trend analysis
                if 'trend' in question_lower or 'historical' in question_lower:
                    historical_data = {}
                    for symbol in symbols:
                        hist_df = self.get_historical_prices(symbol)
                        if hist_df is not None and not hist_df.empty:
                            historical_data[symbol] = hist_df

                    if historical_data:  # Check if the dictionary is not empty
                        if isinstance(context_data, str):
                            context_data = f"Historical price data for {', '.join(symbols)}:\n"
                        else:
                            context_data = context_data.to_string(index=False) + f"\n\nHistorical price data for {', '.join(symbols)}:\n"

                        for symbol, data in historical_data.items():
                            context_data += f"\n{symbol}:\n{data.tail(30).to_string(index=False)}"
            else:
                # Get all available stock prices
                prices_df = self.get_latest_stock_prices()
                if prices_df is not None and not prices_df.empty:
                    context_data = prices_df

        # Check for news-related questions
        elif any(term in question_lower for term in ['news', 'article', 'announcement', 'press']):
            if symbols and len(symbols) == 1:
                # Get news for a specific symbol
                news_df = self.get_latest_news(symbols[0])
                if news_df is not None and not news_df.empty:
                    context_data = news_df
            else:
                # Get general financial news
                news_df = self.get_latest_news()
                if news_df is not None and not news_df.empty:
                    context_data = news_df

        # Check for financial metrics questions
        elif any(term in question_lower for term in ['financial', 'metric', 'ratio', 'earnings', 'revenue']):
            if symbols and len(symbols) == 1:
                # Get financials for a specific symbol
                financials_df = self.get_company_financials(symbols[0])
                if financials_df is not None and not financials_df.empty:
                    context_data = financials_df
            elif symbols:
                # Compile financials for multiple symbols
                all_financials = []
                for symbol in symbols:
                    fin_df = self.get_company_financials(symbol)
                    if fin_df is not None and not fin_df.empty:
                        all_financials.append((symbol, fin_df))

                if all_financials:  # Check if the list is not empty
                    context_data = f"Financial data for {', '.join(symbols)}:\n"
                    for symbol, data in all_financials:
                        context_data += f"\n{symbol}:\n{data.to_string(index=False)}"

        # If we couldn't determine the context, try to use stock prices as default
        if isinstance(context_data, str) and context_data == "No relevant data found for your question.":
            prices_df = self.get_latest_stock_prices(symbols)
            if prices_df is not None and not prices_df.empty:
                context_data = prices_df

        # If we still don't have meaningful context data, inform the user
        if isinstance(context_data, str) and context_data == "No relevant data found for your question.":
            return "I'm sorry, but I couldn't find any relevant data to answer your question. Please try asking about different symbols or collect fresh data first."

        # Query the AI with the context data
        self.logger.info("Querying AI with context data")
        answer = self.query_ai_with_context(query, context_data)

        return answer


# Example usage
if __name__ == "__main__":
    # Example setup for Google Colab
    import os

    # Option 1: Set environment variables directly
    os.environ['GEMINI_API_KEY'] = 'AIzaSyAWyzXBL1Hh6uULC-jWKAq7OhPf4vhYuSw'
    os.environ['FMP_API_KEY'] = '6tWB631QB6x2pcmnl19TgM2hyZeZTOa9'
    os.environ['FINNHUB_API_KEY'] = 'cucvf71r01qri16oti9gcucvf71r01qri16otia0'

    # Create the AI agent
    agent = FinancialAIAgent()

    # Example: Answer financial questions
    # symbols_of_interest = ["AAPL", "MSFT", "GOOGL"]
    symbols_to_track = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "INTC", "IBM", "WMT", "TGT", "COST", "NKE", "PEP", "KO", "TGT", "AMD", "JPM", "BAC", "V", "MA", "GS", "GE", "CAT", "BA", "F", "GM"]

    agent.collect_fresh_data(symbols_to_track)

    # question = "What is the current price of Coca-Cola stock?"
    # print(f"\nQuestion: {question}")
    # print(f"Answer: {answer}")

    question = "What is the current price of Amazon stock?"
    answer = agent.answer_financial_question(question, symbols=["AMZN"])
    print(f"\nQuestion: {question}")
    print(f"Answer: {answer}")