'use client';

/**
 * Login Page - Mock Authentication
 * Feature: 006-frontend-chat-ui
 * Updated: 011-midnight-glass-ui - Glass card and input styling
 *
 * For hackathon MVP - accepts any email/password.
 * Creates a local session with UUID.
 */

import React, { useState, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Container } from '@/components/layout/Container';
import { cn } from '@/lib/utils';

interface FormErrors {
  email?: string;
  password?: string;
  general?: string;
}

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/chat');
    }
  }, [isAuthenticated, isLoading, router]);

  // Validate email format
  const validateEmail = (value: string): string | undefined => {
    if (!value.trim()) {
      return 'Email is required';
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return 'Please enter a valid email address';
    }
    return undefined;
  };

  // Validate password
  const validatePassword = (value: string): string | undefined => {
    if (!value) {
      return 'Password is required';
    }
    return undefined;
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    const emailError = validateEmail(email);
    if (emailError) newErrors.email = emailError;

    const passwordError = validatePassword(password);
    if (passwordError) newErrors.password = passwordError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      await login(email, password);
      // On success, redirect to chat
      router.push('/chat');
    } catch (err) {
      setErrors({
        general: err instanceof Error ? err.message : 'Login failed. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show loading while checking auth state
  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-400" />
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
      <Container className="max-w-md w-full">
        <Card variant="glass" className="p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-12 h-12 glass rounded-xl flex items-center justify-center mx-auto mb-4 shadow-glow">
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
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-dark-50">Welcome back</h1>
            <p className="text-dark-400 mt-2">Sign in to continue to AI Todo Agent</p>
          </div>

          {/* General Error */}
          {errors.general && (
            <div className="mb-6 p-3 glass-subtle border border-error-500/30 rounded-lg">
              <p className="text-sm text-error-400">{errors.general}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Field */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-dark-300 mb-1.5"
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) {
                    setErrors((prev) => ({ ...prev, email: undefined }));
                  }
                }}
                placeholder="you@example.com"
                autoComplete="email"
                className={cn(
                  'w-full input-glass',
                  errors.email && 'border-error-500/50 focus:ring-error-500/50'
                )}
                disabled={isSubmitting}
              />
              {errors.email && (
                <p className="mt-1.5 text-sm text-error-400">{errors.email}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-dark-300 mb-1.5"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) {
                    setErrors((prev) => ({ ...prev, password: undefined }));
                  }
                }}
                placeholder="Enter your password"
                autoComplete="current-password"
                className={cn(
                  'w-full input-glass',
                  errors.password && 'border-error-500/50 focus:ring-error-500/50'
                )}
                disabled={isSubmitting}
              />
              {errors.password && (
                <p className="mt-1.5 text-sm text-error-400">{errors.password}</p>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full"
              size="lg"
              disabled={isSubmitting}
              isLoading={isSubmitting}
            >
              Sign in
            </Button>
          </form>

          {/* Sign Up Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-dark-400">
              Don&apos;t have an account?{' '}
              <Link
                href="/signup"
                className="text-primary-400 hover:text-primary-300 font-medium transition-colors"
              >
                Sign up
              </Link>
            </p>
          </div>

          {/* Back to Home */}
          <div className="mt-4 text-center">
            <Link
              href="/"
              className="text-sm text-dark-400 hover:text-dark-200 transition-colors"
            >
              Back to home
            </Link>
          </div>
        </Card>
      </Container>
    </div>
  );
}
