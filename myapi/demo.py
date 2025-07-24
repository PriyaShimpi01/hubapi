# demo.py
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_KEY = 'd1u80dhr01qp7ee2794gd1u80dhr01qp7ee27950'
BASE_URL = 'https://finnhub.io/api/v1'

@app.route('/company-info', methods=['GET'])
def get_company_info():
    company_query = request.args.get('company')
    if not company_query:
        return jsonify({'error': 'Missing company parameter'}), 400

    # Search for the ticker symbol
    search_url = f'{BASE_URL}/search'
    search_params = {'q': company_query, 'token': API_KEY}
    search_resp = requests.get(search_url, params=search_params).json()

    if not search_resp.get('count', 0):
        return jsonify({'error': f'No results found for company: {company_query}'}), 404

    first_match = search_resp['result'][0]
    symbol = first_match['symbol']

    # Get company profile
    profile_url = f'{BASE_URL}/stock/profile2'
    profile_params = {'symbol': symbol, 'token': API_KEY}
    profile_resp = requests.get(profile_url, params=profile_params).json()

    if not profile_resp or 'name' not in profile_resp:
        return jsonify({'error': f'No profile found for: {symbol}'}), 404

    # Extract profile details
    company_name = profile_resp.get('name', 'N/A')
    country = profile_resp.get('country', 'N/A')
    industry = profile_resp.get('finnhubIndustry', 'N/A')
    market_cap = profile_resp.get('marketCapitalization', 'N/A')

    # Get revenue
    financials_url = f'{BASE_URL}/stock/financials-reported'
    financials_params = {'symbol': symbol, 'token': API_KEY}
    financials_resp = requests.get(financials_url, params=financials_params).json()

    revenue = 'N/A'
    try:
        reports = financials_resp.get('data', [])
        if reports:
            latest_report = reports[0]
            for item in latest_report['report']['ic']:
                if item['concept'] == 'Revenues':
                    revenue = item['value']
                    break
    except Exception as e:
        revenue = f'Error: {e}'

    return jsonify({
        'company_name': company_name,
        'country': country,
        'industry': industry,
        'market_cap_million_usd': market_cap,
        'revenue_latest': revenue
    })

if __name__ == '__main__':
    app.run(debug=True)
