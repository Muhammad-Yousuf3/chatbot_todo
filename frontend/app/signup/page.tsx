'use client';

/**
 * Signup Page - User Registration
 * Feature: 006-frontend-chat-ui
 * Updated: 011-midnight-glass-ui - Glass card and input styling
 *
 * Creates a new user account with email, password, and display name.
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
  displayName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  general?: string;
}

export default function SignupPage() {
  const router = useRouter();
  const { signup, isAuthenticated, isLoading } = useAuth();

  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/chat');
    }
  }, [isAuthenticated, isLoading, router]);

  // Validate display name
  const validateDisplayName = (value: string): string | undefined => {
    if (!value.trim()) {
      return 'Display name is required';
    }
    if (value.trim().length < 2) {
      return 'Display name must be at least 2 characters';
    }
    return undefined;
  };

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
    if (value.length < 6) {
      return 'Password must be at least 6 characters';
    }
    return undefined;
  };

  // Validate confirm password
  const validateConfirmPassword = (value: string): string | undefined => {
    if (!value) {
      return 'Please confirm your password';
    }
    if (value !== password) {
      return 'Passwords do not match';
    }
    return undefined;
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    const displayNameError = validateDisplayName(displayName);
    if (displayNameError) newErrors.displayName = displayNameError;

    const emailError = validateEmail(email);
    if (emailError) newErrors.email = emailError;

    const passwordError = validatePassword(password);
    if (passwordError) newErrors.password = passwordError;

    const confirmPasswordError = validateConfirmPassword(confirmPassword);
    if (confirmPasswordError) newErrors.confirmPassword = confirmPasswordError;

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
      await signup(email, password, displayName.trim());
      // On success, redirect to chat
      router.push('/chat');
    } catch (err) {
      setErrors({
        general: err instanceof Error ? err.message : 'Signup failed. Please try again.',
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
                  d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-dark-50">Create an account</h1>
            <p className="text-dark-400 mt-2">Get started with AI Todo Agent</p>
          </div>

          {/* General Error */}
          {errors.general && (
            <div className="mb-6 p-3 glass-subtle border border-error-500/30 rounded-lg">
              <p className="text-sm text-error-400">{errors.general}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Display Name Field */}
            <div>
              <label
                htmlFor="displayName"
                className="block text-sm font-medium text-dark-300 mb-1.5"
              >
                Display name
              </label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => {
                  setDisplayName(e.target.value);
                  if (errors.displayName) {
                    setErrors((prev) => ({ ...prev, displayName: undefined }));
                  }
                }}
                placeholder="John Doe"
                autoComplete="name"
                className={cn(
                  'w-full input-glass',
                  errors.displayName && 'border-error-500/50 focus:ring-error-500/50'
                )}
                disabled={isSubmitting}
              />
              {errors.displayName && (
                <p className="mt-1.5 text-sm text-error-400">{errors.displayName}</p>
              )}
            </div>

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
                placeholder="At least 6 characters"
                autoComplete="new-password"
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

            {/* Confirm Password Field */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-dark-300 mb-1.5"
              >
                Confirm password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (errors.confirmPassword) {
                    setErrors((prev) => ({ ...prev, confirmPassword: undefined }));
                  }
                }}
                placeholder="Repeat your password"
                autoComplete="new-password"
                className={cn(
                  'w-full input-glass',
                  errors.confirmPassword && 'border-error-500/50 focus:ring-error-500/50'
                )}
                disabled={isSubmitting}
              />
              {errors.confirmPassword && (
                <p className="mt-1.5 text-sm text-error-400">{errors.confirmPassword}</p>
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
              Create account
            </Button>
          </form>

          {/* Sign In Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-dark-400">
              Already have an account?{' '}
              <Link
                href="/login"
                className="text-primary-400 hover:text-primary-300 font-medium transition-colors"
              >
                Sign in
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
