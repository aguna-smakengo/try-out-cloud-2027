import json
import os

def generate():
    with open('database.json', 'r') as f:
        data = json.load(f)
    
    # Sort by percentage descending
    data.sort(key=lambda x: float(x['percentage']), reverse=True)

    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Infrastructure Leaderboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --secondary: #a855f7;
            --bg: #0f172a;
            --card: #1e293b;
            --text: #f8fafc;
            --success: #22c55e;
            --danger: #ef4444;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        body {
            background-color: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 3rem;
            animation: fadeInDown 0.8s ease-out;
        }

        h1 {
            font-size: 2.5rem;
            background: linear-gradient(to right, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        .leaderboard {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .student-card {
            background: var(--card);
            border-radius: 1rem;
            padding: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.05);
            animation: fadeInUp 0.5s ease-out backwards;
        }

        .student-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
            border-color: var(--primary);
        }

        .rank {
            font-size: 1.5rem;
            font-weight: 700;
            width: 50px;
            color: rgba(255,255,255,0.3);
        }

        .info {
            flex-grow: 1;
        }

        .name {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }

        .stats {
            font-size: 0.9rem;
            color: rgba(255,255,255,0.6);
        }

        .score-box {
            text-align: right;
        }

        .percentage {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
        }

        .raw-score {
            font-size: 0.8rem;
            color: rgba(255,255,255,0.4);
        }

        /* Rank Colors */
        .card-0 .rank { color: #ffd700; } /* Gold */
        .card-1 .rank { color: #c0c0c0; } /* Silver */
        .card-2 .rank { color: #cd7f32; } /* Bronze */

        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Modal / Details */
        #detailsModal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(8px);
            z-index: 1000;
            padding: 2rem;
            overflow-y: auto;
        }

        .modal-content {
            background: var(--card);
            max-width: 900px;
            margin: 0 auto;
            border-radius: 1.5rem;
            padding: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 1rem;
        }

        .close-btn {
            background: none;
            border: none;
            color: white;
            font-size: 2rem;
            cursor: pointer;
        }

        .result-item {
            padding: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 2rem;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .status-PASS { background: rgba(34, 197, 94, 0.2); color: #4ade80; }
        .status-FAIL { background: rgba(239, 68, 68, 0.2); color: #f87171; }

        .feedback {
            font-size: 0.85rem;
            color: rgba(255,255,255,0.5);
            margin-top: 0.25rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Infrastructure Leaderboard</h1>
            <p>Cloud Computing Final Project Results</p>
        </header>

        <div class="leaderboard" id="leaderboard">
            <!-- Injected by JS -->
        </div>
    </div>

    <div id="detailsModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalName">Student Name</h2>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div id="modalResults"></div>
        </div>
    </div>

    <script>
        const students = """ + json.dumps(data) + """;

        function renderLeaderboard() {
            const container = document.getElementById('leaderboard');
            container.innerHTML = students.map((s, i) => `
                <div class="student-card card-${i}" onclick="showDetails(${i})" style="animation-delay: ${i * 0.1}s">
                    <div class="rank">#${i + 1}</div>
                    <div class="info">
                        <div class="name">${s.name}</div>
                        <div class="stats">Evaluated at: ${new Date().toLocaleDateString()}</div>
                    </div>
                    <div class="score-box">
                        <div class="percentage">${s.percentage}%</div>
                        <div class="raw-score">${s.total_score} / ${s.max_score} Points</div>
                    </div>
                </div>
            `).join('');
        }

        function showDetails(index) {
            const s = students[index];
            document.getElementById('modalName').innerText = s.name + " - Results";
            document.getElementById('modalResults').innerHTML = s.results.map(r => `
                <div class="result-item">
                    <div>
                        <div style="font-weight: 600; font-size: 0.95rem;">${r.Category}</div>
                        <div style="font-size: 0.85rem; color: rgba(255,255,255,0.7)">${r.Item}</div>
                        <div class="feedback">${r.Feedback}</div>
                    </div>
                    <div class="status-badge status-${r.Status}">${r.Status}</div>
                </div>
            `).join('');
            document.getElementById('detailsModal').style.display = 'block';
        }

        function closeModal() {
            document.getElementById('detailsModal').style.display = 'none';
        }

        renderLeaderboard();
    </script>
</body>
</html>
"""
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    print("index.html generated successfully!")

if __name__ == "__main__":
    generate()
