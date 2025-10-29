# EmailScope

A free, open-source tool that finds and verifies company emails from public websites.

## 🎯 Features

- **Web Crawling**: Respectfully crawls company websites
- **Email Discovery**: Finds emails and generates common formats
- **Email Verification**: MX and SMTP checks with confidence scoring
- **Web Dashboard**: Beautiful, interactive web interface
- **Command Line**: CLI interface for automation
- **CSV Export**: Download results as CSV files

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Web Dashboard (Recommended)
```bash
python launch_emailscope.py
# Open browser to: http://localhost:5000
```


## 📁 Project Structure

```
emailscope/
├── crawler.py          # Web crawling
├── extractor.py       # Email extraction
├── verifier.py        # Email verification
└── dashboard.py      # Web dashboard

templates/
└── dashboard.html    # Web interface

launch_emailscope.py  # Dashboard launcher
requirements.txt      # Dependencies
```

## 🎯 Usage

### Web Dashboard
1. Run: `python launch_emailscope.py`
2. Open: `http://localhost:5000`
3. Enter domain and click "Start Scraping"
4. View results in real-time table
5. Export as CSV when complete


## 🔧 Features

- **Respectful Scraping**: Honors robots.txt and rate limits
- **Email Discovery**: Finds emails and generates common formats
- **Verification**: MX and SMTP checks with confidence scoring
- **Real-time Dashboard**: Beautiful web interface with live updates
- **CSV Export**: Download results with all metadata
- **Automation Ready**: GitHub Actions for monthly execution

---

**EmailScope** - Free email discovery with web dashboard and CLI interface.
