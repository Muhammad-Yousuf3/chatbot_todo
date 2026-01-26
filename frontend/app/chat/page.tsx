'use client';

/**
 * Chat Page - AI Agent Chat Interface
 * Feature: 006-frontend-chat-ui
 * Updated: 011-midnight-glass-ui - Glass container styling
 *
 * Full-screen chat interface for conversational task management.
 * Protected route - requires authentication.
 */

import React, { useState, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { Container } from '@/components/layout/Container';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Skeleton } from '@/components/ui/Skeleton';

function ChatPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Get initial conversation ID from URL if present
  const urlConversationId = searchParams.get('conversation');
  const [conversationId, setConversationId] = useState<string | null>(
    urlConversationId
  );

  // Update URL when new conversation is created
  const handleConversationCreated = useCallback(
    (newConversationId: string) => {
      setConversationId(newConversationId);
      // Update URL without full page navigation
      router.replace(`/chat?conversation=${newConversationId}`, {
        scroll: false,
      });
    },
    [router]
  );

  return (
    <ProtectedRoute>
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        <Container className="flex-1 py-4 flex flex-col">
          <div className="flex-1 glass rounded-xl overflow-hidden">
            <ChatContainer
              conversationId={conversationId}
              onConversationCreated={handleConversationCreated}
            />
          </div>
        </Container>
      </div>
    </ProtectedRoute>
  );
}

function ChatLoadingFallback() {
  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <Container className="flex-1 py-4 flex flex-col">
        <div className="flex-1 glass rounded-xl overflow-hidden p-4">
          <div className="flex flex-col h-full">
            <div className="flex-1 space-y-4">
              <Skeleton className="h-16 w-3/4" />
              <Skeleton className="h-16 w-1/2 ml-auto" />
              <Skeleton className="h-16 w-2/3" />
            </div>
            <Skeleton className="h-12 w-full mt-4" />
          </div>
        </div>
      </Container>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<ChatLoadingFallback />}>
      <ChatPageContent />
    </Suspense>
  );
}
