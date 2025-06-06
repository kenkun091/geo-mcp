import os
import re
import json
from openai import OpenAI
from  import wedge_model, plot_wavelet
from dotenv import load_dotenv

load_dotenv()

# Initialize the DeepSeek client using OpenAI compatible API
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",  # DeepSeek API endpoint
)

def parse_user_input(user_input):
    """
    Use LLM to parse user input and extract parameters for wedge model generation
    """
    prompt = f"""
    Parse the following request for generating a wedge model or wavelet plot and extract the parameters.
    Request: "{user_input}"
    
    For a wedge model, extract these parameters if mentioned (use default values if not specified):
    - Plot type: "wedge" or "wavelet"
    - Wavelet type: "ricker" or "ormsby"
    - Ricker frequency (Hz): e.g., 30
    - Ormsby frequencies (Hz): comma-separated list of 4 values
    - Phase rotation (degrees): default 0
    - Maximum thickness (m): default 80
    - Layer velocities (m/s): Vp1, Vp2, Vp3 (defaults: 2000, 3000, 4000)
    - Layer densities (g/cc): Rho1, Rho2, Rho3 (defaults: 2.0, 2.2, 2.4)
    - Gain: default 1.0
    - Thickness domain: "time" or "depth" (default "depth")
    
    Return a JSON object with these parameters.
    """
    
    try:
        response = client.chat.completions.create(
            # model="gpt-4",
            model = "deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that parses requests for geophysical modeling."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        
        parsed_text = response.choices[0].message.content
        # Extract JSON from the response
        json_match = re.search(r'```json\n(.*?)\n```', parsed_text, re.DOTALL)
        if json_match:
            parsed_json = json.loads(json_match.group(1))
        else:
            # Try to find any JSON-like structure
            json_match = re.search(r'{.*}', parsed_text, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group(0))
            else:
                raise ValueError("Could not extract JSON from LLM response")
                
        return parsed_json
    
    except Exception as e:
        print(f"Error parsing input: {e}")
        return None

def generate_output_filename(params, file_type):
    """Generate a filename based on parameters"""
    if params.get("plot_type") == "wedge":
        base_name = f"wedge_{params.get('wavelet_type')}_{params.get('ricker_freq', '')}Hz"
    else:
        base_name = f"wavelet_{params.get('wavelet_type')}_{params.get('ricker_freq', '')}Hz"
    
    return f"{base_name}.{file_type}"

def process_request(user_input):
    """Process the user request and generate the appropriate plot"""
    params = parse_user_input(user_input)
    
    if not params:
        return "Sorry, I couldn't understand your request. Please try again with more details.", None
    
    try:
        # Set default values
        defaults = {
            "plot_type": "wedge",
            "wavelet_type": "ricker",
            "ricker_freq": 30,
            "ormsby_freq": "5,10,40,60",
            "phase_rot": 0,
            "max_thickness": 50,
            "vp1": 2000, "vp2": 3000, "vp3": 4000,
            "rho1": 2.0, "rho2": 2.2, "rho3": 2.4,
            "gain": 1.0,
            "thickness_domain": "depth",
            "zunit": "m",
            "plotpadtime": 100
        }
        
        # Update with parsed values
        for key, value in params.items():
            if key in defaults and value is not None:
                defaults[key] = value
        
        # Generate filenames
        fig_fname = generate_output_filename(defaults, "png")
        csv_fname = generate_output_filename(defaults, "csv") if defaults["plot_type"] == "wedge" else ""
        
        # Generate the appropriate plot
        if defaults["plot_type"].lower() == "wedge":
            wedge_model(
                defaults["zunit"],
                defaults["max_thickness"],
                defaults["wavelet_type"],
                defaults["ricker_freq"],
                defaults["ormsby_freq"],
                "",  # wavelet_str
                "",  # wavelet_fname
                defaults["phase_rot"],
                defaults["vp1"],
                defaults["vp2"],
                defaults["vp3"],
                defaults["rho1"],
                defaults["rho2"],
                defaults["rho3"],
                defaults["gain"],
                defaults["plotpadtime"],
                defaults["thickness_domain"],
                fig_fname,
                csv_fname
            )
            return f"Wedge model created: {fig_fname}", fig_fname
        
        elif defaults["plot_type"].lower() == "wavelet":
            plot_wavelet(
                defaults["wavelet_type"],
                defaults["ricker_freq"],
                defaults["ormsby_freq"],
                "",  # wavelet_str
                "",  # wavelet_fname
                defaults["phase_rot"],
                fig_fname
            )
            return f"Wavelet plot created: {fig_fname}", fig_fname
        
        else:
            return "Unknown plot type requested. Please specify 'wedge' or 'wavelet'.", None
    
    except Exception as e:
        return f"Error generating plot: {e}", None

# Example usage
if __name__ == "__main__":
    # Test with a sample input
    user_input = "make a wedge model with ricker wavelet, frequency 30Hz"
    result, filename = process_request(user_input)
    print(result)