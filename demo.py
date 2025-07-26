from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = 'd1u80dhr01qp7ee2794gd1u80dhr01qp7ee27950'
BASE_URL = 'https://finnhub.io/api/v1'


@app.route('/')
def home():
    return "Welcome to the Company Info API! Use /company-info?company=YourCompanyName"

@app.route('/test')
def test():
    return "✅ Flask is working!"

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

@app.route('/competitor-analysis', methods=['GET'])
def competitor_analysis():
    company = request.args.get('company')
    location = request.args.get('location')
    industry = request.args.get('industry')
    try:
        market_cap = float(request.args.get('market_cap'))
    except:
        return jsonify({'error': 'Invalid revenue or market_cap'}), 400

    if not company or not industry or not location:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Step 1: Get symbol
    search_resp = requests.get(f"{BASE_URL}/search", params={'q': company, 'token': API_KEY}).json()
    if not search_resp.get('count'):
        return jsonify({'error': 'Company not found'}), 404
    symbol = search_resp['result'][0]['symbol']

    # Step 2: Get peers
    peers_resp = requests.get(f"{BASE_URL}/stock/peers", params={'symbol': symbol, 'token': API_KEY}).json()
    if not isinstance(peers_resp, list):
        return jsonify({'error': 'Peers not found'}), 404

    matches = []

    for peer in peers_resp:
        try:
            profile = requests.get(f"{BASE_URL}/stock/profile2", params={'symbol': peer, 'token': API_KEY}).json()
            financials = requests.get(f"{BASE_URL}/stock/financials-reported", params={'symbol': peer, 'token': API_KEY}).json()
            
            peer_revenue = None
            reports = financials.get('data', [])
            if reports:
                for item in reports[0]['report']['ic']:
                    if item['concept'] == 'Revenues':
                        peer_revenue = float(item['value'])
                        break

            if not profile.get('name') or not peer_revenue:
                continue

            peer_country = profile.get('country', '')
            peer_industry = profile.get('finnhubIndustry', '')
            peer_market_cap = profile.get('marketCapitalization', 0)

            # Filter logic: within ±20% of revenue & market cap, matching location and industry
            if (peer_country.lower() == location.lower() and
                peer_industry.lower() == industry.lower() and
                abs(peer_revenue - revenue) / revenue <= 0.2 and
                abs(peer_market_cap - market_cap) / market_cap <= 0.2):

                matches.append({
                    'symbol': peer,
                    'name': profile.get('name', 'N/A'),
                    'country': peer_country,
                    'industry': peer_industry,
                    'revenue': peer_revenue,
                    'market_cap': peer_market_cap
                })

        except:
            continue

        if len(matches) >= 4:
            break

    if not matches:
        return jsonify({'message': 'No matching competitors found'}), 404

    return jsonify({'matches': matches})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
