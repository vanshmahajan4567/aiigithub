'use client';

import React, { useState } from 'react';

interface Candidate {
  name: string;
  bio: string;
  location: string;
  languages: Record<string, number>;
  contributions: number;
  public_repos: number;
  followers: number;
  pinned_repos: string[];
  contribution_streak: string;
  explanation: string;
  profile_url: string;
  score: number;
}

export default function Home() {
  const [requirement, setRequirement] = useState('');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchCandidates = async () => {
    if (!requirement) {
      setError('Please enter search requirements');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ requirement }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setCandidates(data.candidates);
    } catch (err) {
      setError('Failed to search candidates. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 bg-gray-100">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center text-gray-800">
          Sphynx - Git the perfect candidate
        </h1>

        <div className="mb-8">
          <input
            type="text"
            value={requirement}
            onChange={(e) => setRequirement(e.target.value)}
            placeholder="Describe the candidate you're looking for..."
            className="w-full p-4 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={searchCandidates}
            disabled={loading}
            className="mt-4 w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? 'Searching...' : 'SEARCH'}
          </button>
          {error && <p className="mt-2 text-red-500">{error}</p>}
        </div>

        {candidates.length > 0 && (
          <div>
            <h2 className="text-2xl font-semibold mb-4">
              Found {candidates.length} matching candidates
            </h2>
            <div className="space-y-4">
              {candidates.map((candidate, index) => (
                <div
                  key={index}
                  className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow"
                >
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-semibold">{candidate.name}</h3>
                    <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                      Score: {candidate.score}/100
                    </span>
                  </div>
                  <p className="text-gray-600 mb-2">{candidate.bio}</p>
                  <p className="text-gray-600 mb-2">📍 {candidate.location}</p>
                  <p className="text-gray-600 mb-2">
                    💻 Languages: {Object.keys(candidate.languages).join(', ')}
                  </p>
                  <p className="text-gray-600 mb-2">
                    🔥 Contributions: {candidate.contributions}
                  </p>
                  <p className="text-gray-600 mb-2">
                    📚 Public Repos: {candidate.public_repos}
                  </p>
                  <p className="text-gray-600 mb-2">
                    👥 Followers: {candidate.followers}
                  </p>
                  {candidate.pinned_repos.length > 0 && (
                    <div className="mb-2">
                      <p className="text-gray-600">📌 Pinned Repositories:</p>
                      <ul className="list-disc list-inside pl-4">
                        {candidate.pinned_repos.map((repo, i) => (
                          <li key={i} className="text-gray-600">
                            {repo}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <p className="text-gray-600 mb-2">
                    📊 Contribution Streak: {candidate.contribution_streak}
                  </p>
                  <p className="text-gray-600 mb-4">
                    ℹ️ Match Details: {candidate.explanation}
                  </p>
                  <a
                    href={candidate.profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:text-blue-600"
                  >
                    View GitHub Profile →
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
} 