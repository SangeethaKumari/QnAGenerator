# 🤖 AI Agents Webinar Q&A Parser

A powerful Streamlit application that intelligently extracts interview questions, production-level insights, and common issues with solutions from AI agents webinar transcripts using Claude AI.

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Project Setup](#project-setup)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [Output Categories](#output-categories)
- [Supported File Formats](#supported-file-formats)
- [Export Options](#export-options)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [License](#license)

## ✨ Features

- **📤 Smart File Upload**: Support for TXT, PDF, and DOCX file formats
- **🤖 AI-Powered Parsing**: Uses Claude 3 Opus to intelligently analyze transcripts
- **📊 Organized Categorization**:
  - Interview Questions (general AI agent knowledge)
  - Production-Level Questions (scaling, monitoring, deployment)
  - Common Issues & Solutions (real problems and fixes)
- **🎯 Multiple Views**: All results, individual tabs, table view, and raw JSON
- **📥 Flexible Export**: Download as JSON or CSV formats
- **📈 Statistics Dashboard**: Visual metrics for all categories
- **🎨 User-Friendly Interface**: Clean, professional Streamlit UI

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+**
- **uv** (Ultra-fast Python package installer) - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Anthropic API Key** - Get it from [console.anthropic.com](https://console.anthropic.com)
- **Git** (optional, for version control)

## 🚀 Project Setup

### Step 1: Initialize Project with uv

Initialize a new project directory with Python 3.12:

```bash
uv init ai_agents_qa_parser --python=3.12
cd ai_agents_qa_parser
```

### Step 2: Copy Configuration Files

Copy the environment configuration script and documentation:

```bash
cp <my_path>/ai_environment/ensure_config.sh ./
cp <my_path>/ai_environment/docs.tgz ./
chmod +x ./ensure_config.sh
```

### Step 3: Run Configuration Script

Execute the configuration script to set up your environment:

```bash
./ensure_config.sh
```

This script will:
- Extract the documentation archive
- Set up environment variables
- Configure project dependencies

### Step 4: Create Project Files

Create the main application file:

```bash
touch app.py
```

Copy the Streamlit application code (provided in the code artifact) into `app.py`.

## 📦 Installation

### Install Dependencies

Add required packages to your project using uv:

```bash
uv add streamlit anthropic PyPDF2 python-docx pandas
```

This will create/update your `pyproject.toml` and `uv.lock` files.

### Verify Installation

To verify all dependencies are installed correctly:

```bash
uv pip list
```

You should see:
- streamlit
- anthropic
- PyPDF2
- python-docx
- pandas

### Create Requirements File (Optional)

If you need a traditional `requirements.txt`:

```bash
uv pip freeze > requirements.txt
```

## ⚙️ Configuration

### API Key Setup

1. Get your Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
2. When you run the app, enter your API key in the sidebar
3. Alternatively, set environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Optional: Streamlit Configuration

Create `.streamlit/config.toml` for persistent settings:

```toml
[logger]
level = "info"

[client]
showErrorDetails = true

[server]
maxUploadSize = 200
```

## 🎯 Running the Application

### Development Mode

```bash
uv run streamlit run app.py
```

This will:
- Start the Streamlit development server
- Open the app in your default browser (usually http://localhost:8501)
- Hot-reload on code changes

### Production Mode

For production deployment:

```bash
uv run streamlit run app.py --logger.level=warning --server.headless=true
```

## 📖 Usage Guide

### Basic Workflow

1. **Start the Application**
   ```bash
   uv run streamlit run app.py
   ```

2. **Enter API Key**
   - Paste your Anthropic API key in the sidebar settings
   - Key is not stored and only used for the current session

3. **Upload Transcript**
   - Click the file upload area
   - Select your webinar transcript (TXT, PDF, or DOCX)
   - File preview shows the selected filename

4. **Parse Transcript**
   - Click the "🔍 Parse Transcript" button
   - Wait for processing (typically 10-30 seconds)
   - Success message appears when complete

5. **View Results**
   - Browse different tabs:
     - 📋 All Results
     - 📝 Interview Questions
     - 🏭 Production Questions
     - ⚠️ Common Issues
     - 📥 Export
   - Each item shows question/issue with detailed answer/solution

6. **Export Data**
   - Go to the "📥 Export" tab
   - Download as JSON or CSV
   - View results in table format
   - Inspect raw JSON data

7. **Clear Results**
   - Click "🗑️ Clear Results" to start with a new transcript

### Tips for Best Results

- **File Quality**: Use clear, well-formatted transcripts for better extraction
- **File Size**: Optimal file size is 5-50KB of text content
- **Language**: Ensure transcript is in English
- **Format**: PDF files should have selectable text (not scanned images)

## 📊 Output Categories

### Interview Questions
General knowledge questions suitable for technical interviews:
- AI agent architecture and design
- Implementation best practices
- Core concepts and frameworks
- System design considerations

### Production Questions
Production-environment specific questions:
- Scaling and performance optimization
- Monitoring and observability
- Error handling and resilience
- Deployment strategies
- Reliability and availability
- Security considerations

### Common Issues & Solutions
Real-world problems and their solutions:
- Known issues discussed in the webinar
- Practical solutions and workarounds
- Best practices to avoid problems
- Optimization techniques

## 📁 Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| Plain Text | `.txt` | UTF-8 encoded, fastest processing |
| PDF | `.pdf` | Must have extractable text (not scanned images) |
| Word Document | `.docx` | Microsoft Word 2007+ format |

### File Size Limits

- **Recommended**: 5-50 KB of text content
- **Maximum**: Limited by Anthropic API (approx. 100KB per request)
- **Minimum**: At least 50 characters

## 📥 Export Options

### JSON Export
```json
{
  "interview_questions": [
    {
      "question": "What is an AI agent?",
      "answer": "An AI agent is..."
    }
  ],
  "production_questions": [...],
  "common_issues": [...]
}
```

### CSV Export
Three columns: Type, Question/Issue, Answer/Solution
Suitable for:
- Spreadsheet applications (Excel, Google Sheets)
- Further processing and filtering
- Database imports

### Table View
Interactive pandas DataFrame with sortable columns

### Raw JSON View
Complete JSON structure for programmatic access

## 🛠️ Troubleshooting

### Issue: "API Key not provided"
**Solution**: Enter your API key in the sidebar settings

### Issue: "Unsupported file type"
**Solution**: Ensure file is in TXT, PDF, or DOCX format

### Issue: "Error reading PDF file"
**Cause**: PDF may contain scanned images without text
**Solution**: Use a tool to extract text or convert to TXT format

### Issue: "JSON parsing error"
**Cause**: API response format unexpected
**Solution**: Try a smaller transcript or check API quota

### Issue: "Empty results"
**Cause**: Transcript doesn't contain AI agent discussion
**Solution**: Ensure you're using a webinar transcript about AI agents

### Issue: "Slow processing"
**Cause**: Large file size or slow internet
**Solution**: Try a smaller transcript or check connection

## 📁 Project Structure

```
ai_agents_qa_parser/
├── app.py                           # Main Streamlit application
├── pyproject.toml                   # Project metadata and dependencies (uv)
├── uv.lock                          # Locked dependency versions
├── ensure_config.sh                 # Configuration script
├── docs.tgz                         # Documentation archive
├── README.md                        # This file
├── .streamlit/
│   └── config.toml                  # Streamlit configuration (optional)
├── .env                             # Environment variables (optional)
└── outputs/                         # Exported results (optional)
    ├── qa_extraction.json
    └── qa_extraction.csv
```

## 🔐 Security Notes

- **API Key**: Never commit your API key to version control
- **Use Environment Variables**: Store API key in `.env` file (add to `.gitignore`)
- **Data Privacy**: Transcripts are sent to Anthropic API but not stored
- **.gitignore**: Create one to exclude sensitive files:

```
.env
.streamlit/secrets.toml
*.pyc
__pycache__/
.DS_Store
uv.lock
```

## 🐛 Debugging

### Enable Verbose Logging

```bash
uv run streamlit run app.py --logger.level=debug
```

### Check Dependencies

```bash
uv pip show streamlit anthropic
```

### Verify Python Version

```bash
python --version  # Should be 3.12+
```

## 📝 Advanced Usage

### Processing Multiple Files

Process transcripts one at a time:
1. Run the app
2. Upload first transcript
3. Parse and export
4. Clear results
5. Repeat with next transcript

### Custom Prompt Engineering

Edit the `prompt` variable in `parse_transcript()` function to customize:
- Question categories
- Answer depth
- Output format

### Integration with Other Tools

Export JSON or CSV for:
- Knowledge management systems
- Interview preparation platforms
- Study applications
- Data analysis tools

## 📚 Learn More

- [Streamlit Documentation](https://docs.streamlit.io)
- [Anthropic Claude API](https://docs.anthropic.com)
- [uv Package Manager](https://docs.astral.sh/uv/)
- [Python 3.12 Guide](https://docs.python.org/3.12/)

## 🤝 Contributing

To contribute improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙋 Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review error messages in the Streamlit terminal
3. Verify API key and file format
4. Check Anthropic API status at [status.anthropic.com](https://status.anthropic.com)

## 🎯 Roadmap

Future enhancements planned:

- [ ] Batch processing for multiple files
- [ ] Custom category templates
- [ ] SQLite database storage
- [ ] Web API for programmatic access
- [ ] User authentication
- [ ] File history and caching
- [ ] Advanced filtering and search
- [ ] Real-time transcript processing

## 📞 Contact

For questions or feedback about this project, please open an issue or contact the development team.

---

**Last Updated**: November 2024
**Version**: 1.0.0
**Python**: 3.12+
**Status**: Active Maintenance
