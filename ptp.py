import streamlit as st
from PIL import Image
import io
import zipfile
import os


# -----------------------------
# Function: Crop image by aspect ratio
# -----------------------------
def crop_to_aspect_ratio(image, target_width, target_height):
    img_width, img_height = image.size
    target_ratio = target_width / target_height
    img_ratio = img_width / img_height

    if img_ratio > target_ratio:
        # Image is too wide, crop left and right
        new_width = int(img_height * target_ratio)
        left = (img_width - new_width) // 2
        right = left + new_width
        top = 0
        bottom = img_height
    else:
        # Image is too tall, crop top and bottom
        new_height = int(img_width / target_ratio)
        top = (img_height - new_height) // 2
        bottom = top + new_height
        left = 0
        right = img_width

    return image.crop((left, top, right, bottom))


# -----------------------------
# Function: Manual crop image
# -----------------------------
def manual_crop_image(image, left, top, right, bottom):
    img_width, img_height = image.size

    left = max(0, min(left, img_width - 1))
    top = max(0, min(top, img_height - 1))
    right = max(left + 1, min(right, img_width))
    bottom = max(top + 1, min(bottom, img_height))

    return image.crop((left, top, right, bottom))


# -----------------------------
# Function: Resize image
# -----------------------------
def resize_image(image, width, height):
    return image.resize((width, height), Image.LANCZOS)


# -----------------------------
# Function: Compress image to target KB
# -----------------------------
def compress_to_target_kb(image, target_kb, image_format="JPEG", dpi=(300, 300)):
    target_bytes = target_kb * 1024

    quality = 95
    min_quality = 10

    output = io.BytesIO()

    # Convert to RGB for JPEG
    if image_format == "JPEG":
        image = image.convert("RGB")

    while quality >= min_quality:
        output = io.BytesIO()

        image.save(
            output,
            format=image_format,
            quality=quality,
            optimize=True,
            dpi=dpi
        )

        size = output.tell()

        if size <= target_bytes:
            break

        quality -= 5

    # If still bigger, reduce image dimensions slightly
    while output.tell() > target_bytes and image.size[0] > 100 and image.size[1] > 100:
        new_width = int(image.size[0] * 0.90)
        new_height = int(image.size[1] * 0.90)

        image = image.resize((new_width, new_height), Image.LANCZOS)

        quality = 85
        output = io.BytesIO()

        image.save(
            output,
            format=image_format,
            quality=quality,
            optimize=True,
            dpi=dpi
        )

    output.seek(0)
    return output


# -----------------------------
# Function: Get image size in KB
# -----------------------------
def get_file_size_kb(file_bytes):
    return round(len(file_bytes.getvalue()) / 1024, 2)


# -----------------------------
# Streamlit Page Settings
# -----------------------------
st.set_page_config(
    page_title="Passport Size Picture Converter",
    page_icon="🖼️",
    layout="wide"
)


# -----------------------------
# App Title
# -----------------------------
st.title("🖼️ Passport Size Picture Converter")
st.write("Convert pictures to passport size, crop images, change resolution, resize image, and reduce file size in KB.")


# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("⚙️ Image Settings")

size_option = st.sidebar.selectbox(
    "Select Passport Size",
    [
        "Pakistan Passport Size - 35 x 45 mm",
        "CNIC Size - 35 x 45 mm",
        "Visa Size - 2 x 2 inch",
        "Custom Size"
    ]
)

dpi = st.sidebar.number_input(
    "Resolution / DPI",
    min_value=72,
    max_value=1200,
    value=300,
    step=10
)

# -----------------------------
# Size conversion
# pixels = inches × DPI
# 1 inch = 25.4 mm
# -----------------------------
if size_option == "Pakistan Passport Size - 35 x 45 mm":
    width_mm = 35
    height_mm = 45
    width_px = int((width_mm / 25.4) * dpi)
    height_px = int((height_mm / 25.4) * dpi)

elif size_option == "CNIC Size - 35 x 45 mm":
    width_mm = 35
    height_mm = 45
    width_px = int((width_mm / 25.4) * dpi)
    height_px = int((height_mm / 25.4) * dpi)

elif size_option == "Visa Size - 2 x 2 inch":
    width_px = int(2 * dpi)
    height_px = int(2 * dpi)

else:
    width_px = st.sidebar.number_input(
        "Custom Width in Pixels",
        min_value=50,
        max_value=5000,
        value=413,
        step=10
    )

    height_px = st.sidebar.number_input(
        "Custom Height in Pixels",
        min_value=50,
        max_value=5000,
        value=531,
        step=10
    )


st.sidebar.write(f"Final Width: **{width_px}px**")
st.sidebar.write(f"Final Height: **{height_px}px**")

image_format = st.sidebar.selectbox(
    "Output Format",
    ["JPEG", "PNG"]
)

target_kb = st.sidebar.number_input(
    "Target File Size in KB",
    min_value=5,
    max_value=2000,
    value=50,
    step=5
)


# -----------------------------
# Crop Controls
# -----------------------------
st.sidebar.header("✂️ Crop Settings")

crop_mode = st.sidebar.radio(
    "Select Crop Mode",
    [
        "Auto Crop to Passport Ratio",
        "Manual Crop",
        "No Crop"
    ]
)

manual_left = 0
manual_top = 0
manual_right = 0
manual_bottom = 0

if crop_mode == "Manual Crop":
    st.sidebar.write("Manual crop values are based on original image pixels.")

    manual_left = st.sidebar.number_input(
        "Crop Left",
        min_value=0,
        value=0,
        step=10
    )

    manual_top = st.sidebar.number_input(
        "Crop Top",
        min_value=0,
        value=0,
        step=10
    )

    manual_right = st.sidebar.number_input(
        "Crop Right",
        min_value=1,
        value=500,
        step=10
    )

    manual_bottom = st.sidebar.number_input(
        "Crop Bottom",
        min_value=1,
        value=500,
        step=10
    )


# -----------------------------
# Upload Images
# -----------------------------
uploaded_files = st.file_uploader(
    "Upload one or more images",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)


# -----------------------------
# Process Images
# -----------------------------
if uploaded_files:
    processed_images = []

    st.subheader("📷 Processed Images")

    for uploaded_file in uploaded_files:
        try:
            image = Image.open(uploaded_file)
            original_image = image.copy()

            original_size_kb = round(uploaded_file.size / 1024, 2)
            original_width, original_height = image.size

            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # -----------------------------
            # Apply crop according to user choice
            # -----------------------------
            if crop_mode == "Auto Crop to Passport Ratio":
                image = crop_to_aspect_ratio(image, width_px, height_px)

            elif crop_mode == "Manual Crop":
                image = manual_crop_image(
                    image,
                    manual_left,
                    manual_top,
                    manual_right,
                    manual_bottom
                )

            elif crop_mode == "No Crop":
                image = image

            # Resize image
            image = resize_image(image, width_px, height_px)

            # Compress image
            compressed_image = compress_to_target_kb(
                image=image,
                target_kb=target_kb,
                image_format=image_format,
                dpi=(dpi, dpi)
            )

            final_size_kb = get_file_size_kb(compressed_image)

            file_extension = "jpg" if image_format == "JPEG" else "png"
            output_filename = f"passport_{os.path.splitext(uploaded_file.name)[0]}.{file_extension}"

            processed_images.append(
                {
                    "filename": output_filename,
                    "file": compressed_image,
                    "original_size": original_size_kb,
                    "final_size": final_size_kb,
                    "image": image
                }
            )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                st.image(original_image, caption="Original Image", use_container_width=True)

            with col2:
                st.image(image, caption=output_filename, use_container_width=True)

            with col3:
                st.write(f"**Original File:** {uploaded_file.name}")
                st.write(f"**Original Size:** {original_size_kb} KB")
                st.write(f"**Original Dimensions:** {original_width} x {original_height} pixels")
                st.write(f"**Final Size:** {final_size_kb} KB")
                st.write(f"**Final Dimensions:** {width_px} x {height_px} pixels")
                st.write(f"**DPI:** {dpi}")
                st.write(f"**Crop Mode:** {crop_mode}")

                if crop_mode == "Manual Crop":
                    st.write(f"**Manual Crop Area:** Left {manual_left}, Top {manual_top}, Right {manual_right}, Bottom {manual_bottom}")

                st.download_button(
                    label="⬇️ Download This Image",
                    data=compressed_image,
                    file_name=output_filename,
                    mime=f"image/{file_extension}"
                )

            st.divider()

        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")

    # -----------------------------
    # Download all images as ZIP
    # -----------------------------
    if processed_images:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for item in processed_images:
                item["file"].seek(0)
                zip_file.writestr(item["filename"], item["file"].read())

        zip_buffer.seek(0)

        st.download_button(
            label="⬇️ Download All Images as ZIP",
            data=zip_buffer,
            file_name="passport_size_images.zip",
            mime="application/zip"
        )

else:
    st.info("Please upload images to start conversion.")