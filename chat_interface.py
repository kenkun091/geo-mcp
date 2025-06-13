import gradio as gr
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from tools import make_ricker, plot_ricker, compute_reflectivity
import io
import base64

class SeismicChatBot:
    def __init__(self):
        self.available_tools = {
            'make_ricker': {
                'function': make_ricker,
                'description': 'Creates a Ricker wavelet',
                'keywords': ['ricker', 'wavelet', 'create', 'make', 'generate'],
                'required_params': ['frequency'],
                'optional_params': {'dt': 0.001, 'duration': 0.256}
            },
            'plot_ricker': {
                'function': plot_ricker,
                'description': 'Plots a Ricker wavelet with time domain and frequency domain analysis',
                'keywords': ['plot', 'show', 'visualize', 'display', 'graph', 'chart'],
                'required_params': ['wavelet'],
                'optional_params': {'time': None}
            },
            'compute_reflectivity': {
                'function': compute_reflectivity,
                'description': 'Computes reflectivity from velocity and density data',
                'keywords': ['reflectivity', 'reflection', 'coefficient', 'velocity', 'density', 'impedance'],
                'required_params': ['vp'],
                'optional_params': {'rho': None, 'n_samples': 1000, 'positions': [100, 300]}
            }
        }
        self.conversation_context = {}
    
    def extract_numbers(self, text):
        """Extract numbers from text"""
        numbers = re.findall(r'\d+\.?\d*', text)
        return [float(n) for n in numbers]
    
    def extract_frequencies(self, text):
        """Extract frequency values from text"""
        freq_patterns = [
            r'(\d+\.?\d*)\s*hz',
            r'frequency\s*(?:of|is|=)?\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*hertz',
            r'freq\s*(?:of|is|=)?\s*(\d+\.?\d*)'
        ]
        
        for pattern in freq_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return [float(m) for m in matches]
        
        # If no specific frequency keywords, look for numbers in context
        numbers = self.extract_numbers(text)
        if numbers and any(keyword in text.lower() for keyword in ['frequency', 'freq', 'hz', 'hertz']):
            return numbers
        
        return []
    
    def extract_velocities(self, text):
        """Extract velocity values from text"""
        vel_patterns = [
            r'velocity\s*(?:of|is|=)?\s*\[([^\]]+)\]',
            r'vp\s*(?:of|is|=)?\s*\[([^\]]+)\]',
            r'velocities?\s*(?:of|is|=)?\s*\[([^\]]+)\]',
            r'v\s*=\s*\[([^\]]+)\]'
        ]
        
        for pattern in vel_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                # Parse the array-like string
                try:
                    values = [float(x.strip()) for x in matches[0].split(',')]
                    return values
                except:
                    continue
        
        # Look for sequences of numbers when velocity is mentioned
        if any(keyword in text.lower() for keyword in ['velocity', 'vp', 'speed']):
            numbers = self.extract_numbers(text)
            if len(numbers) > 1:
                return numbers
        
        return []
    
    def parse_natural_language(self, user_input):
        """Parse natural language input to determine tool and parameters"""
        text = user_input.lower()
        
        # Determine which tool to use based on keywords
        best_tool = None
        max_score = 0
        
        for tool_name, tool_info in self.available_tools.items():
            score = sum(1 for keyword in tool_info['keywords'] if keyword in text)
            if score > max_score:
                max_score = score
                best_tool = tool_name
        
        if not best_tool:
            return None, "I couldn't understand what seismic modeling operation you'd like to perform. Try asking about creating a ricker wavelet, plotting wavelets, or computing reflectivity."
        
        # Extract parameters based on the selected tool
        params = {}
        
        if best_tool == 'make_ricker':
            frequencies = self.extract_frequencies(text)
            if frequencies:
                params['frequency'] = frequencies[0]
            
            # Extract dt if mentioned
            if 'dt' in text or 'sampling' in text:
                numbers = self.extract_numbers(text)
                for num in numbers:
                    if 0.0001 <= num <= 0.01:  # Reasonable dt range
                        params['dt'] = num
                        break
            
            # Extract duration if mentioned
            if 'duration' in text or 'length' in text:
                numbers = self.extract_numbers(text)
                for num in numbers:
                    if 0.1 <= num <= 2.0:  # Reasonable duration range
                        params['duration'] = num
                        break
        
        elif best_tool == 'plot_ricker':
            # Check if we have a wavelet from previous context
            if 'wavelet' in self.conversation_context:
                params['wavelet'] = self.conversation_context['wavelet']
                if 'time' in self.conversation_context:
                    params['time'] = self.conversation_context['time']
            else:
                # Try to create a wavelet first
                frequencies = self.extract_frequencies(text)
                if frequencies:
                    ricker_params = {'frequency': frequencies[0]}
                    result = make_ricker(ricker_params)
                    params['wavelet'] = result['wavelet']
                    params['time'] = result['time']
                    self.conversation_context.update(result)
        
        elif best_tool == 'compute_reflectivity':
            velocities = self.extract_velocities(text)
            if velocities:
                params['vp'] = velocities
            
            # Extract other parameters if mentioned
            numbers = self.extract_numbers(text)
            if 'samples' in text and numbers:
                for num in numbers:
                    if 100 <= num <= 10000:
                        params['n_samples'] = int(num)
                        break
        
        return best_tool, params
    
    def execute_tool(self, tool_name, params):
        """Execute the selected tool with parameters"""
        tool_info = self.available_tools[tool_name]
        
        # Check required parameters
        missing_params = []
        for req_param in tool_info['required_params']:
            if req_param not in params:
                missing_params.append(req_param)
        
        if missing_params:
            return None, f"Missing required parameters: {', '.join(missing_params)}"
        
        # Add default values for optional parameters
        for opt_param, default_value in tool_info['optional_params'].items():
            if opt_param not in params and default_value is not None:
                params[opt_param] = default_value
        
        try:
            result = tool_info['function'](params)
            return result, None
        except Exception as e:
            return None, f"Error executing {tool_name}: {str(e)}"
    
    def format_response(self, tool_name, params, result):
        """Format the response with explanations"""
        if tool_name == 'make_ricker':
            freq = params['frequency']
            dt = params.get('dt', 0.001)
            duration = params.get('duration', 0.256)
            
            response = f"""I've created a Ricker wavelet with the following parameters:
- Frequency: {freq} Hz
- Sampling interval (dt): {dt} seconds
- Duration: {duration} seconds

The wavelet contains {len(result['wavelet'])} samples. This Ricker wavelet is commonly used in seismic modeling as a source wavelet due to its zero-phase characteristic and compact frequency spectrum.

The wavelet data has been stored for further analysis. You can now ask me to plot it or use it in other operations."""
        
        elif tool_name == 'plot_ricker':
            wavelet_length = len(result) if hasattr(result, '__len__') else "unknown"
            
            response = f"""I've generated a comprehensive plot of the Ricker wavelet showing:

1. **Time Domain**: The wavelet amplitude over time, with positive values in blue and negative values in red
2. **Amplitude Spectrum**: The frequency content showing the dominant frequency and bandwidth
3. **Power Spectrum**: The normalized power in decibels, useful for understanding the energy distribution

This visualization helps understand both the temporal and spectral characteristics of the wavelet, which is crucial for seismic forward modeling and interpretation."""
        
        elif tool_name == 'compute_reflectivity':
            vp = params['vp']
            n_layers = len(vp)
            
            response = f"""I've computed the reflectivity series from {n_layers} velocity layers:
- Input velocities: {vp}
- Generated {len(result['reflectivity'])} reflection coefficients

The reflectivity represents the contrast in acoustic impedance between layers. Positive values indicate an increase in impedance (hard reflection), while negative values indicate a decrease (soft reflection). This reflectivity series can be convolved with a source wavelet to generate synthetic seismograms."""
        
        else:
            response = f"Successfully executed {tool_name} with the provided parameters."
        
        return response

def create_chat_interface():
    chatbot = SeismicChatBot()
    
    def chat_fn(message, history):
        # Parse the natural language input
        tool_name, params_or_error = chatbot.parse_natural_language(message)
        
        if tool_name is None:
            return history + [[message, params_or_error]]
        
        # Execute the tool
        result, error = chatbot.execute_tool(tool_name, params_or_error)
        
        if error:
            return history + [[message, f"Error: {error}"]]
        
        # Update conversation context
        if isinstance(result, dict):
            chatbot.conversation_context.update(result)
        
        # Format response
        response = chatbot.format_response(tool_name, params_or_error, result)
        
        # Handle plotting
        if tool_name == 'plot_ricker' and isinstance(result, plt.Figure):
            # Convert matplotlib figure to image
            buf = io.BytesIO()
            result.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode()
            
            response += f"\n\n![Ricker Wavelet Plot](data:image/png;base64,{img_str})"
            plt.close(result)  # Clean up the figure
        
        return history + [[message, response]]
    
    # Create the Gradio interface
    with gr.Blocks(title="Seismic Modeling Chat Interface") as demo:
        gr.Markdown("""
        # 🌊 Seismic Modeling Chat Interface
        
        Ask me to perform seismic modeling tasks using natural language! I can:
        - Create Ricker wavelets: *"Create a 30 Hz Ricker wavelet"*
        - Plot wavelets: *"Plot the wavelet"* or *"Show me a 25 Hz ricker wavelet"*
        - Compute reflectivity: *"Calculate reflectivity for velocities [2000, 3000, 2500]"*
        
        Just describe what you want to do in natural language!
        """)
        
        chatbot_ui = gr.Chatbot(
            label="Seismic Modeling Assistant",
            height=500,
            show_label=True
        )
        
        with gr.Row():
            msg = gr.Textbox(
                label="Your message",
                placeholder="e.g., 'Create a 30 Hz Ricker wavelet and plot it'",
                scale=4
            )
            submit = gr.Button("Send", scale=1, variant="primary")
        
        gr.Examples(
            examples=[
                "Create a 25 Hz Ricker wavelet",
                "Plot a 30 Hz Ricker wavelet", 
                "Generate a ricker wavelet with frequency 20 Hz and duration 0.5 seconds",
                "Compute reflectivity for velocities [2000, 3000, 2500, 4000]",
                "Show me the frequency spectrum of a 35 Hz ricker"
            ],
            inputs=msg
        )
        
        # Event handlers
        submit.click(chat_fn, [msg, chatbot_ui], chatbot_ui)
        msg.submit(chat_fn, [msg, chatbot_ui], chatbot_ui)
        
        # Clear message box after sending
        submit.click(lambda: "", None, msg)
        msg.submit(lambda: "", None, msg)
    
    return demo

if __name__ == "__main__":
    demo = create_chat_interface()
    demo.launch(debug=True, share=True)