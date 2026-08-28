import gspread

import os
import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from bot.sheets import get_client, get_sheet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='dashboard')
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory('dashboard', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('dashboard', path)

@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        client = get_client()
        if not client:
            return jsonify({"error": "Failed to authenticate with Google Sheets. Check service account credentials."}), 500

        sheet = get_sheet(client)
        if not sheet:
            return jsonify({"error": "Failed to open Google Sheet. Check SHEET_ID and permissions."}), 500

        data = {}
        tabs = ['Equity', 'Positions', 'Trades', 'Watchlist']

        for tab_name in tabs:
            try:
                ws = sheet.worksheet(tab_name)
                # get_all_records() returns a list of dicts mapped by the header row.
                # Since all fields are parsed as strings by the frontend, this works perfectly.
                records = ws.get_all_records()
                data[tab_name.lower()] = records

            except gspread.exceptions.WorksheetNotFound:
                return jsonify({"error": f"Worksheet '{tab_name}' not found."}), 404
            except Exception as e:
                logger.error(f"Error reading tab {tab_name}: {e}")
                return jsonify({"error": f"Error reading tab '{tab_name}': {str(e)}"}), 500

        return jsonify(data), 200

    except Exception as e:
        logger.error(f"Unexpected error in /api/data: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
