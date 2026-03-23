async function checkScam() {
    const text = document.getElementById("message").value.trim();
    const resultBox = document.getElementById("result");

    if (!text) {
        showResult('Please enter text to analyze.', 'warning');
        return;
    }

    try {
        // Use API endpoint if available, otherwise fallback to local heuristic check
        const response = await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });

        if (!response.ok) {
            throw new Error('API unavailable');
        }

        const data = await response.json();
        applyResult(data.result, data.confidence || 0, data.reasons || []);
        // Save to database
        saveToDatabase(text, data.result);
    } catch (err) {
        // Fallback heuristic analysis
        const local = analyzeScamText(text);
        applyResult(local.result, local.confidence, local.reasons);
        // Save to database
        saveToDatabase(text, local.result);
    }
}

function analyzeScamText(text) {
    const normalized = text.toLowerCase();
    let score = 0;
    let reasons = [];

    // Check for suspicious links
    const hasLink = /https?:\/\//.test(normalized);
    if (hasLink) {
        score += 3;
        reasons.push("Contains a link - always verify links before clicking");
    }

    // Check for urgent language
    const urgentWords = ['urgent', 'immediate', 'action required', 'act now', 'limited time', 'expires soon', 'time sensitive'];
    urgentWords.forEach(word => {
        if (normalized.includes(word)) {
            score += 2;
            reasons.push(`Uses urgent language: "${word}"`);
        }
    });

    // Check for requests for personal information
    const personalInfoWords = ['password', 'otp', 'one-time password', 'pin', 'social security', 'ssn', 'credit card', 'bank account', 'login', 'verify your account'];
    personalInfoWords.forEach(word => {
        if (normalized.includes(word)) {
            score += 3;
            reasons.push(`Asks for personal information: "${word}"`);
        }
    });

    // Check for financial incentives
    const financialWords = ['prize', 'winner', 'congratulations', 'free money', 'inheritance', 'lottery', 'refund', 'compensation', 'transfer funds', 'send money'];
    financialWords.forEach(word => {
        if (normalized.includes(word)) {
            score += 2;
            reasons.push(`Promises money or prizes: "${word}"`);
        }
    });

    // Check for threats
    const threatWords = ['account suspended', 'account closed', 'legal action', 'debt', 'billing issue', 'security breach'];
    threatWords.forEach(word => {
        if (normalized.includes(word)) {
            score += 3;
            reasons.push(`Contains threats: "${word}"`);
        }
    });

    // Check for impersonation
    const impersonationWords = ['from bank', 'from government', 'from microsoft', 'from amazon', 'official notice', 'support team'];
    impersonationWords.forEach(word => {
        if (normalized.includes(word)) {
            score += 2;
            reasons.push(`Claims to be from official source: "${word}"`);
        }
    });

    // Determine result based on score
    let result;
    let confidence;
    if (score >= 8) {
        result = 'scam';
        confidence = Math.min(95, 70 + score * 2);
    } else if (score >= 4) {
        result = 'warning';
        confidence = Math.min(80, 50 + score * 3);
    } else {
        result = 'safe';
        confidence = Math.max(60, 100 - score * 5);
    }

    return { result, confidence, reasons };
}

function applyResult(result, confidence=0, reasons=[]) {
    const resultBox = document.getElementById('result');
    let message = '';
    let status = '';

    if (result === 'scam') {
        message = `⚠ Scam Detected (confidence)`;
        status = 'scam';
    } else if (result === 'warning') {
        message = `⚠ Potential Scam (confidence)`;
        status = 'warning';
    } else {
        message = `✅ Message seems safe (confidence)`;
        status = 'safe';
    }

    if (reasons.length > 0) {
        message += '\n\nWhy this was flagged:\n' + reasons.map(reason => '• ' + reason).join('\n');
    }

    showResult(message, status);
}

function showResult(text, status) {
    const resultBox = document.getElementById('result');
    resultBox.style.display = 'block';
    resultBox.textContent = text;
    resultBox.className = `result-box result ${status}`;
}

async function saveToDatabase(message, result) {
    try {
        await fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, result })
        });
        console.log('Result saved to database');
    } catch (err) {
        console.error('Failed to save to database:', err);
    }
}