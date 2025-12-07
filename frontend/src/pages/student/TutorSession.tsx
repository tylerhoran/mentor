import { useState, useRef, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "../../api/client";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  pedagogical_move?: string;
  concepts_referenced?: string[];
}

interface SessionInfo {
  id: string;
  course_id: string;
  course_name: string;
  started_at: string;
  messages: Message[];
  current_concept?: string;
  mastery_update?: {
    concept: string;
    previous: number;
    current: number;
  };
}

export default function TutorSession() {
  const { courseId } = useParams<{ courseId: string }>();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: session } = useQuery({
    queryKey: ["tutorSession", courseId],
    queryFn: () => api.get<SessionInfo>(`/tutor/session/${courseId}`),
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (session?.messages) {
      setMessages(session.messages);
    }
  }, [session]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const sendMessage = useMutation({
    mutationFn: async (content: string) => {
      setIsStreaming(true);
      setStreamingContent("");

      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      let fullResponse = "";

      await api.stream(
        `/tutor/message/${courseId}`,
        {
          message: content,
        },
        (chunk) => {
          fullResponse += chunk;
          setStreamingContent(fullResponse);
        },
      );

      const assistantMessage: Message = {
        id: `response-${Date.now()}`,
        role: "assistant",
        content: fullResponse,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setStreamingContent("");
      setIsStreaming(false);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const message = input.trim();
    setInput("");
    sendMessage.mutate(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/student" className="text-gray-500 hover:text-gray-700">
            &larr;
          </Link>
          <div>
            <h1 className="font-semibold text-gray-900">
              {session?.course_name || "Loading..."}
            </h1>
            {session?.current_concept && (
              <p className="text-sm text-gray-500">
                Currently discussing: {session.current_concept}
              </p>
            )}
          </div>
        </div>
        <Link to={`/student/courses/${courseId}/progress`}>
          <Button variant="outline" size="sm">
            View Progress
          </Button>
        </Link>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && !isStreaming && (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">👋</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Welcome to your tutoring session!
              </h2>
              <p className="text-gray-500 max-w-md mx-auto">
                Ask me anything about the course material. I'm here to help you
                understand concepts and guide you through problems.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {[
                  "Explain the main concept",
                  "Give me a practice problem",
                  "Review what we covered",
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setInput(prompt)}
                    className="px-3 py-2 bg-white border rounded-lg text-sm text-gray-700 hover:bg-gray-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-white border text-gray-900"
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.pedagogical_move && (
                  <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-400">
                    {message.pedagogical_move}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isStreaming && streamingContent && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg px-4 py-3 bg-white border text-gray-900">
                <div className="whitespace-pre-wrap">{streamingContent}</div>
                <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-1" />
              </div>
            </div>
          )}

          {isStreaming && !streamingContent && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg px-4 py-3 bg-white border">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Mastery Update Toast */}
      {session?.mastery_update && (
        <div className="fixed bottom-24 right-4 bg-green-50 border border-green-200 rounded-lg px-4 py-3 shadow-lg">
          <div className="text-sm font-medium text-green-800">
            Mastery Updated!
          </div>
          <div className="text-xs text-green-600">
            {session.mastery_update.concept}:{" "}
            {Math.round(session.mastery_update.previous * 100)}% →{" "}
            {Math.round(session.mastery_update.current * 100)}%
          </div>
        </div>
      )}

      {/* Input */}
      <div className="bg-white border-t px-4 py-4">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-3">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            disabled={isStreaming}
            className="flex-1"
          />
          <Button type="submit" disabled={!input.trim() || isStreaming}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}
