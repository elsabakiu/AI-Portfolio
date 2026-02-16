# AI Portfolio – Elsa Bakiu

AI Product Manager with 12+ years of experience building and scaling complex B2B and B2G platforms.  
This portfolio showcases end-to-end AI product work, focusing on LLM-powered workflows, usability, and production-aware system design.

## TL;DR

- Product Manager with strong technical background (MSc Computer Science)
- Experience leading large-scale platform redesigns and regulated products
- Hands-on with AI prototyping, prompt design, and system trade-offs
- Focused on turning AI capabilities into usable, reliable products


## What this portfolio shows

This portfolio is not a collection of demos.  
It focuses on how AI is applied to real product problems, including:

- Problem framing and user needs
- AI system design under real-world constraints
- Prompt design and controllability
- Trade-offs, limitations, and next steps
- Usable outputs, not just code


## Projects

### 🎙️ Podcast Studio – AI Podcast Episode Generator

An AI-powered application that transforms long-form online articles into narrated podcast episodes.

Why it matters:
- Explores AI-driven content adaptation
- Focuses on audio-first and accessibility use cases
- Demonstrates reliability challenges in LLM and TTS pipelines

What it demonstrates:
- End-to-end AI product thinking
- Prompt design for structured, spoken output
- Chunking strategies to handle LLM and TTS limits
- Balancing automation with user control
- Simple UI for fast experimentation and feedback

Project folder: `podcast-studio`  
See the detailed README inside the project folder for full documentation.

### 📰 News Summarizer – AI Briefing Assistant

A product-style AI news pipeline that fetches headlines, generates summaries, runs sentiment analysis, and tracks usage/cost metrics.

What it demonstrates:
- Clear modular architecture (`providers`, `processing`, `pipeline`, `reporting`)
- Production-grade logging with `run_id` correlation
- Typed error handling and graceful failure thresholds
- CLI + Gradio UX for different user needs

Project folder: `news-summarizer`

### 📈 Stock Market Analysis RAG – Investment Research Assistant

A retrieval-augmented generation project for grounded Q&A on filings/transcripts from a local market research dataset.

What it demonstrates:
- End-to-end RAG pipeline (chunking, embeddings, retrieval, answer generation)
- Reliability design (retry strategy, error mapping, document-level fault isolation)
- PM-oriented product framing and release-ready documentation
- Backward compatibility while modernizing architecture

Project folder: `stock-market-analysis-RAG`

### 🧠 AI Product Playbook – Reusable PM Assets

A collection of reusable prompts and product-thinking artifacts used across projects.

What it demonstrates:
- Prompt libraries and reusable templates
- Product requirements framing for AI features
- Structured experimentation and workflow guidance

Project folder: `ai-product-playbook`


## Skills demonstrated through projects

- AI product discovery and prototyping
- Prompt engineering and evaluation thinking
- System design for generative AI
- UX considerations for AI-driven workflows
- Translating complex requirements into usable products


## How to navigate this repo

- Start with the project that matches your interest area (content, news intelligence, or RAG)
- Read the project README for problem, solution, and design decisions
- Review docs and outputs before diving into code


## Contact

- LinkedIn: https://www.linkedin.com/in/elsa-bakiu
- Location: Munich, Germany
- Email: elsabakiu@gmail.com


## Notes

This portfolio is evolving. New projects and deeper documentation will be added over time as I continue exploring AI-powered product experiences.

If you are reviewing this as a recruiter or hiring manager, I am happy to walk through any project and discuss design decisions, trade-offs, and next steps.
