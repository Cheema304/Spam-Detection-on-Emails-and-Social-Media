from .security import esc


def layout(title, heading, body, active="dashboard"):
    nav = [
        ("dashboard", "/", "Dashboard"),
        ("detect", "/detect", "Detect Spam"),
        ("history", "/history", "History"),
        ("analytics", "/analytics", "Analytics"),
        ("models", "/models", "Model Lab"),
        ("about", "/about", "Architecture"),
    ]
    nav_html = "".join(
        f'<a class="nav-link {"active" if key==active else ""}" href="{url}">{label}</a>'
        for key, url, label in nav
    )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · SpamShield AI</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="app-shell">
<aside class="sidebar">
  <a href="/" class="brand"><span class="brand-mark">S</span><span><strong>SpamShield</strong><small>AI Security</small></span></a>
  <nav>{nav_html}</nav>
  <div class="side-status"><span class="pulse"></span><div><b>Engine Online</b><small>Local inference</small></div></div>
  <div class="course-tag"><b>ICT942</b><small>Cyber Security Project</small></div>
</aside>
<main class="main">
<header class="topbar"><div><p class="eyebrow">EMAIL + SOCIAL MEDIA DEFENCE</p><h1>{esc(heading)}</h1></div><a class="button primary" href="/detect">New Analysis</a></header>
{body}
<footer><span>SpamShield AI · Academic Prototype</span><span>Local-first · No message content executed</span></footer>
</main></div>
<script src="/static/app.js"></script>
</body></html>'''


def dashboard(stats, recent, metadata):
    s = stats["summary"]
    total = int(s["total"] or 0); spam = int(s["spam"] or 0); ham = int(s["ham"] or 0)
    avg_ms = float(s["avg_ms"] or 0)
    recent_html = ""
    if recent:
        for r in recent:
            cls = "danger" if r["prediction"] == "Spam" else "safe"
            recent_html += f'''<div class="activity-row">
              <span class="status {cls}">{esc(r["prediction"])}</span>
              <div class="activity-copy"><b>{esc(r["source_type"])}</b><small>{esc(r["raw_text"][:95])}{'…' if len(r['raw_text'])>95 else ''}</small></div>
              <div class="metric-end"><b>{float(r['spam_probability']):.1f}%</b><small>spam risk</small></div>
            </div>'''
    else:
        recent_html = '<div class="empty-state"><div class="empty-icon">◎</div><b>No analyses yet</b><span>Run your first message through the classifier.</span></div>'
    active = f"{metadata.get('active_vectorizer','')} + {metadata.get('active_model','')}"
    body = f'''
<section class="hero panel">
  <div class="hero-copy"><span class="badge">REAL PUBLIC DATA · LIVE MODEL · NLP</span>
  <h2>Detect suspicious messages before they become a security incident.</h2>
  <p>Analyse email and social-media text in real time. The active classifier is selected from eight evaluated pipelines trained on downloaded public Email and YouTube spam datasets. Every benchmark is recalculated when the project is retrained.</p>
  <div class="button-row"><a class="button primary large" href="/detect">Analyse a message</a><a class="button secondary large" href="/models">Inspect live evaluation</a></div></div>
  <div class="shield-wrap"><div class="shield"><span>✓</span></div><div class="model-label"><b>{esc(metadata.get('active_model','Model'))}</b><small>{esc(metadata.get('active_vectorizer','Vectorizer'))}</small></div></div>
</section>
<section class="stats-grid">
  <article class="stat panel"><span>Total Analyses</span><strong>{total}</strong><small>Auditable predictions</small></article>
  <article class="stat panel"><span>Spam Detected</span><strong>{spam}</strong><small>Potentially unwanted</small></article>
  <article class="stat panel"><span>Legitimate</span><strong>{ham}</strong><small>Not-spam predictions</small></article>
  <article class="stat panel"><span>Avg. Inference</span><strong>{avg_ms:.1f}<em> ms</em></strong><small>Application processing</small></article>
</section>
<section class="two-col">
  <article class="panel"><div class="section-title"><div><p class="eyebrow">RECENT ACTIVITY</p><h3>Latest classifications</h3></div><a href="/history">View history →</a></div>{recent_html}</article>
  <article class="panel"><p class="eyebrow">ACTIVE DETECTION PIPELINE</p><h3>{esc(active)}</h3>
    <div class="pipeline">
      <div><span>01</span><p><b>Input</b><small>Email, comment, post or DM text</small></p></div>
      <div><span>02</span><p><b>Secure preprocessing</b><small>URL/email/currency tokens + normalisation</small></p></div>
      <div><span>03</span><p><b>Feature extraction</b><small>{esc(metadata.get('active_vectorizer',''))} n-grams</small></p></div>
      <div><span>04</span><p><b>Classification</b><small>{esc(metadata.get('active_model',''))} · probability + risk</small></p></div>
    </div>
  </article>
</section>'''
    return layout("Dashboard", "Security Overview", body, "dashboard")

def detect(result=None, error="", message="", source="Email"):
    error_html = f'<div class="alert">{esc(error)}</div>' if error else ""
    result_html = '''<div class="result-empty"><div class="radar"></div><h3>Ready to analyse</h3><p>Submit a message to calculate classification, confidence, spam probability, risk level and indicative signal terms.</p></div>'''
    if result:
        danger = result["prediction"] == "Spam"
        cls = "danger-result" if danger else "safe-result"
        signals = "".join(f'<span class="signal">{esc(x)}</span>' for x in result.get("signals", [])) or '<span class="muted">No strong spam-indicative terms identified.</span>'
        result_html = f'''<div class="prediction {cls}">
          <div class="prediction-icon">{'!' if danger else '✓'}</div>
          <p class="eyebrow">PREDICTION</p><h2>{esc(result['prediction'])}</h2>
          <div class="risk-gauge" style="--risk:{float(result['spam_probability']) * 3.6}deg"><div><strong>{float(result['spam_probability']):.1f}%</strong><small>spam probability</small></div></div>
          <div class="result-pills"><span>Confidence <b>{float(result['confidence']):.1f}%</b></span><span>Risk <b>{esc(result['risk_level'])}</b></span><span>Time <b>{float(result['processing_ms']):.1f} ms</b></span></div>
        </div>
        <div class="explain-box"><div class="section-title"><div><p class="eyebrow">EXPLAINABILITY</p><h3>Spam-indicative signal terms</h3></div></div><div class="signals">{signals}</div><p class="hint">Signals are model feature contributions, not a definitive security diagnosis.</p></div>
        <details class="details"><summary>View preprocessed text</summary><code>{esc(result['cleaned_text'])}</code></details>'''
    body = f'''<section class="detect-grid">
      <form class="panel form-panel" method="post" action="/detect">
        <p class="eyebrow">REAL-TIME CLASSIFIER</p><h2>Analyse Message Content</h2>{error_html}
        <label>Source channel</label><div class="segmented">
          <label><input type="radio" name="source_type" value="Email" {'checked' if source=='Email' else ''}><span>Email</span></label>
          <label><input type="radio" name="source_type" value="Social Media" {'checked' if source=='Social Media' else ''}><span>Social Media</span></label>
        </div>
        <label for="message">Message text</label><textarea id="message" name="message" maxlength="8000" rows="15" placeholder="Paste an email, post, comment or direct message here…">{esc(message)}</textarea>
        <div class="form-meta"><span id="char-count">0 / 8,000 characters</span><span>Content is treated as inert text</span></div>
        <button class="button primary full large" type="submit">Run Spam Analysis</button>
      </form>
      <article class="panel result-panel"><p class="eyebrow">ANALYSIS RESULT</p>{result_html}</article>
    </section>'''
    return layout("Detect", "Message Analysis", body, "detect")


def history(rows, query="", label="", source=""):
    table = ""
    for r in rows:
        cls = "danger" if r["prediction"] == "Spam" else "safe"
        table += f'''<tr><td>#{r['id']}</td><td>{esc(r['source_type'])}</td><td class="message-cell">{esc(r['raw_text'])}</td>
        <td><span class="status {cls}">{esc(r['prediction'])}</span></td><td>{float(r['spam_probability']):.1f}%</td><td>{esc(r['risk_level'])}</td><td>{float(r['processing_ms']):.1f} ms</td><td>{esc(r['created_at'].replace('T',' ')[:19])}</td></tr>'''
    if not table:
        table = '<tr><td colspan="8" class="table-empty">No matching records.</td></tr>'
    body = f'''<section class="panel">
      <form class="filters" method="get" action="/history">
        <input name="q" value="{esc(query)}" placeholder="Search message content">
        <select name="label"><option value="">All results</option><option value="Spam" {'selected' if label=='Spam' else ''}>Spam</option><option value="Not Spam" {'selected' if label=='Not Spam' else ''}>Not Spam</option></select>
        <select name="source"><option value="">All channels</option><option value="Email" {'selected' if source=='Email' else ''}>Email</option><option value="Social Media" {'selected' if source=='Social Media' else ''}>Social Media</option><option value="API" {'selected' if source=='API' else ''}>API</option></select>
        <button class="button primary" type="submit">Filter</button><a class="button secondary" href="/history">Reset</a>
      </form>
      <div class="table-wrap"><table><thead><tr><th>ID</th><th>Source</th><th>Message</th><th>Result</th><th>Spam Risk</th><th>Risk</th><th>Time</th><th>Date</th></tr></thead><tbody>{table}</tbody></table></div>
    </section>'''
    return layout("History", "Prediction History", body, "history")


def analytics(stats, metadata):
    s=stats["summary"]
    version=esc(metadata.get("model_version",""))
    trained=esc(metadata.get("trained_at_utc","").replace("T"," ")[:19])
    body=f'''<section class="stats-grid">
      <article class="stat panel"><span>Predictions</span><strong>{int(s['total'] or 0)}</strong><small>Stored locally</small></article>
      <article class="stat panel"><span>Spam</span><strong>{int(s['spam'] or 0)}</strong><small>Detected cases</small></article>
      <article class="stat panel"><span>Not Spam</span><strong>{int(s['ham'] or 0)}</strong><small>Legitimate cases</small></article>
      <article class="stat panel"><span>Mean Spam Risk</span><strong>{float(s['avg_spam_probability'] or 0):.1f}<em>%</em></strong><small>Across stored predictions</small></article>
    </section>
    <section class="live-strip panel"><div><span class="live-dot"></span><b>LIVE EVALUATION</b><small>Model version {version} · trained {trained} UTC</small></div><a href="/models">Manage models →</a></section>
    <section class="chart-grid">
      <article class="panel chart-card"><div><p class="eyebrow">REAL DATA</p><h3>Dataset distribution by channel</h3></div><img src="/live-chart/dataset.svg" alt="Live real dataset distribution chart"></article>
      <article class="panel chart-card"><div><p class="eyebrow">MODEL PERFORMANCE</p><h3>F1 comparison — all 8 pipelines</h3></div><img src="/live-chart/model-comparison.svg" alt="Live model F1 comparison chart"></article>
      <article class="panel chart-card"><div><p class="eyebrow">HOLD-OUT METRICS</p><h3>Accuracy, precision, recall & F1</h3></div><img src="/live-chart/metrics.svg" alt="Live metric comparison chart"></article>
      <article class="panel chart-card"><div><p class="eyebrow">CLASSIFICATION ERRORS</p><h3>Active model confusion matrix</h3></div><img src="/live-chart/confusion.svg" alt="Live confusion matrix"></article>
      <article class="panel chart-card"><div><p class="eyebrow">DISCRIMINATION</p><h3>Active model ROC curve</h3></div><img src="/live-chart/roc.svg" alt="Live ROC curve"></article>
      <article class="panel chart-card"><div><p class="eyebrow">EMAIL VS SOCIAL</p><h3>Active model performance by channel</h3></div><img src="/live-chart/channels.svg" alt="Live Email versus Social Media model metrics"></article>
      <article class="panel chart-card wide-chart"><div><p class="eyebrow">LIVE USAGE</p><h3>Application predictions by channel</h3></div><img src="/live-chart/usage.svg" alt="Live application usage chart"></article>
    </section>
    <section class="panel"><p class="hint"><b>Live means computed from current project state:</b> evaluation charts are rendered from the latest saved hold-out results; confusion/ROC/channel charts follow whichever model is currently active; usage charts are rendered directly from the SQLite prediction database. Retraining updates the evaluation data and all charts automatically.</p></section>'''
    return layout("Analytics","Analytics & Live Visualisation",body,"analytics")

def models(evaluation, metadata, notice=""):
    rows=""
    for idx,r in enumerate(evaluation,1):
        active = r["key"] == metadata.get("active_key")
        best = r["key"] == metadata.get("best_key")
        badges = (" <span class=\"mini-badge\">ACTIVE</span>" if active else "") + (" <span class=\"mini-badge best-badge\">BEST</span>" if best else "")
        action = '<span class="muted">In use</span>' if active else f'''<form method="post" action="/models/activate" class="inline-form"><input type="hidden" name="key" value="{esc(r['key'])}"><button class="button tiny secondary" type="submit">Use model</button></form>'''
        rows += f'''<tr class="{'deployed-row' if active else ''}"><td>{idx}</td><td>{esc(r['vectorizer'])}</td><td>{esc(r['model'])}{badges}</td>
        <td>{r['accuracy']:.4f}</td><td>{r['precision']:.4f}</td><td>{r['recall']:.4f}</td><td><b>{r['f1']:.4f}</b></td><td>{r['roc_auc']:.4f}</td><td>{action}</td></tr>'''
    notice_html = f'<div class="success-note">{esc(notice)}</div>' if notice else ""
    trained = esc(metadata.get("trained_at_utc","").replace("T"," ")[:19])
    body=f'''{notice_html}<section class="model-hero panel"><div><p class="eyebrow">REAL-DATA EXPERIMENT</p><h2>Vectorisation + Classifier Benchmark</h2><p>All eight pipelines are trained and evaluated on the same source-and-class-stratified hold-out split. The highest-ranked model is selected automatically after retraining, but you can activate any evaluated model to use it for live predictions.</p><div class="button-row"><form method="post" action="/models/retrain"><button class="button primary" type="submit">Retrain all 8 models on real data</button></form><a class="button secondary" href="/analytics">Open live charts</a></div></div><div class="model-chip"><small>ACTIVE MODEL</small><b>{esc(metadata['active_vectorizer'])}</b><span>+</span><b>{esc(metadata['active_model'])}</b></div></section>
    <section class="panel"><div class="table-wrap"><table><thead><tr><th>#</th><th>Vectorizer</th><th>Classifier</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC AUC</th><th>Live model</th></tr></thead><tbody>{rows}</tbody></table></div></section>
    <section class="three-col"><article class="panel"><p class="eyebrow">REAL DATASET</p><h3>{int(metadata['dataset_rows']):,} labelled messages</h3><p class="muted">Email: {int(metadata['email_spam_rows']+metadata['email_ham_rows']):,} · Social Media: {int(metadata['social_spam_rows']+metadata['social_ham_rows']):,}<br>Spam: {int(metadata['spam_rows']):,} · Ham: {int(metadata['ham_rows']):,}</p></article>
    <article class="panel"><p class="eyebrow">REPRODUCIBILITY</p><h3>Stratified hold-out · seed 42</h3><p class="muted">Train: {int(metadata['train_rows']):,} · Test: {int(metadata['test_rows']):,}<br>Trained: {trained} UTC</p></article>
    <article class="panel real-panel"><p class="eyebrow">DATA PROVENANCE</p><h3>Official public datasets</h3><p class="muted">Email: Apache SpamAssassin Public Corpus<br>Social: UCI YouTube Spam Collection (DOI 10.24432/C58885, CC BY 4.0)</p></article></section>
    <section class="panel source-panel"><div><p class="eyebrow">DATA SOURCES</p><h3>Evaluation is not based on dummy screenshots or hard-coded metric values</h3><p class="muted">The project downloads labelled public data, builds the combined dataset locally, trains every pipeline, writes fresh metric JSON and renders the charts from those current values.</p></div><div class="source-links"><a class="button secondary" href="https://spamassassin.apache.org/old/publiccorpus/" target="_blank" rel="noreferrer">Apache corpus</a><a class="button secondary" href="https://archive.ics.uci.edu/dataset/380/youtube+spam+collection" target="_blank" rel="noreferrer">UCI YouTube corpus</a></div></section>'''
    return layout("Model Lab","Live Model Evaluation Lab",body,"models")

def about(metadata):
    body=f'''<section class="panel"><p class="eyebrow">SYSTEM DESIGN</p><h2>Spam Detection on Emails and Social Media</h2><p class="lead">A local-first cybersecurity system combining real public labelled datasets, NLP preprocessing, eight machine-learning pipelines, selectable live inference, SQLite persistence and dynamically rendered Matplotlib evaluation graphics.</p><img class="architecture-img" src="/static/charts/architecture.png" alt="SpamShield AI system architecture"></section>
    <section class="chart-grid project-charts"><article class="panel chart-card"><p class="eyebrow">PROJECT GOVERNANCE</p><h3>Weeks 1–5 delivery plan</h3><img src="/static/charts/assessment_timeline.png" alt="Assessment timeline"></article><article class="panel chart-card"><p class="eyebrow">RISK MANAGEMENT</p><h3>Project risk matrix</h3><img src="/static/charts/risk_matrix.png" alt="Project risk matrix"></article></section>
    <section class="three-col">
      <article class="panel"><p class="eyebrow">SECURITY CONTROLS</p><h3>Safe text handling</h3><ul class="feature-list"><li>Message input length limit</li><li>No embedded URL is opened</li><li>HTML output is escaped</li><li>Security response headers</li><li>Local SQLite persistence</li></ul></article>
      <article class="panel"><p class="eyebrow">MACHINE LEARNING</p><h3>8 evaluated pipelines</h3><ul class="feature-list"><li>Bag of Words + TF-IDF</li><li>Naive Bayes</li><li>Logistic Regression</li><li>Calibrated Linear SVM</li><li>Random Forest</li></ul></article>
      <article class="panel"><p class="eyebrow">REAL DATA</p><h3>Email + social text</h3><ul class="feature-list"><li>Apache SpamAssassin email corpus</li><li>UCI YouTube spam comments</li><li>Source-aware stratified split</li><li>Fresh evaluation after retraining</li><li>Live Matplotlib SVG charts</li></ul></article>
    </section>
    <section class="panel"><div class="section-title"><div><p class="eyebrow">API</p><h3>Machine-readable prediction endpoint</h3></div><span class="endpoint">POST /api/predict</span></div><pre><code>{{"text":"Congratulations! Claim your prize now.","source_type":"Email"}}</code></pre></section>'''
    return layout("Architecture","System Architecture",body,"about")
