# Sphynx - GitHub Candidate Finder

An AI-powered tool that helps you find the perfect candidates on GitHub based on your requirements.

## Features

- Search GitHub users based on natural language requirements
- AI-powered analysis of candidate profiles
- Score candidates based on their suitability
- View detailed candidate information including:
  - Programming languages
  - Contributions
  - Location
  - Bio
  - GitHub activity

## Setup

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```
GITHUB_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_api_key
```

## Usage

Run the Streamlit app:
```bash
streamlit run github_scraper.py
```

Then:
1. Enter your requirements in natural language (e.g., "I want an AI engineer from San Francisco")
2. Click "SEARCH"
3. View the ranked list of candidates with detailed profiles

## Notes

- GitHub API has rate limits. For better results, use an authenticated token
- The tool uses GPT-4 for candidate analysis, ensure you have appropriate OpenAI API access
- Previous searches are saved locally in `previous_searches.json` 