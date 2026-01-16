'use client';

/**
 * Chat Container Component
 * Feature: 006-frontend-chat-ui
 *
 * Custom chat interface following ChatKit patterns.
 * Can be replaced with @openai/chatkit-react when available.
 */

import React, { useState, useRef, useEffect, useCallback, FormEvent } from 'react';
import { apiClient, ApiClientError } from '@/lib/api';
import { cn, formatRelativeTime } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import type { Message, ChatMessage } from '@/types';

interface ChatContainerProps {
  conversationId?: string | null;
  onConversationCreated?: (conversationId: string) => void;
}

export function ChatContainer({
  conversationId: initialConversationId,
  onConversationCreated,
}: ChatContainerProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(
    initialConversationId || null
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    const content = inputValue.trim();
    if (!content || isSending) return;

    setError(null);
    setIsSending(true);

    // Optimistic update - add user message immediately
    const tempId = 'temp-' + Date.now();
    const userMessage: ChatMessage = {
      id: tempId,
      role: 'user',
      content,
      createdAt: new Date().toISOString(),
      isPending: true,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    try {
      const response = await apiClient.sendMessage({
        conversation_id: conversationId,
        content,
      });

      // Update conversation ID if new conversation was created
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
        onConversationCreated?.(response.conversation_id);
      }

      // Replace temp message with confirmed message and add assistant response
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== tempId);
        // Find the user message in the response
        const userMsg = response.messages.find(
          (m) => m.role === 'user' && m.content === content
        );
        // Get the assistant message
        const assistantMsg = response.message;

        return [
          ...filtered,
          userMsg || { ...userMessage, isPending: false },
          assistantMsg,
        ].map((m) => ({ ...m, isPending: false }));
      });
    } catch (err) {
      // Mark message as failed
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempId
            ? {
                ...m,
                isPending: false,
                hasError: true,
                errorMessage:
                  err instanceof ApiClientError
                    ? err.message
                    : 'Failed to send message',
              }
            : m
        )
      );

      setError(
        err instanceof ApiClientError
          ? err.message
          : 'Failed to send message. Please try again.'
      );
    } finally {
      setIsSending(false);
    }
  };

  // Handle retry for failed messages
  const handleRetry = async (message: ChatMessage) => {
    // Remove the failed message
    setMessages((prev) => prev.filter((m) => m.id !== message.id));
    // Set the content back to input
    setInputValue(message.content);
    inputRef.current?.focus();
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-primary-600"
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
            <h3 className="text-lg font-medium text-slate-800 mb-2">
              Start a conversation
            </h3>
            <p className="text-sm text-slate-500 max-w-sm">
              Ask me to help manage your tasks. Try &quot;Add a task to buy groceries&quot;
              or &quot;Show me my tasks&quot;.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onRetry={() => handleRetry(message)}
          />
        ))}

        {/* Thinking indicator */}
        {isSending && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
              <svg
                className="w-4 h-4 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div className="bg-slate-100 rounded-2xl rounded-tl-md px-4 py-3">
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                <span
                  className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                />
                <span
                  className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error message */}
      {error && (
        <div className="px-4 py-2 bg-error-50 border-t border-error-200">
          <p className="text-sm text-error-700">{error}</p>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-slate-200 p-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            rows={1}
            className={cn(
              'flex-1 resize-none rounded-lg border border-slate-300 px-4 py-3',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              'placeholder:text-slate-400 text-slate-800',
              'disabled:bg-slate-50 disabled:cursor-not-allowed'
            )}
            disabled={isSending}
          />
          <Button
            type="submit"
            disabled={!inputValue.trim() || isSending}
            isLoading={isSending}
            aria-label="Send message"
          >
            Send
          </Button>
        </form>
        <p className="text-xs text-slate-400 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

// Message Bubble Component
function MessageBubble({
  message,
  onRetry,
}: {
  message: ChatMessage;
  onRetry: () => void;
}) {
  const isUser = message.role === 'user';
  const [showToolCalls, setShowToolCalls] = useState(false);

  // Check if message contains tool calls (simple heuristic)
  const hasToolCalls =
    message.role === 'assistant' &&
    (message.content.includes('[Tool:') || message.content.includes('tool_call'));

  return (
    <div
      className={cn(
        'flex items-start gap-3',
        isUser && 'flex-row-reverse'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-slate-200' : 'bg-primary-100'
        )}
      >
        {isUser ? (
          <svg
            className="w-4 h-4 text-slate-600"
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
        ) : (
          <svg
            className="w-4 h-4 text-primary-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
        )}
      </div>

      {/* Message Content */}
      <div className={cn('max-w-[70%] space-y-1', isUser && 'text-right')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-3',
            isUser
              ? 'bg-primary-600 text-white rounded-tr-md'
              : 'bg-slate-100 text-slate-800 rounded-tl-md',
            message.isPending && 'opacity-70',
            message.hasError && 'border-2 border-error-300'
          )}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Metadata */}
        <div
          className={cn(
            'flex items-center gap-2 text-xs text-slate-400',
            isUser && 'justify-end'
          )}
        >
          {message.isPending && <span>Sending...</span>}
          {message.hasError && (
            <>
              <span className="text-error-500">{message.errorMessage}</span>
              <button
                onClick={onRetry}
                className="text-primary-600 hover:text-primary-700 underline"
              >
                Retry
              </button>
            </>
          )}
          {!message.isPending && !message.hasError && (
            <span>{formatRelativeTime(message.createdAt)}</span>
          )}
        </div>

        {/* Tool Calls (collapsed by default) */}
        {hasToolCalls && (
          <div className="mt-2">
            <button
              onClick={() => setShowToolCalls(!showToolCalls)}
              className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1"
            >
              <svg
                className={cn(
                  'w-3 h-3 transition-transform',
                  showToolCalls && 'rotate-90'
                )}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
              Tool calls
            </button>
            {showToolCalls && (
              <div className="mt-1 p-2 bg-slate-50 rounded text-xs text-slate-600 font-mono">
                {message.content}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatContainer;
