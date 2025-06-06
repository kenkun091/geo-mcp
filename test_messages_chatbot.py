import gradio as gr
import os
from PIL import Image
from openai import OpenAI
from chat_interface import process_request

# Get OpenAI API key from environment
openai_api_key = os.environ.get("DEEPSEEK_API_KEY")

# Initialize the DeepSeek client using OpenAI compatible API
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",  # DeepSeek API endpoint
)

def chat_function(message, history):
    if not openai_api_key:
        return history + [{"role": "user", "content": message}, {"role": "assistant", "content": "OpenAI API key not set. Please set the OPENAI_API_KEY environment variable."}], None
    
    try:
        # Process the natural language request using the actual process_request function
        response_text, image_path = process_request(message)
        
        # If successful, return the image and response
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            return history + [{"role": "user", "content": message}, {"role": "assistant", "content": response_text}], img
        else:
            return history + [{"role": "user", "content": message}, {"role": "assistant", "content": response_text}], None
    except Exception as e:
        error_message = f"Error processing request: {str(e)}"
        return history + [{"role": "user", "content": message}, {"role": "assistant", "content": error_message}], None

with gr.Blocks() as demo:
    gr.Markdown("# Seismic Modeling Interface - Test")
    gr.Markdown("Generate seismic wavelets and wedge models using natural language.")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(type="messages", height=500)
            msg = gr.Textbox(
                placeholder="Describe what you want to model in natural language (e.g., 'Generate a Ricker wavelet with 40Hz frequency and 45 degree phase rotation')...", 
                show_label=False
            )
            clear = gr.Button("Clear")
        
        with gr.Column(scale=2):
            image_output = gr.Image(label="Generated Visualization", height=500)
    
    # Connect the components
    msg.submit(chat_function, [msg, chatbot], [chatbot, image_output]).then(
        lambda: "", None, msg
    )
    clear.click(lambda: None, None, chatbot)

if __name__ == "__main__":
    print("Starting Gradio demo...")
    demo.launch()
    print("Demo launched!")