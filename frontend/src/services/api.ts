import { ChatRequest, ChatResponse, ApiErrorResponse } from "@/types/chat";

/**
 * Architectural note:
 * The frontend exclusively interfaces with our intermediate FastAPI backend.
 * No Gemini SDK or provider credentials are ever loaded into or invoked from the browser.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  statusCode: number;
  detail: string;

  constructor(statusCode: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.detail = detail;
  }
}

/**
 * Dispatches a user query to the FastAPI POST /chat endpoint.
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const endpoint = `${API_BASE_URL}/chat`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errorMessage = `Server responded with status ${response.status}`;
      try {
        const errorData: ApiErrorResponse = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === "string" 
            ? errorData.detail 
            : JSON.stringify(errorData.detail);
        }
      } catch {
        // Fallback to HTTP status text if response is not JSON
        errorMessage = response.statusText || errorMessage;
      }
      throw new ApiError(response.status, errorMessage);
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : "Failed to connect to backend server";
    throw new ApiError(0, message);
  }
}

/**
 * Inspects backend health check endpoint.
 */
export async function checkBackendHealth(): Promise<{ status: string; model: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error("Backend reported non-OK status");
    }
    return await response.json();
  } catch (error) {
    throw new Error("Unable to connect to FastAPI backend at " + API_BASE_URL);
  }
}
