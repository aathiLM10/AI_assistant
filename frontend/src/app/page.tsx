"use client";

import { useState, useEffect, useRef } from "react";
import { ChatMessage } from "@/types/chat";
import { sendChatMessage, checkBackendHealth, ApiError } from "@/services/api";

const PRESET_PROMPTS = [
  "Explain the difference between a prompt and a system instruction.",
  "How does tokenization work in Large Language Models?",
  "What are temperature and top-p sampling parameters in GenAI?",
  "Why is it architectural best practice to separate LLM providers from business services?",
];

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [activeModel, setActiveModel] = useState<string>("gemini-1.5-flash");
  const [showArchTrace, setShowArchTrace] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    async function verifyBackend() {
      try {
        const health = await checkBackendHealth();
        setBackendStatus("online");
        if (health.model) {
          setActiveModel(health.model);
        }
      } catch {
        setBackendStatus("offline");
      }
    }
    verifyBackend();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSubmit = async (e?: React.FormEvent, customPrompt?: string) => {
    if (e) e.preventDefault();
    const query = customPrompt || inputMessage;
    const trimmed = query.trim();

    if (!trimmed || isLoading) return;

    setErrorMessage(null);

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await sendChatMessage({ message: trimmed });

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        model: response.model,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setBackendStatus("online");
    } catch (err: unknown) {
      let displayError = "An unexpected error occurred while communicating with the backend.";
      if (err instanceof ApiError) {
        if (err.statusCode === 0) {
          displayError = "Cannot connect to FastAPI backend. Ensure the backend server is running on http://localhost:8000.";
          setBackendStatus("offline");
        } else if (err.statusCode === 504) {
          displayError = "Request timed out while waiting for Gemini to generate a response (504 Gateway Timeout).";
        } else if (err.statusCode === 502) {
          displayError = `Upstream LLM Provider error: ${err.detail}`;
        } else if (err.statusCode === 422) {
          displayError = `Validation Error: ${err.detail}`;
        } else {
          displayError = err.detail || `Server error (${err.statusCode})`;
        }
      }
      setErrorMessage(displayError);
    } finally {
      setIsLoading(false);
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setErrorMessage(null);
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Top Application Bar */}
      <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-4 lg:px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <span className="text-lg">🤖</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-white">AI Assistant</h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                GenAI Architecture
              </span>
            </div>
            <p className="text-xs text-slate-400">Next.js → FastAPI → PromptService → LLMService → Gemini</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Status Indicator */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                backendStatus === "online"
                  ? "bg-emerald-400 animate-pulse"
                  : backendStatus === "offline"
                  ? "bg-rose-500"
                  : "bg-amber-400"
              }`}
            />
            <span className="text-slate-300">
              {backendStatus === "online"
                ? `FastAPI Online (${activeModel})`
                : backendStatus === "offline"
                ? "FastAPI Disconnected"
                : "Checking backend..."}
            </span>
          </div>

          <button
            onClick={() => setShowArchTrace(!showArchTrace)}
            className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
            title="Toggle Architecture Pipeline Visualizer"
          >
            {showArchTrace ? "Hide Flow" : "Show Architecture"}
          </button>

          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="text-xs px-2.5 py-1 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/40 text-rose-300 transition-colors"
            >
              Reset Chat
            </button>
          )}
        </div>
      </header>

      {/* Learning Architecture Visualizer Banner */}
      {showArchTrace && (
        <section className="bg-slate-900/60 border-b border-slate-800/80 px-4 py-2.5">
          <div className="max-w-5xl mx-auto flex items-center justify-between flex-wrap gap-2 text-xs">
            <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
              End-to-End Pipeline:
            </span>
            <div className="flex items-center flex-wrap gap-1.5 text-slate-300">
              <span className="px-2 py-0.5 rounded bg-blue-950/60 border border-blue-800/60 text-blue-300 font-mono">
                1. Next.js UI
              </span>
              <span className="text-slate-600">→</span>
              <span className="px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 font-mono">
                2. FastAPI /chat
              </span>
              <span className="text-slate-600">→</span>
              <span className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 font-mono">
                3. ChatService
              </span>
              <span className="text-slate-600">→</span>
              <span className="px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800/60 text-amber-300 font-mono">
                4. PromptService
              </span>
              <span className="text-slate-600">→</span>
              <span className="px-2 py-0.5 rounded bg-purple-950/60 border border-purple-800/60 text-purple-300 font-mono">
                5. LLMService
              </span>
              <span className="text-slate-600">→</span>
              <span className="px-2 py-0.5 rounded bg-violet-950/60 border border-violet-800/60 text-violet-300 font-mono">
                6. GeminiProvider
              </span>
              <span className="text-slate-600">→</span>
              <span className="px-2 py-0.5 rounded bg-rose-950/60 border border-rose-800/60 text-rose-300 font-mono">
                7. Gemini API
              </span>
            </div>
          </div>
        </section>
      )}

      {/* Main Content / Chat Stream */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col justify-between">
        {messages.length === 0 ? (
          <div className="my-auto py-12 flex flex-col items-center text-center max-w-2xl mx-auto">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center text-3xl mb-4 shadow-xl">
              ⚡
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Welcome to AI Assistant</h2>
            <p className="text-sm text-slate-400 mb-8 leading-relaxed">
              This application is designed to demonstrate clean GenAI application architecture.
              Every prompt travels through decoupled layers: Validation → Services → Provider → Gemini.
            </p>

            <div className="w-full text-left">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Suggested exploration questions:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {PRESET_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSubmit(undefined, prompt)}
                    disabled={isLoading}
                    className="p-3 rounded-xl bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800 hover:border-indigo-500/50 text-left text-xs text-slate-300 transition-all hover:shadow-md hover:shadow-indigo-500/5 group"
                  >
                    <span className="text-indigo-400 group-hover:text-indigo-300 mr-1.5 font-bold">›</span>
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4 py-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
              >
                <div className="flex items-center gap-2 mb-1 px-1">
                  <span className="text-[11px] font-medium text-slate-400">
                    {msg.role === "user" ? "You" : "AI Assistant"}
                  </span>
                  {msg.model && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-950/60 border border-indigo-800/40 text-indigo-300 font-mono">
                      {msg.model}
                    </span>
                  )}
                  <span className="text-[10px] text-slate-500">{msg.timestamp}</span>
                </div>

                <div
                  className={`p-4 rounded-2xl max-w-[88%] text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white rounded-tr-none shadow-md shadow-indigo-600/20"
                      : "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-sm"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Loading / Generating State */}
            {isLoading && (
              <div className="flex flex-col items-start">
                <div className="flex items-center gap-2 mb-1 px-1">
                  <span className="text-[11px] font-medium text-slate-400">AI Assistant</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-950/60 border border-violet-800/40 text-violet-300 font-mono animate-pulse">
                    Generating...
                  </span>
                </div>
                <div className="p-4 rounded-2xl rounded-tl-none bg-slate-900 border border-slate-800 text-slate-400 text-xs flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                  <span>Querying FastAPI → PromptService → LLMService → Gemini...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Error Notification Alert */}
        {errorMessage && (
          <div className="mb-4 p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start justify-between gap-3">
            <div className="flex items-start gap-2">
              <span className="text-rose-400 font-bold text-sm">⚠</span>
              <div>
                <p className="font-semibold text-rose-200">Request Error</p>
                <p className="mt-0.5 text-rose-300/90 leading-relaxed">{errorMessage}</p>
              </div>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-rose-200 text-xs px-2 py-1 rounded bg-rose-900/30 hover:bg-rose-900/60 transition-colors"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Input Bar */}
        <div className="pt-2 sticky bottom-0 bg-slate-950 pb-2">
          <form
            onSubmit={(e) => handleSubmit(e)}
            className="rounded-2xl border border-slate-800 bg-slate-900/95 focus-within:border-indigo-500/80 transition-all p-2 flex flex-col shadow-xl"
          >
            <textarea
              ref={textareaRef}
              rows={2}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Ask anything (e.g. How does self-attention work in Transformers?)..."
              className="w-full bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none disabled:opacity-50"
            />

            <div className="flex items-center justify-between pt-2 px-2 border-t border-slate-800/60">
              <span className="text-[11px] text-slate-500">
                Press <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono text-[10px]">Enter ↵</kbd> to submit, <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono text-[10px]">Shift+Enter</kbd> for newline
              </span>

              <button
                type="submit"
                disabled={isLoading || !inputMessage.trim()}
                className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                  isLoading || !inputMessage.trim()
                    ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
                    : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30 cursor-pointer"
                }`}
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-3.5 w-3.5 text-slate-400" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <span>Send</span>
                    <span className="text-sm">↗</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
