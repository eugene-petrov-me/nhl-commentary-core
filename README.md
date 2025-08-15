# 🏒 nhl-commentary-core

This repository is responsible for **fetching NHL data** and **generating AI-powered text commentary**. It serves as the backend engine of a larger AI live commentary system.

---

## 📁 Folder Structure

| Folder / File        | Description |
|----------------------|-------------|
| `data/`              | Game data ingestion, including play-by-play and summaries |
| `prompts/`           | Prompt templates used for generating commentary in different styles |
| `engine/`            | Main LLM script for transforming data into human-like commentary |
| `.env.example`       | Template file for required API keys and configuration variables |
| `main.py`            | CLI or application entry point |
| `requirements.txt`   | Dependency list for setting up the project |

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/nhl-commentary-core.git
cd nhl-commentary-core
```

### 2. Create your .env file
Copy the .env.example to .env and fill in your OpenAI and (optionally) NHL API keys.

```bash
cp .env.example .env
```

Example:
```bash
OPENAI_API_KEY=your-openai-key
NHL_API_BASE=https://api.nhle.com/stats/rest/
```
### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## 🚀 Usage

Run the CLI to summarize a game:

```bash
python main.py
```

Follow the prompts to choose a game and select between AI or rule-based summaries.

## 🤝 Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and open a pull request.
Feel free to submit issues for bugs or feature suggestions.

