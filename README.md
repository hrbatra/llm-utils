# Exa-Researcher

A powerful research assistant that leverages OpenAI's models and Exa's search capabilities to conduct comprehensive research on any topic.

## Features

- Iterative research query generation based on previous findings
- Intelligent source evaluation and ranking
- Content summarization and analysis
- Comprehensive research report synthesis
- Structured output using OpenAI's function calling

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/exa-researcher.git
cd exa-researcher
```

2. Create and activate a virtual environment using `uv`:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY
# - EXA_API_KEY
```

## Usage

Run a research pipeline:
```bash
python test_openai_model.py
```

## Project Structure

```
exa-researcher/
├── models/
│   ├── base.py          # Base classes and data models
│   └── openai_model.py  # OpenAI model implementation
├── tests/
│   └── test_openai_model.py  # Unit tests and sample pipeline
├── README.md
├── requirements.txt
└── .env
```

## Future Development

The following features are planned for future releases:

1. **Enhanced Media Support**
   - Download and analyze images from sources
   - Extract and process data from charts and infographics
   - Support for video content analysis

2. **Data Analysis Capabilities**
   - Download and parse CSV files
   - Statistical analysis of numerical data
   - Data visualization generation
   - Integration with pandas/polars for data manipulation

3. **Improved Reporting**
   - Custom report templates
   - Interactive visualizations
   - Citation management
   - Export to multiple formats (PDF, HTML, etc.)
   - Executive summaries with different detail levels

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
