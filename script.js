async function checkScam() {   // ✅ FIXED (async)
    const text = document.getElementById("message").value.trim();

    if (!text) {
        showResult('Please enter text to analyze.', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });

        if (!response.ok) throw new Error('API error');

        const data = await response.json();

        applyResult(data.result, data.confidence, data.reasons);

        // ✅ SAVE TO DB
        await saveToDatabase(text, data.result);

    } catch (err) {
        const local = analyzeScamText(text);
        applyResult(local.result, local.confidence, local.reasons);

        // ✅ SAVE EVEN IF API FAILS
        await saveToDatabase(text, local.result);
    }
}

function analyzeScamText(text) {
    const normalized = text.toLowerCase();
    let score = 0;
    let reasons = [];

    if (/https?:\/\//.test(normalized)) {
        score += 3;
        reasons.push("Contains suspicious link");
    }

    const words = ['urgent','password','otp','winner','lottery','bank'];
    words.forEach(word => {
        if (normalized.includes(word)) {
            score += 2;
            reasons.push(`Suspicious word: ${word}`);
        }
    });

    let result = 'safe';
    let confidence = 90;

    if (score >= 6) {
        result = 'scam';
        confidence = 85;
    } else if (score >= 3) {
        result = 'warning';
        confidence = 70;
    }

    return { result, confidence, reasons };
}

function applyResult(result, confidence = 0, reasons = []) {
    let message = '';

    if (result.toLowerCase() === 'scam') {
        message = `⚠ Scam Detected (${confidence}%)`;
    } else if (result.toLowerCase() === 'warning') {
        message = `⚠ Potential Scam (${confidence}%)`;
    } else {
        message = `✅ Safe Message (${confidence}%)`;
    }

    if (reasons.length > 0) {
        message += '\n\n' + reasons.join('\n');
    }

    showResult(message, result);
}

function showResult(text, status) {
    const box = document.getElementById('result');
    box.style.display = 'block';
    box.innerText = text;
}

async function saveToDatabase(message, result) {
    console.log("🔥 Sending to backend:", message, result);   // ✅ DEBUG

    try {
        const response = await fetch('/api/check_results', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                result: result
            })
        });

        const data = await response.json();
        console.log("✅ Saved:", data);   // ✅ DEBUG

    } catch (err) {
        console.error("❌ Error saving:", err);
    }
}