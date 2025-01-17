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

## Local Development

1. Clone this repository
2. Install backend dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Create a `.env` file with your GitHub token:
```
GITHUB_TOKEN=your_github_token
```

5. Run the backend:
```bash
uvicorn api.main:app --reload
```

6. Run the frontend:
```bash
cd frontend
npm run dev
```

## Deployment to Vercel

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Add your GitHub token to Vercel:
```bash
vercel secrets add github_token your_github_token
```

4. Deploy to Vercel:
```bash
vercel
```

5. For production deployment:
```bash
vercel --prod
```

## Notes

- GitHub API has rate limits. For better results, use an authenticated token
- The tool uses Selenium for scraping additional GitHub data
- Make sure to set up the GitHub token in your Vercel environment variables 