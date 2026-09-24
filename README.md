# AI Assistant 🤖

A learning-focused Generative AI application built to understand the complete end-to-end LLM application architecture.

## Overview

The purpose of this project is to learn the complete flow of an LLM-powered application:
```
User → Next.js UI → FastAPI /chat → ChatService → PromptService → LLMService → GeminiProvider → Gemini API → Validation → Next.js UI
```

This project intentionally does not use heavy abstraction frameworks (such as LangChain or LangGraph) so that every layer of prompt management, provider integration, response parsing, validation, and error handling can be clearly understood and traced.

## Tech Stack

- **Backend:** Python 3.13, FastAPI, Pydantic v2, pydantic-settings, official Google Gemini SDK (`google-generativeai`), Uvicorn
- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS
