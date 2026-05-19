# AI School Log Extractor

AI-powered Flask application that extracts handwritten school daily logs from uploaded photos and converts them into structured data using NVIDIA-hosted Meta Llama vision models.

The app can automatically append extracted entries to a single Google Sheet using Google OAuth authentication.

## Features

- 📸 Upload school daily log photos
- 🤖 AI-powered handwriting extraction using NVIDIA + Meta Llama 3.2 Vision
- 📋 Automatic template detection
- 📊 Append entries to one persistent Google Sheet
- 💾 Local JSON backup storage
- 📁 Export to CSV
- 📗 Export to Excel (.xlsx)
- 🔐 Google OAuth authentication
- 🌐 Flask web UI

## Tech Stack

- Python
- Flask
- NVIDIA API
- Meta Llama 3.2 90B Vision Instruct
- Google Sheets API
- Google OAuth
- gspread
- OpenPyXL

## Prerequisites

- Python 3.10+
- NVIDIA API key
- Google OAuth client credentials

## Installation

### Clone repository

```bash
git clone https://github.com/vxdatalabs/ai-school-log-extractor.git
cd ai-school-log-extractor