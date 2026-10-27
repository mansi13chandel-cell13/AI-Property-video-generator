# Realty Assistant — AI Property Video Generator

A beginner-friendly Streamlit application that turns property details and uploaded listing photos into a promotional MP4 video. It includes three templates, auto-generated captions, optional background music, preview, and download.

## Features
- **Three templates:** Luxury Noir, Fresh & Bright, Editorial Teal
- **Property form:** listing name, location, price, type, bedroom count, features, and CTA
- **Photo upload:** accepts JPG, JPEG, PNG, WEBP (up to 8 images)
- **Video export:** creates a 1280×720 MP4
- **Optional soundtrack:** upload music you have permission to use
- **Graceful validation:** clear errors for missing fields and invalid uploads
- **Demo mode:** runs without property photos using graphic placeholder scenes (not fake property photos)

## Requirements
- Python 3.10 or newer
- Internet is not required after dependencies are installed
- FFmpeg is bundled through `imageio-ffmpeg`

## Setup (Windows / macOS / Linux)
1. Extract the ZIP.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment (recommended):
   - Windows: `py -m venv .venv` then `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install dependencies:
   `pip install -r requirements.txt`
5. Start the app:
   `streamlit run app.py`
6. Open the local URL shown in the terminal, usually `http://localhost:8501`.

## Sample input
- Listing: Modern 2-BHK Apartment
- Location: Kalka, Himachal Pradesh
- Price: ₹45 lakh
- Type: Apartment
- Bedrooms: 2 BHK
- Features: Bright living room; Modular kitchen; Balcony with a view; Covered parking
- CTA: Book your site visit today
- Photos: upload 1–8 images, or leave blank for graphic demo scenes
- Template: Luxury Noir
- Seconds per scene: 4

## Expected output
A five-scene, roughly 20-second MP4 with an opening title, location/property type, key features, price, and enquiry call-to-action. Actual duration can vary slightly because of video encoding.

## How it works
1. Streamlit collects property details and image uploads.
2. Pillow crops photos and draws readable title/caption overlays.
3. FFmpeg concatenates the scenes and encodes the MP4.
4. The user previews and downloads the result.

This version uses a transparent, rule-based layout/caption system rather than an external AI API. It only uses the details entered by the user and does not infer or verify property facts. This is acceptable for a simple MVP and avoids API keys or personal data. A later version could add AI-written caption suggestions, narration, and more transition styles.

## Troubleshooting
- If `streamlit` is not found, ensure the virtual environment is active and run `pip install -r requirements.txt`.
- If video export fails, reinstall dependencies with `pip install --upgrade -r requirements.txt`.
- Use short MP3/WAV files for background audio; only use music you own or are licensed to use.
- Keep image files reasonably sized for faster rendering.

## Project structure
```
ai_property_video_generator/
├── app.py
├── requirements.txt
├── README.md
└── output/
```

## Privacy and submission notes
- Use synthetic/sample listing data when sharing the assignment.
- Do not include API keys, passwords, or real customer personal information.
- The `output/` folder is where the generated MP4 is saved.
