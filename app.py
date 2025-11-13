import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
import pytesseract
import io
import json
import csv
import re
import math
import base64
import uuid

# --- Configuration ---
st.set_page_config(layout="wide", page_title="ThankYouWall")

# --- Constants ---
EXPORT_WIDTH = 1080
EXPORT_HEIGHT = 1350
PFP_SIZE = 180  # Profile picture size in the final image
COLS = 3
PADDING = 40
GUTTER = 30

# --- Helper Functions ---

def blur_phone_numbers(text):
    """Finds and replaces phone numbers with a redacted string."""
    # This is a basic regex and can be improved
    phone_regex = re.compile(r'(\+?\d[\d\s-]{7,}\d)')
    return phone_regex.sub('[REDACTED PHONE]', text)

def extract_details_from_image(image_bytes):
    """
    Runs OCR on the image and returns heuristically extracted data.
    For this prototype, it's very basic: it OCRs and blurs.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Run OCR
        full_text = pytesseract.image_to_string(image)
        
        # --- Heuristics (Basic) ---
        # A real app would have complex regex for WhatsApp, iG, etc.
        # For now, we require manual editing.
        blurred_text = blur_phone_numbers(full_text)
        
        # Use first ~150 chars as excerpt
        message_excerpt = (blurred_text[:150] + '...') if len(blurred_text) > 150 else blurred_text
        
        # Create thumbnail
        thumb = image.copy()
        thumb.thumbnail((100, 100))
        thumb_bytes = io.BytesIO()
        thumb.save(thumb_bytes, format="PNG")
        
        return {
            "id": str(uuid.uuid4()),
            "name": "Wisher (Edit Me)",
            "message_excerpt": message_excerpt,
            "timestamp": "Timestamp (Edit Me)",
            "platform": "Unknown",
            "full_text_original": full_text,
            "full_text_blurred": blurred_text,
            "thumbnail": thumb_bytes.getvalue(),
            "profile_photo": None,  # Will be uploaded by user
            "include": True,
            "anonymize": False,
        }
    except Exception as e:
        st.error(f"Failed to process an image: {e}")
        return None

def create_initials_pfp(initials, size):
    """Creates a circular PFP with initials."""
    img = Image.new('RGB', (size, size), color='#CCCCCC')
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fall back to default if unavailable
    try:
        # You may need to change this path to a font file on your system
        font = ImageFont.truetype("Arial.ttf", size // 2)
    except IOError:
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size - text_width) / 2
    y = (size - text_height) / 2 - (size * 0.05) # Small vertical adjustment
    
    draw.text((x, y), initials, font=font, fill='#FFFFFF')
    return img

def create_circular_image(image, size):
    """Crops and masks an image to be a circle."""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Crop to square
    img_size = min(image.size)
    left = (image.width - img_size) / 2
    top = (image.height - img_size) / 2
    right = (image.width + img_size) / 2
    bottom = (image.height + img_size) / 2
    image = image.crop((left, top, right, bottom))
    
    # Resize
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    
    # Create mask
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    # Apply mask
    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    
    return output

def generate_export_image(wishes, header_text, anonymize_all):
    """Generates the final 1080x1350 PNG image."""
    
    # 1. Setup Base Image
    img = Image.new('RGB', (EXPORT_WIDTH, EXPORT_HEIGHT), color='white')
    draw = ImageDraw.Draw(img)
    
    # 2. Load Fonts (Ensure you have these fonts or change paths)
    try:
        font_header = ImageFont.truetype("Arial.ttf", 70)
        font_name = ImageFont.truetype("Arial.ttf", 28)
        font_msg = ImageFont.truetype("Arial.ttf", 22)
    except IOError:
        st.error("Arial.ttf not found. Using default font. Please install Arial or edit font paths.")
        font_header = ImageFont.load_default()
        font_name = ImageFont.load_default()
        font_msg = ImageFont.load_default()

    # 3. Draw Header
    header_bbox = draw.textbbox((0, 0), header_text, font=font_header)
    header_width = header_bbox[2] - header_bbox[0]
    draw.text(((EXPORT_WIDTH - header_width) / 2, PADDING), header_text, font=font_header, fill='black')
    
    # 4. Grid Calculation
    start_y = PADDING + (header_bbox[3] - header_bbox[1]) + PADDING
    item_width = (EXPORT_WIDTH - (PADDING * 2) - (GUTTER * (COLS - 1))) / COLS
    
    # 5. Draw Wishes
    current_x = PADDING
    current_y = start_y
    
    for wish in wishes:
        # 5a. Get Name/Message (and anonymize if needed)
        is_anon = anonymize_all or wish['anonymize']
        name = "A Kind Wisher" if is_anon else wish['name']
        message = "Sent a lovely message!" if is_anon else wish['message_excerpt'].split('\n')[0] # First line
        
        # 5b. Get/Create PFP
        if wish['profile_photo']:
            pfp_img = Image.open(io.BytesIO(wish['profile_photo'])).convert('RGB')
        else:
            initials = "".join([n[0] for n in name.split()[:2]]).upper()
            pfp_img = create_initials_pfp(initials, PFP_SIZE)
            
        pfp_circular = create_circular_image(pfp_img, PFP_SIZE)
        
        # 5c. Paste PFP
        pfp_x = current_x + (item_width - PFP_SIZE) / 2
        img.paste(pfp_circular, (int(pfp_x), int(current_y)), pfp_circular)
        
        # 5d. Draw Name
        name_bbox = draw.textbbox((0, 0), name, font=font_name)
        name_width = name_bbox[2] - name_bbox[0]
        name_y = current_y + PFP_SIZE + 15
        draw.text((current_x + (item_width - name_width) / 2, name_y), name, font=font_name, fill='black', align="center")
        
        # 5e. Draw Message (simple, one-line excerpt)
        msg_bbox = draw.textbbox((0, 0), message, font=font_msg)
        msg_width = msg_bbox[2] - msg_bbox[0]
        msg_y = name_y + (name_bbox[3] - name_bbox[1]) + 10
        
        # Basic wrap (for demo)
        if msg_width > item_width:
             message = message[:int(len(message) * (item_width / msg_width)) - 3] + "..."
             msg_bbox = draw.textbbox((0, 0), message, font=font_msg)
             msg_width = msg_bbox[2] - msg_bbox[0]

        draw.text((current_x + (item_width - msg_width) / 2, msg_y), message, font=font_msg, fill='#555555', align="center")
        
        # 5f. Update Grid Position
        current_x += item_width + GUTTER
        if current_x + item_width > EXPORT_WIDTH - PADDING:
            current_x = PADDING
            current_y += PFP_SIZE + 120 # Height of one item block
            
        if current_y + PFP_SIZE > EXPORT_HEIGHT:
            st.warning("Too many wishes to fit on one image! Only the first few will be shown.")
            break
            
    # 6. Save to Bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()

def get_metadata_json(wishes):
    """Generates a JSON string of all wish data."""
    export_data = []
    for wish in wishes:
        # Don't export image data, just metadata
        export_data.append({
            "id": wish['id'],
            "name": wish['name'],
            "message_excerpt": wish['message_excerpt'],
            "timestamp": wish['timestamp'],
            "platform": wish['platform'],
            "anonymized": wish['anonymize'],
            "included_in_export": wish['include'],
        })
    return json.dumps(export_data, indent=2)

def get_metadata_csv(wishes):
    """Generates a CSV string of all wish data."""
    if not wishes:
        return ""
        
    output = io.StringIO()
    fieldnames = ["id", "name", "message_excerpt", "timestamp", "platform", "anonymized", "included_in_export"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for wish in wishes:
        writer.writerow({
            "id": wish['id'],
            "name": wish['name'],
            "message_excerpt": wish['message_excerpt'],
            "timestamp": wish['timestamp'],
            "platform": wish['platform'],
            "anonymized": wish['anonymize'],
            "included_in_export": wish['include'],
        })
    return output.getvalue()


# --- Session State Management ---
if 'wishes' not in st.session_state:
    st.session_state.wishes = []
if 'processing' not in st.session_state:
    st.session_state.processing = False

def update_wish_field(wish_id, field):
    """Callback to update a field for a specific wish."""
    wish = next((w for w in st.session_state.wishes if w['id'] == wish_id), None)
    if wish:
        wish[field] = st.session_state[f"{field}_{wish_id}"]

def handle_pfp_upload(wish_id):
    """Callback to handle profile photo upload."""
    uploaded_file = st.session_state[f"pfp_upload_{wish_id}"]
    if uploaded_file:
        wish = next((w for w in st.session_state.wishes if w['id'] == wish_id), None)
        if wish:
            wish['profile_photo'] = uploaded_file.getvalue()

def remove_wish(wish_id):
    """Callback to remove a wish from the list."""
    st.session_state.wishes = [w for w in st.session_state.wishes if w['id'] != wish_id]


# --- Main App UI ---
st.title("🎂 ThankYouWall")
st.write("Convert your birthday screenshots into a tidy, shareable 'thank you' page.")

# --- Sidebar (Settings & Export) ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.text_input("Header Text", value="Thank you for your wishes!", key="header_text")
    st.checkbox("Anonymize all names/messages in export", key="anonymize_all")
    
    st.subheader("Cloud OCR")
    st.checkbox("Use Google Vision API", disabled=True, key="use_google_vision")
    st.info("Google Vision is not implemented in this prototype. We are using local Tesseract OCR.")

    st.header("📤 Export")
    
    # Filter wishes to be included in export
    included_wishes = [w for w in st.session_state.wishes if w['include']]
    num_included = len(included_wishes)
    
    st.write(f"**{num_included}** wishes selected for export.")

    if st.button("Generate Shareable Image (PNG)", type="primary", disabled=(num_included == 0)):
        with st.spinner("Generating your ThankYouWall..."):
            png_data = generate_export_image(
                included_wishes,
                st.session_state.header_text,
                st.session_state.anonymize_all
            )
            st.image(png_data, caption="Your 'ThankYouWall' Image", use_column_width=True)
            st.download_button("⬇️ Download PNG", png_data, file_name="ThankYouWall.png", mime="image/png")
    
    st.download_button(
        "Download Metadata (JSON)",
        data=get_metadata_json(st.session_state.wishes),
        file_name="wishes_metadata.json",
        mime="application/json",
        disabled=(len(st.session_state.wishes) == 0)
    )
    
    st.download_button(
        "Download Metadata (CSV)",
        data=get_metadata_csv(st.session_state.wishes),
        file_name="wishes_metadata.csv",
        mime="text/csv",
        disabled=(len(st.session_state.wishes) == 0)
    )

# --- Main Area (Upload & Edit) ---

# 1. Uploader
uploaded_files = st.file_uploader(
    "1. Upload your screenshots (PNG, JPG)",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key="file_uploader"
)

# 2. Process Button
if st.button("2. Process Uploaded Screenshots", type="primary", disabled=(not uploaded_files)):
    st.session_state.processing = True
    
    # Get names of already processed files
    processed_ids = [w['id'] for w in st.session_state.wishes]
    new_files_to_process = []
    
    # A simple way to avoid re-processing on button click.
    # In a real app, you'd use file hashes.
    # For this demo, we'll clear and re-process all for simplicity.
    st.session_state.wishes = [] 
    
    progress_bar = st.progress(0, text="Starting OCR... Please wait.")
    
    for i, file in enumerate(uploaded_files):
        progress_text = f"Processing image {i+1} of {len(uploaded_files)}: {file.name}"
        progress_bar.progress((i+1) / len(uploaded_files), text=progress_text)
        
        details = extract_details_from_image(file.getvalue())
        if details:
            details['id'] = file.name  # Use filename as ID to prevent duplicates
            st.session_state.wishes.append(details)
            
    progress_bar.empty()
    st.session_state.processing = False
    st.success(f"Processed {len(st.session_state.wishes)} images! You can now edit them below.")


# 3. Editor
st.header("3. Edit Wishes")
st.write("Review the extracted text, upload profile photos, and choose which wishes to include in the final image.")

if not st.session_state.wishes:
    st.info("Upload and process images to see the editor.")
else:
    for i, wish in enumerate(st.session_state.wishes):
        wish_id = wish['id'] # Use the unique ID
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 2, 1.5])
            
            # --- COLUMN 1: Controls & Photo ---
            with col1:
                st.image(wish['thumbnail'], width=100, caption="Original Screenshot")
                st.checkbox(
                    "Include in export", 
                    value=wish['include'], 
                    key=f"include_{wish_id}",
                    on_change=update_wish_field,
                    args=(wish_id, 'include')
                )
                
                # Show uploaded PFP or a placeholder
                if wish['profile_photo']:
                    st.image(wish['profile_photo'], width=100, caption="Profile Photo")
                else:
                    st.markdown("_(No PFP uploaded)_")

                st.file_uploader(
                    "Upload PFP",
                    type=["png", "jpg", "jpeg"],
                    key=f"pfp_upload_{wish_id}",
                    on_change=handle_pfp_upload,
                    args=(wish_id,)
                )

            # --- COLUMN 2: Editable Text ---
            with col2:
                st.text_input(
                    "Name", 
                    value=wish['name'], 
                    key=f"name_{wish_id}",
                    on_change=update_wish_field,
                    args=(wish_id, 'name')
                )
                st.text_area(
                    "Message Excerpt (for image)",
                    value=wish['message_excerpt'],
                    key=f"message_excerpt_{wish_id}",
                    on_change=update_wish_field,
                    args=(wish_id, 'message_excerpt'),
                    height=100,
                    help="This short text will appear on the final image. Keep it brief!"
                )
                st.text_input(
                    "Timestamp", 
                    value=wish['timestamp'], 
                    key=f"timestamp_{wish_id}",
                    on_change=update_wish_field,
                    args=(wish_id, 'timestamp')
                )

            # --- COLUMN 3: Meta & Danger Zone ---
            with col3:
                st.selectbox(
                    "Platform (for your ref)",
                    options=["Unknown", "WhatsApp", "Instagram", "Twitter/X", "LinkedIn", "Other"],
                    index=0, # Default to "Unknown"
                    key=f"platform_{wish_id}",
                    on_change=update_wish_field,
                    args=(wish_id, 'platform')
                )
                st.checkbox(
                    "Anonymize this entry",
                    value=wish['anonymize'],
                    key=f"anonymize_{wish_id}",
                    on_change=update_wish_field,
                    args=(wish_id, 'anonymize'),
                    help="Hides name and message in the final export."
                )
                
                st.button(
                    "Remove Wish",
                    key=f"remove_{wish_id}",
                    on_click=remove_wish,
                    args=(wish_id,),
                    type="secondary",
                    use_container_width=True
                )
                
                with st.expander("Show full OCR text (for reference)"):
                    st.text_area(
                        "Full OCR Text (Blurred)", 
                        value=wish['full_text_blurred'], 
                        height=200, 
                        disabled=True
                    )
