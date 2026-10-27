import os, io, math, tempfile, subprocess, textwrap
from pathlib import Path
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import imageio_ffmpeg

APP_DIR = Path(__file__).parent
OUT_DIR = APP_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Realty Assistant | Property Video Studio", page_icon="🏡", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
.stApp {background: radial-gradient(circle at 15% 0%, #fff4ee 0, #f7f8fc 35%, #eef2fb 100%);}
.block-container {padding-top: 1.3rem; max-width: 1250px;}
.hero {padding: 26px 30px; border-radius: 22px; color: white;
background: linear-gradient(120deg,#191b35 0%,#4e3b77 55%,#d47b63 100%);
box-shadow: 0 14px 35px #25254b22; margin-bottom: 18px;}
.hero h1 {font-size: 2.25rem; margin: 0 0 8px 0;}
.hero p {font-size: 1rem; opacity: .92; margin: 0;}
div[data-testid="stForm"] {background: #ffffffb8; border: 1px solid #e3e5ef; padding: 18px; border-radius: 18px;}
div[data-testid="stMetric"] {background:white; border:1px solid #e6e7ef; padding:12px; border-radius:14px;}
.small-note {color:#62677b; font-size:.88rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🏡 Realty Assistant · Property Video Studio</h1>
  <p>Turn listing details and property photos into a polished, share-ready promotional video — no video editor required.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for f in candidates:
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default()

def cover_crop(img, size):
    w, h = size
    img = img.convert("RGB")
    scale = max(w / img.width, h / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x, y = (nw-w)//2, (nh-h)//2
    return img.crop((x, y, x+w, y+h))

def wrap_text(draw, text, font, max_width):
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textbbox((0,0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    return lines

def rounded_rectangle(draw, xy, radius, fill):
    draw.rounded_rectangle(xy, radius=radius, fill=fill)

def create_scene(photo, title, subtitle, template, idx, total, size=(1280,720)):
    W,H = size
    if photo is None:
        bg = Image.new("RGB", size, (32,35,60))
    else:
        bg = cover_crop(photo, size)
    # Subtle cinematic treatment
    bg = ImageEnhance.Color(bg).enhance(0.88)
    overlay = Image.new("RGBA", size, (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    if template == "Luxury Noir":
        od.rectangle((0,0,W,H), fill=(9,13,28,68))
        od.rectangle((0,int(H*.61),W,H), fill=(13,15,30,205))
        accent=(239,185,115); primary=(255,255,255)
    elif template == "Fresh & Bright":
        od.rectangle((0,0,W,H), fill=(255,255,255,22))
        od.rectangle((0,int(H*.64),W,H), fill=(250,251,255,224))
        accent=(226,111,78); primary=(35,39,61)
    else: # Editorial
        od.rectangle((0,0,W,H), fill=(19,26,43,55))
        od.rectangle((0,int(H*.59),W,H), fill=(23,31,49,215))
        accent=(126,220,207); primary=(255,255,255)
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay)
    d = ImageDraw.Draw(bg)
    title_font=get_font(48,True); sub_font=get_font(25); label_font=get_font(18,True)
    # Brand pill
    rounded_rectangle(d,(52,42,310,88),18,(*accent,235))
    d.text((72,54),"REALTY ASSISTANT",font=label_font,fill=(20,24,40))
    # Text block
    y=int(H*.68)
    for line in wrap_text(d,title,title_font,W-110)[:2]:
        d.text((58,y),line,font=title_font,fill=primary,stroke_width=0)
        y += 58
    if subtitle:
        y += 3
        for line in wrap_text(d,subtitle,sub_font,W-120)[:2]:
            d.text((61,y),line,font=sub_font,fill=primary)
            y += 34
    # Progress indicator
    d.rounded_rectangle((58,H-35,W-58,H-27),radius=4,fill=(255,255,255,75))
    d.rounded_rectangle((58,H-35,58+int((W-116)*(idx+1)/max(total,1)),H-27),radius=4,fill=(*accent,255))
    d.text((W-180,40),f"{idx+1:02d} / {total:02d}",font=label_font,fill=primary)
    return bg.convert("RGB")

def make_video(images, titles, subtitles, template, out_path, seconds_per_scene, music_bytes=None):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        frame_paths=[]
        for i, (img, title, sub) in enumerate(zip(images,titles,subtitles)):
            scene=create_scene(img,title,sub,template,i,len(images))
            # Hold each scene for a few seconds; add gentle zoom via ffmpeg zoompan
            p=td/f"scene_{i:02d}.jpg"
            scene.save(p, quality=94)
            frame_paths.append(p)
        # Build a concat list with each still image duration
        concat=td/"concat.txt"
        with open(concat,"w",encoding="utf-8") as f:
            for p in frame_paths:
                f.write(f"file '{str(p).replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'\n")
                f.write(f"duration {float(seconds_per_scene):.2f}\n")
            f.write(f"file '{str(frame_paths[-1])}'\n")
        cmd=[ffmpeg,"-y","-f","concat","-safe","0","-i",str(concat),"-vf","scale=1280:720,format=yuv420p","-r","25","-c:v","libx264","-preset","medium","-crf","22","-movflags","+faststart"]
        audio_path=None
        if music_bytes:
            audio_path=td/"music"
            audio_path.write_bytes(music_bytes)
            cmd += ["-stream_loop","-1","-i",str(audio_path),"-shortest","-c:a","aac","-b:a","160k"]
        else:
            cmd += ["-an"]
        cmd += [str(out_path)]
        result=subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or "FFmpeg video export failed")[-1800:])
    return out_path

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### ✨ Studio settings")
    template = st.selectbox("Video template", ["Luxury Noir", "Fresh & Bright", "Editorial Teal"])
    duration = st.slider("Seconds per scene", 3, 7, 4)
    st.caption("Tip: 4–6 scenes make a great 20–35 second listing reel.")
    st.markdown("---")
    st.markdown("**Included features**")
    st.markdown("• 3 visual templates\\n• Auto captions from listing details\\n• MP4 export\\n• Optional music upload\\n• Graceful validation")

col1, col2 = st.columns([1.02, 0.98], gap="large")
with col1:
    st.markdown("### 🏠 Property details")
    with st.form("property_form"):
        property_name = st.text_input("Property / listing name", "Modern 2-BHK Apartment")
        location = st.text_input("Location", "Kalka, Himachal Pradesh")
        price = st.text_input("Price", "₹45 lakh")
        property_type = st.selectbox("Property type", ["Apartment", "Independent House", "Villa", "Studio", "Plot", "Commercial"])
        bedrooms = st.selectbox("Bedrooms", ["Studio", "1 BHK", "2 BHK", "3 BHK", "4+ BHK", "Not applicable"], index=2)
        features_text = st.text_area("Key features (one per line)", "Bright living room\\nModular kitchen\\nBalcony with a view\\nCovered parking")
        contact = st.text_input("Contact / CTA", "Book your site visit today")
        submitted = st.form_submit_button("✨ Build my video", use_container_width=True, type="primary")
    st.markdown('<p class="small-note">Use only property facts you can verify. Sample details are provided so you can test the app immediately.</p>', unsafe_allow_html=True)

with col2:
    st.markdown("### 📸 Photos & soundtrack")
    uploads = st.file_uploader("Upload 1–8 property photos", type=["jpg","jpeg","png","webp"], accept_multiple_files=True)
    music = st.file_uploader("Optional background music (royalty-free / licensed)", type=["mp3","wav","m4a"], accept_multiple_files=False)
    st.markdown("#### 🎞️ Scene plan")
    st.markdown("1. Opening title and location\\n2. Property highlights\\n3. Interior / exterior photo scenes\\n4. Price and key feature\\n5. Contact / enquiry call-to-action")
    st.info("No photos? The app creates elegant graphic scenes so you can preview the workflow. For a realistic property video, upload your own listing photos.")

def build_preview_images(uploaded_files):
    imgs=[]
    if uploaded_files:
        for f in uploaded_files[:8]:
            try:
                im=Image.open(io.BytesIO(f.getvalue())).convert("RGB")
                imgs.append(im)
            except Exception:
                pass
    if not imgs:
        # Built-in sample graphic scenes, not fake property photographs
        for i, color in enumerate([(35,45,75),(71,65,104),(40,88,96),(120,77,65)]):
            im=Image.new("RGB",(1280,720),color)
            d=ImageDraw.Draw(im)
            d.ellipse((850,-150,1450,450),fill=tuple(min(255,c+25) for c in color))
            d.rounded_rectangle((90,125,1190,590),radius=35,outline=(240,220,190),width=4)
            d.text((135,200),["YOUR PROPERTY","DESIGNED FOR LIVING","SPACE TO GROW","LET'S TALK"][i],font=get_font(50,True),fill=(255,255,255))
            d.text((140,285),"Upload real property photos for a personalised video",font=get_font(24),fill=(240,235,230))
            imgs.append(im)
    return imgs

if submitted:
    errors=[]
    if not property_name.strip(): errors.append("Please enter a property/listing name.")
    if not location.strip(): errors.append("Please enter the property location.")
    if not contact.strip(): errors.append("Please enter a contact or call-to-action.")
    if len(uploads or []) > 8: errors.append("Please upload no more than 8 photos.")
    if errors:
        for e in errors: st.error(e)
    else:
        features=[x.strip() for x in features_text.splitlines() if x.strip()]
        imgs=build_preview_images(uploads)
        # Align each photo with a scene and produce captions based only on supplied facts
        titles=[property_name, f"{property_type} in {location}", "Thoughtful details", price if price.strip() else "Enquire for pricing", "Make it yours"]
        subtitles=[
            f"{location} • {bedrooms}",
            "A closer look at the property",
            " • ".join(features[:3]) if features else "Explore the space",
            " • ".join(features[3:6]) if len(features)>3 else f"{bedrooms} • {property_type}",
            contact
        ]
        # use uploaded images first, then repeat them; built-in graphics only if none uploaded
        if uploads:
            imgs=imgs[:]
            while len(imgs)<len(titles): imgs.append(imgs[-1].copy())
        else:
            imgs=imgs[:len(titles)]
        out=OUT_DIR/"property_promo_video.mp4"
        with st.spinner("Creating your property video… this can take a minute."):
            try:
                make_video(imgs[:len(titles)],titles,subtitles,template,out,duration,music.getvalue() if music else None)
                st.success("Your video is ready!")
                st.video(str(out))
                with open(out,"rb") as vf:
                    st.download_button("⬇️ Download MP4 video", data=vf.read(), file_name=f"{property_name.strip().replace(' ','_')}_promo.mp4", mime="video/mp4", use_container_width=True)
                st.markdown("#### 📋 Video summary")
                m1,m2,m3=st.columns(3)
                m1.metric("Scenes",len(titles))
                m2.metric("Template",template)
                m3.metric("Estimated duration",f"~{len(titles)*duration}s")
            except Exception as e:
                st.error(f"Video export failed: {e}")
                st.info("Check the installation steps in README.md and try again.")

st.markdown("---")
st.markdown("### 🧪 Sample input → expected output")
a,b,c=st.columns(3)
a.metric("Input", "Listing + photos")
b.metric("Automation", "5 scenes")
c.metric("Output", "MP4 video")
st.caption("This demo uses a rule-based caption and scene layout. It does not invent amenities or verify listing claims. Add licensed music only.")
