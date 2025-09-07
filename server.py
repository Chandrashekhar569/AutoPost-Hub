from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import sys
import logging
from pydantic import ValidationError
from genai_poster.workflow.langgraph_flow import build_graph, GraphState
from genai_poster.models import AppConfig
from genai_poster.config.settings import DEFAULT_OPENAI_MODEL, DEFAULT_IMAGE_MODEL, DOWNLOAD_DIR
from genai_poster.publisher.post_manager import LinkedInClient

app = Flask(__name__)
CORS(app)

LOG = logging.getLogger("festival_linkedin_bot")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

@app.route('/api/generate-post', methods=['POST'])
def generate_post():
    data = request.json

    try:
        # Use data from the form to configure the app
        os.environ["OPENAI_API_KEY"] = data.get("openaiKey")
        os.environ["LINKEDIN_ACCESS_TOKEN"] = data.get("linkedinToken")

        # Get LinkedIn Author URN from the access token
        try:
            linkedin_client = LinkedInClient(data.get("linkedinToken"))
            profile = linkedin_client.get_self_profile()
            linkedin_author_urn = f'urn:li:person:{profile["sub"]}'
        except Exception as e:
            return jsonify({'error': f'Could not retrieve LinkedIn Author URN: {e}'}), 500

        hashtags = [h.strip() for h in data.get("hashtags", "").split(",") if h.strip()]

        cfg = AppConfig(
            brand_name=data.get("brandName"),
            brand_tone=data.get("brandTone"),
            hashtags=hashtags,
            linkedin_author_urn=linkedin_author_urn,
            openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
            image_model=os.getenv("IMAGE_MODEL", DEFAULT_IMAGE_MODEL),
        )

        initial_state: GraphState = {
            "config": cfg,
            "festival": None,
            "post": None,
            "banner": None,
            "banner_path": None,
            "linkedin_result": None,
        }
        
        # Set the calendar URL from the form
        os.environ["CALENDAR_URL"] = data.get("calendarUrl")

        app_instance = build_graph().compile()
        final_state = app_instance.invoke(initial_state)

        fest = final_state["festival"]
        post = final_state["post"]
        result = final_state["linkedin_result"]

        banner_path = final_state.get('banner_path')
        banner_url = f'/downloads/{os.path.basename(banner_path)}' if banner_path else None

        return jsonify({
            'festival': fest.name if fest else 'n/a',
            'post_title': post.title if post else 'n/a',
            'post_body': post.body if post else 'n/a',
            'banner_url': banner_url,
            'linkedin_post_urn': result.post_urn if result else 'n/a'
        })

    except ValidationError as ve:
        return jsonify({'error': f'Validation error: {ve}'}), 400
    except Exception as e:
        return jsonify({'error': f'Fatal error: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
