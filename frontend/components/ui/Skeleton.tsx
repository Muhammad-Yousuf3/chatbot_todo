'use client';

/**
 * Skeleton Loader Component
 * Feature: 006-frontend-chat-ui
 */

import React, { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'circular' | 'rectangular';
}

export function Skeleton({
  width,
  height,
  variant = 'rectangular',
  className,
  style,
  ...props
}: SkeletonProps) {
  const variantStyles = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  return (
    <div
      className={cn(
        'animate-pulse bg-slate-200',
        variantStyles[variant],
        className
      )}
      style={{
        width: typeof width === 'number' ? width + 'px' : width,
        height: typeof height === 'number' ? height + 'px' : height,
        ...style,
      }}
      {...props}
    />
  );
}

/**
 * Pre-built skeleton for text lines
 */
export function SkeletonText({
  lines = 1,
  className,
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          height={16}
          width={i === lines - 1 && lines > 1 ? '60%' : '100%'}
        />
      ))}
    </div>
  );
}

/**
 * Pre-built skeleton for cards
 */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('p-4 border border-slate-200 rounded-lg', className)}>
      <Skeleton height={20} width="40%" className="mb-3" />
      <SkeletonText lines={2} />
      <div className="flex gap-2 mt-4">
        <Skeleton height={32} width={80} />
        <Skeleton height={32} width={80} />
      </div>
    </div>
  );
}

/**
 * Pre-built skeleton for avatar
 */
export function SkeletonAvatar({
  size = 40,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <Skeleton
      variant="circular"
      width={size}
      height={size}
      className={className}
    />
  );
}

export default Skeleton;
