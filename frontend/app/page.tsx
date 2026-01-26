'use client';

/**
 * Landing Page - Hero Section with CTA
 * Feature: 006-frontend-chat-ui
 * Updated: 011-midnight-glass-ui - Glass effects and accent gradient
 *
 * First impression for hackathon judges.
 * Explains product purpose within 10 seconds.
 */

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import { Container } from '@/components/layout/Container';

export default function LandingPage() {
  const { isAuthenticated } = useAuth();

  // Navigate to chat if authenticated, otherwise to login
  const ctaHref = isAuthenticated ? '/chat' : '/login';

  return (
    <div className="flex flex-col min-h-[calc(100vh-8rem)]">
      {/* Hero Section */}
      <section className="flex-1 flex items-center justify-center px-4">
        <Container className="text-center">
          {/* Icon - Glass with glow */}
          <div className="mb-8 flex justify-center">
            <div className="w-20 h-20 glass rounded-2xl flex items-center justify-center shadow-glow">
              <svg
                className="w-10 h-10 text-primary-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                />
              </svg>
            </div>
          </div>

          {/* Headline - Gradient accent */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-dark-50 mb-6">
            Manage Tasks with{' '}
            <span className="bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">Natural Language</span>
          </h1>

          {/* Description */}
          <p className="text-lg sm:text-xl text-dark-300 max-w-2xl mx-auto mb-10">
            An AI-powered assistant that understands your requests and manages your todo list.
            Just type what you need, and let the agent handle the rest.
          </p>

          {/* CTA Button */}
          <Link href={ctaHref}>
            <Button size="lg" className="px-8 py-4 text-lg">
              Start Chatting
            </Button>
          </Link>

          {/* Sub-text */}
          <p className="mt-4 text-sm text-dark-400">
            {isAuthenticated
              ? 'Continue to your conversations'
              : 'No account required to try'}
          </p>
        </Container>
      </section>

      {/* Features Section - Glass cards */}
      <section className="py-16 glass-subtle">
        <Container>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
            {/* Feature 1 */}
            <div className="p-6 glass rounded-xl card-hover">
              <div className="w-12 h-12 glass rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-6 h-6 text-primary-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-dark-50 mb-2">
                Natural Conversation
              </h3>
              <p className="text-dark-400 text-sm">
                Just type what you want. No need to learn commands or syntax.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 glass rounded-xl card-hover">
              <div className="w-12 h-12 glass rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-6 h-6 text-success-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-dark-50 mb-2">
                Smart Task Management
              </h3>
              <p className="text-dark-400 text-sm">
                Add, complete, and organize tasks with simple requests.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 glass rounded-xl card-hover">
              <div className="w-12 h-12 glass rounded-lg flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-6 h-6 text-warning-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-dark-50 mb-2">
                Intelligent Agent
              </h3>
              <p className="text-dark-400 text-sm">
                Powered by AI that understands context and learns from interactions.
              </p>
            </div>
          </div>
        </Container>
      </section>
    </div>
  );
}
