'use client';

/**
 * DecisionTimeline Component - Vertical timeline of decisions
 * Feature: 006-frontend-chat-ui
 */

import React from 'react';
import type { DecisionLog } from '@/types';
import { DecisionNode } from './DecisionNode';
import { cn } from '@/lib/utils';

interface DecisionTimelineProps {
  decisions: DecisionLog[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  className?: string;
}

export function DecisionTimeline({
  decisions,
  selectedId,
  onSelect,
  className,
}: DecisionTimelineProps) {
  if (decisions.length === 0) {
    return (
      <div className={cn('text-center py-8', className)}>
        <p className="text-slate-500">No decisions found</p>
      </div>
    );
  }

  return (
    <div className={cn('relative', className)}>
      {/* Timeline line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-200" />

      {/* Decision nodes */}
      <div className="space-y-4">
        {decisions.map((decision) => (
          <DecisionNode
            key={decision.decisionId}
            decision={decision}
            isSelected={selectedId === decision.decisionId}
            onClick={() => onSelect(decision.decisionId)}
          />
        ))}
      </div>
    </div>
  );
}

export default DecisionTimeline;
