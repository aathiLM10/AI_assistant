export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  answer: string;
  model: string;
}

export interface ApiErrorResponse {
  detail: string;
  error_code?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  model?: string;
  timestamp: string;
  error?: boolean;
}
