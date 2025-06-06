import os
import json
import gradio as gr
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import openai
from dotenv import load_dotenv
from tools import make_ricker, compute_reflectivity
from  import wedge_model, plot_wavelet
from chat_interface import parse_user_input, process_request

# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai_api_key = os.environ.get("DEEPSEEK_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

openai.api_key = openai_api_key

# Function to handle chat interactions
def chat_and_generate(message, history):
    # Parse the user input to extract parameters
    try:
        # First, try to process as a direct seismic modeling request
        response_text, image_path = process_request(message)
        
        # If successful, return the image and response
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            return response_text, img
        
        # If no image was generated, treat as a regular chat message for OpenAI
        client = openai.OpenAI()
        
        # Define the tool schema for OpenAI
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": "make_ricker",
                    "description": "Generate a Ricker wavelet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "frequency": {"type": "number"},
                            "dt": {"type": "number"},
                            "duration": {"type": "number"},
                        },
                        "required": ["frequency"],
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "compute_reflectivity",
                    "description": "Compute 1D reflectivity series",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "vp": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "P-wave velocities in m/s"
                            },
                            "rho": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "Densities in kg/m³ (optional)"
                            },
                            "n_samples": {"type": "number", "description": "Number of samples in output"},
                            "positions": {
                                "type": "array",
                                "items": {"type": "number"},
                                "description": "Positions of reflectors"
                            }
                        },
                        "required": ["vp"],
                    }
                }
            }
        ]
        
        # Send user message to OpenAI
        response = client.chat.completions.create(
            model="deepseek-chat",  # or your preferred model
            messages=[
                {"role": "system", "content": "You are a helpful assistant for seismic modeling. You can generate Ricker wavelets and compute reflectivity series."},
                {"role": "user", "content": message}
            ],
            tools=openai_tools,
            tool_choice="auto",
        )
        
        # Check if a tool was called
        response_message = response.choices[0].message
        
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            # Process tool calls
            tool_call = response_message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            # Execute the tool
            if tool_name == "make_ricker":
                result = make_ricker(tool_args)
                
                # Plot the Ricker wavelet
                wavelet = np.array(result["wavelet"])
                time = np.array(result["time"])
                
                plt.figure(figsize=(10, 6))
                plt.plot(time, wavelet)
                plt.title(f"Ricker Wavelet ({tool_args['frequency']} Hz)")
                plt.xlabel("Time (s)")
                plt.ylabel("Amplitude")
                plt.grid(True)
                
                # Save the plot
                temp_img_path = "temp_wavelet.png"
                plt.savefig(temp_img_path)
                plt.close()
                
                # Send result back to OpenAI
                followup = client.chat.completions.create(
                    model="gpt-4",  # or your preferred model
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for seismic modeling."},
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": response_message.content},
                        {"role": "tool", "tool_call_id": tool_call.id, "name": tool_name, "content": json.dumps(result)}
                    ],
                )
                
                # Return the image and the explanation
                img = Image.open(temp_img_path)
                return followup.choices[0].message.content, img
                
            elif tool_name == "compute_reflectivity":
                result = compute_reflectivity(tool_args)
                
                # Plot the reflectivity series
                reflectivity = np.array(result["reflectivity"])
                
                plt.figure(figsize=(10, 6))
                plt.stem(reflectivity)
                plt.title("Reflectivity Series")
                plt.xlabel("Sample Index")
                plt.ylabel("Reflection Coefficient")
                plt.grid(True)
                
                # Save the plot
                temp_img_path = "temp_reflectivity.png"
                plt.savefig(temp_img_path)
                plt.close()
                
                # Send result back to OpenAI
                followup = client.chat.completions.create(
                    model="deepseek-chat", 
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for seismic modeling."},
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": response_message.content},
                        {"role": "tool", "tool_call_id": tool_call.id, "name": tool_name, "content": json.dumps(result)}
                    ],
                )
                
                # Return the image and the explanation
                img = Image.open(temp_img_path)
                return followup.choices[0].message.content, img
        
        # If no tool was called, just return the response content
        return response_message.content, None
        
    except Exception as e:
        return f"Error: {str(e)}", None

# Create the Gradio interface
with gr.Blocks(title="Seismic Modeling Chat") as demo:
    gr.Markdown("# Seismic Modeling Chat Interface")
    gr.Markdown("Ask questions about seismic modeling or request specific models and visualizations.")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(placeholder="Type your message here...", show_label=False)
            clear = gr.Button("Clear")
        
        with gr.Column(scale=2):
            image_output = gr.Image(label="Generated Visualization", height=500)
    
    # Set up event handlers
    msg.submit(chat_and_generate, [msg, chatbot], [chatbot, image_output])
    clear.click(lambda: None, None, chatbot, queue=False)

# Launch the app
if __name__ == "__main__":
    demo.launch(share=True)