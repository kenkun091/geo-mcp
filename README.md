# Seismic Modeling Chat Interface

This project provides a chat interface for seismic modeling using Gradio. It allows users to interact with an AI assistant to generate seismic models and visualizations.

## Features

- Chat-based interface for seismic modeling requests
- Generate Ricker wavelets with customizable parameters
- Create wedge models with various layer properties
- Compute reflectivity series
- Visualize results directly in the chat interface

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Starting the Gradio Interface

Run the following command to start the Gradio interface:

```bash
python gradio_interface.py
```

This will launch a local web server and provide a URL to access the interface.

### Example Queries

You can interact with the system using natural language. Here are some example queries:

- "Generate a 30 Hz Ricker wavelet with 0.1 s duration"
- "Create a wedge model with a Ricker wavelet at 25 Hz"
- "Plot an Ormsby wavelet with frequencies 5,10,40,60 Hz"
- "Compute reflectivity for layers with velocities 2000, 3000, and 4000 m/s"

## Project Structure

- `gradio_interface.py`: Main Gradio interface for the chat application
- `app.py`: OpenAI API integration for tool-calling
- `tools.py`: Implementation of seismic modeling tools
- `wedge.py`: Functions for generating wedge models and wavelets
- `chat_interface.py`: Utilities for parsing user input and generating responses
- `run_server.py`: MCP server implementation

## Dependencies

- Gradio: For the chat interface
- OpenAI API: For natural language processing
- MCP: Model Control Protocol for tool integration
- Bruges: Seismic modeling library
- Matplotlib: For visualization
- NumPy/SciPy: For numerical computations

## License

This project is licensed under the MIT License - see the LICENSE file for details.