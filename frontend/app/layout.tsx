import React from 'react';
import { Inter } from 'next/font/google';
import './globals.css';
import type { Metadata } from 'next';
import type { ReactNode } from 'react';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: "Sphynx - GitHub Candidate Finder",
  description: "Find the perfect GitHub candidates for your team",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}