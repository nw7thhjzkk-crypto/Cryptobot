const { google } = require('googleapis');

exports.handler = async function(event, context) {
    try {
        const credentialsStr = process.env.GOOGLE_SERVICE_ACCOUNT_JSON;
        const sheetId = process.env.GOOGLE_SHEET_ID;

        if (!credentialsStr || !sheetId) {
            return {
                statusCode: 500,
                body: JSON.stringify({ error: "Missing environment variables." })
            };
        }

        const credentials = JSON.parse(credentialsStr);

        const auth = new google.auth.GoogleAuth({
            credentials,
            scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
        });

        const sheets = google.sheets({ version: 'v4', auth });

        // Get Trades
        const tradesResponse = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: 'Trades!A:J',
        });

        // Get Equity
        const equityResponse = await sheets.spreadsheets.values.get({
            spreadsheetId: sheetId,
            range: 'Equity!A:D',
        });

        const tradesData = tradesResponse.data.values || [];
        const equityData = equityResponse.data.values || [];

        // Format to objects assuming first row is header
        const formatData = (data) => {
            if (data.length < 2) return [];
            const headers = data[0];
            return data.slice(1).map(row => {
                const obj = {};
                headers.forEach((header, index) => {
                    obj[header] = row[index] || '';
                });
                return obj;
            });
        };

        const trades = formatData(tradesData);
        const equity = formatData(equityData);

        // Return latest equity (last row)
        const latestEquity = equity.length > 0 ? equity[equity.length - 1] : null;

        return {
            statusCode: 200,
            headers: {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ trades: trades.reverse(), equity: latestEquity })
        };

    } catch (error) {
        console.error("Error fetching data:", error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: "Failed to fetch data from sheets." })
        };
    }
};