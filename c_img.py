import hashlib
import io
import zipfile
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError


# =========================================================
# PAGE SETTINGS
# =========================================================
st.set_page_config(
    page_title="Multiple Image Cropper",
    page_icon="✂️",
    layout="wide"
)

st.title("✂️ Multiple Image Cropper")

st.write(
    "Upload multiple images, crop each image using the controls, "
    "save the crops, and download all cropped images in one ZIP file."
)

st.info(
    "This version does not require the streamlit-cropper package. "
    "Use the crop-position controls to select the required part of the image."
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def create_image_id(file_name, file_bytes, position):
    """
    Create a unique ID for every uploaded image.
    """

    file_hash = hashlib.sha256(file_bytes).hexdigest()[:15]

    return f"{position}_{file_name}_{file_hash}"


def open_uploaded_image(file_bytes):
    """
    Open an uploaded image and correct its orientation.
    """

    image = Image.open(io.BytesIO(file_bytes))

    # Correct rotation of mobile-camera images
    image = ImageOps.exif_transpose(image)

    image.load()

    return image


def get_output_extension(original_name, output_format):
    """
    Decide which extension should be used.
    """

    if output_format == "Keep original format":

        original_extension = Path(original_name).suffix.lower()

        if original_extension in [".jpg", ".jpeg"]:
            return ".jpg"

        elif original_extension == ".webp":
            return ".webp"

        else:
            return ".png"

    extensions = {
        "PNG": ".png",
        "JPG": ".jpg",
        "WEBP": ".webp"
    }

    return extensions[output_format]


def prepare_image_for_saving(image, extension):
    """
    Convert image mode according to the selected format.
    """

    if extension == ".jpg":

        # JPEG does not support transparency
        if image.mode in ["RGBA", "LA"]:

            background = Image.new(
                "RGB",
                image.size,
                "white"
            )

            if image.mode == "RGBA":
                alpha = image.getchannel("A")
                background.paste(
                    image.convert("RGB"),
                    mask=alpha
                )

            else:
                background.paste(
                    image.convert("RGB")
                )

            return background

        return image.convert("RGB")

    elif extension == ".webp":

        if image.mode not in ["RGB", "RGBA"]:
            return image.convert("RGBA")

        return image

    else:

        if image.mode not in ["RGB", "RGBA"]:
            return image.convert("RGBA")

        return image


def convert_image_to_bytes(
    image,
    extension,
    image_quality
):
    """
    Convert a PIL image into downloadable bytes.
    """

    image_buffer = io.BytesIO()

    image = prepare_image_for_saving(
        image,
        extension
    )

    if extension == ".jpg":

        image.save(
            image_buffer,
            format="JPEG",
            quality=image_quality,
            optimize=True
        )

    elif extension == ".webp":

        image.save(
            image_buffer,
            format="WEBP",
            quality=image_quality,
            method=6
        )

    else:

        image.save(
            image_buffer,
            format="PNG",
            optimize=True
        )

    return image_buffer.getvalue()


def create_output_name(
    original_name,
    extension,
    used_names
):
    """
    Create a unique output filename.
    """

    original_stem = Path(original_name).stem

    base_name = f"{original_stem}_cropped"

    output_name = f"{base_name}{extension}"

    number = 2

    while output_name.lower() in used_names:

        output_name = (
            f"{base_name}_{number}{extension}"
        )

        number += 1

    used_names.add(output_name.lower())

    return output_name


def create_zip_file(saved_crops):
    """
    Put all cropped images into one ZIP file.
    """

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED
    ) as zip_file:

        for crop_information in saved_crops.values():

            zip_file.writestr(
                crop_information["output_name"],
                crop_information["image_bytes"]
            )

    return zip_buffer.getvalue()


def resize_image(
    image,
    resize_enabled,
    target_width,
    target_height
):
    """
    Resize the cropped image if resizing is enabled.
    """

    if not resize_enabled:
        return image

    resized_image = image.resize(
        (
            int(target_width),
            int(target_height)
        ),
        Image.Resampling.LANCZOS
    )

    return resized_image


def calculate_aspect_ratio_crop(
    image_width,
    image_height,
    ratio_width,
    ratio_height
):
    """
    Calculate a centred crop box for a selected aspect ratio.
    """

    required_ratio = ratio_width / ratio_height
    image_ratio = image_width / image_height

    if image_ratio > required_ratio:

        crop_height = image_height
        crop_width = int(
            crop_height * required_ratio
        )

    else:

        crop_width = image_width
        crop_height = int(
            crop_width / required_ratio
        )

    left = int(
        (image_width - crop_width) / 2
    )

    top = int(
        (image_height - crop_height) / 2
    )

    right = left + crop_width
    bottom = top + crop_height

    return left, top, right, bottom


def draw_crop_rectangle(
    image,
    left,
    top,
    right,
    bottom
):
    """
    Draw the selected crop area over the original image.
    """

    preview_image = image.convert("RGB").copy()

    drawing = ImageDraw.Draw(preview_image)

    line_width = max(
        3,
        int(min(image.size) * 0.008)
    )

    drawing.rectangle(
        [
            left,
            top,
            right,
            bottom
        ],
        outline="red",
        width=line_width
    )

    return preview_image


# =========================================================
# SESSION STATE
# =========================================================
if "saved_crops" not in st.session_state:

    st.session_state.saved_crops = {}


if "uploaded_signature" not in st.session_state:

    st.session_state.uploaded_signature = ()


# =========================================================
# SIDEBAR SETTINGS
# =========================================================
st.sidebar.header("Output Settings")


output_format = st.sidebar.selectbox(
    "Output format",
    [
        "Keep original format",
        "PNG",
        "JPG",
        "WEBP"
    ]
)


image_quality = st.sidebar.slider(
    "JPG or WEBP quality",
    min_value=20,
    max_value=100,
    value=92
)


resize_enabled = st.sidebar.checkbox(
    "Resize all cropped images",
    value=False
)


if resize_enabled:

    target_width = st.sidebar.number_input(
        "Output width in pixels",
        min_value=1,
        max_value=10000,
        value=600,
        step=1
    )

    target_height = st.sidebar.number_input(
        "Output height in pixels",
        min_value=1,
        max_value=10000,
        value=600,
        step=1
    )

else:

    target_width = 600
    target_height = 600


st.sidebar.header("Aspect Ratio")


aspect_ratio_choice = st.sidebar.selectbox(
    "Crop aspect ratio",
    [
        "Free Crop",
        "1:1 Square",
        "35:45 Passport",
        "4:3 Landscape",
        "3:4 Portrait",
        "16:9 Widescreen",
        "9:16 Mobile"
    ]
)


aspect_ratios = {
    "Free Crop": None,
    "1:1 Square": (1, 1),
    "35:45 Passport": (35, 45),
    "4:3 Landscape": (4, 3),
    "3:4 Portrait": (3, 4),
    "16:9 Widescreen": (16, 9),
    "9:16 Mobile": (9, 16)
}


# =========================================================
# MULTIPLE FILE UPLOADER
# =========================================================
uploaded_files = st.file_uploader(
    "Upload multiple images",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
        "bmp",
        "tif",
        "tiff"
    ],
    accept_multiple_files=True
)


if not uploaded_files:

    st.warning(
        "Upload at least one image to begin."
    )

    st.stop()


# =========================================================
# PREPARE IMAGE RECORDS
# =========================================================
image_records = []


for position, uploaded_file in enumerate(uploaded_files):

    file_bytes = uploaded_file.getvalue()

    image_id = create_image_id(
        uploaded_file.name,
        file_bytes,
        position
    )

    image_records.append(
        {
            "id": image_id,
            "name": uploaded_file.name,
            "bytes": file_bytes
        }
    )


current_signature = tuple(
    record["id"]
    for record in image_records
)


# Remove old crops belonging to removed files
if (
    current_signature
    != st.session_state.uploaded_signature
):

    current_image_ids = set(
        current_signature
    )

    st.session_state.saved_crops = {
        image_id: crop_information
        for image_id, crop_information
        in st.session_state.saved_crops.items()
        if image_id in current_image_ids
    }

    st.session_state.uploaded_signature = (
        current_signature
    )


# =========================================================
# PROGRESS
# =========================================================
total_images = len(image_records)


saved_count = sum(
    1
    for record in image_records
    if record["id"]
    in st.session_state.saved_crops
)


progress_value = (
    saved_count / total_images
    if total_images > 0
    else 0
)


st.progress(progress_value)


st.write(
    f"**Saved images: {saved_count} "
    f"out of {total_images}**"
)


# =========================================================
# IMAGE SELECTOR
# =========================================================
def display_image_name(image_record):
    """
    Display image name and saved status.
    """

    if (
        image_record["id"]
        in st.session_state.saved_crops
    ):

        status = "✅ Saved"

    else:

        status = "⬜ Not saved"

    return (
        f"{image_record['name']} | {status}"
    )


selected_record = st.selectbox(
    "Select an image to crop",
    options=image_records,
    format_func=display_image_name
)


selected_image_id = selected_record["id"]


# =========================================================
# OPEN SELECTED IMAGE
# =========================================================
try:

    original_image = open_uploaded_image(
        selected_record["bytes"]
    )

except (
    UnidentifiedImageError,
    OSError,
    ValueError
) as error:

    st.error(
        f"Could not open "
        f"{selected_record['name']}."
    )

    st.exception(error)

    st.stop()


image_width = original_image.width
image_height = original_image.height


# =========================================================
# UNIQUE KEYS FOR CURRENT IMAGE
# =========================================================
left_key = f"left_{selected_image_id}"
top_key = f"top_{selected_image_id}"
right_key = f"right_{selected_image_id}"
bottom_key = f"bottom_{selected_image_id}"


# Set default crop coordinates
if left_key not in st.session_state:

    st.session_state[left_key] = 0


if top_key not in st.session_state:

    st.session_state[top_key] = 0


if right_key not in st.session_state:

    st.session_state[right_key] = image_width


if bottom_key not in st.session_state:

    st.session_state[bottom_key] = image_height


# Keep saved values inside image dimensions
st.session_state[left_key] = min(
    st.session_state[left_key],
    max(0, image_width - 1)
)


st.session_state[top_key] = min(
    st.session_state[top_key],
    max(0, image_height - 1)
)


st.session_state[right_key] = min(
    max(1, st.session_state[right_key]),
    image_width
)


st.session_state[bottom_key] = min(
    max(1, st.session_state[bottom_key]),
    image_height
)


# =========================================================
# APPLY ASPECT RATIO OR RESET
# =========================================================
button_column_1, button_column_2 = (
    st.columns(2)
)


with button_column_1:

    apply_ratio_button = st.button(
        "📐 Apply Selected Aspect Ratio",
        use_container_width=True,
        disabled=(
            aspect_ratio_choice
            == "Free Crop"
        )
    )


with button_column_2:

    reset_crop_button = st.button(
        "🔄 Reset Crop Area",
        use_container_width=True
    )


if apply_ratio_button:

    selected_ratio = aspect_ratios[
        aspect_ratio_choice
    ]

    ratio_width = selected_ratio[0]
    ratio_height = selected_ratio[1]

    (
        new_left,
        new_top,
        new_right,
        new_bottom
    ) = calculate_aspect_ratio_crop(
        image_width,
        image_height,
        ratio_width,
        ratio_height
    )

    st.session_state[left_key] = new_left
    st.session_state[top_key] = new_top
    st.session_state[right_key] = new_right
    st.session_state[bottom_key] = new_bottom

    st.rerun()


if reset_crop_button:

    st.session_state[left_key] = 0
    st.session_state[top_key] = 0
    st.session_state[right_key] = image_width
    st.session_state[bottom_key] = image_height

    st.rerun()


# =========================================================
# CROP COORDINATE CONTROLS
# =========================================================
st.subheader(
    f"Crop: {selected_record['name']}"
)


st.caption(
    f"Original image size: "
    f"{image_width} × {image_height} pixels"
)


control_column_1, control_column_2 = (
    st.columns(2)
)


with control_column_1:

    left = st.slider(
        "Left position",
        min_value=0,
        max_value=max(0, image_width - 1),
        key=left_key
    )


    top = st.slider(
        "Top position",
        min_value=0,
        max_value=max(0, image_height - 1),
        key=top_key
    )


with control_column_2:

    right = st.slider(
        "Right position",
        min_value=1,
        max_value=image_width,
        key=right_key
    )


    bottom = st.slider(
        "Bottom position",
        min_value=1,
        max_value=image_height,
        key=bottom_key
    )


# =========================================================
# VALIDATE CROP AREA
# =========================================================
crop_is_valid = True


if right <= left:

    crop_is_valid = False

    st.error(
        "The right position must be greater "
        "than the left position."
    )


if bottom <= top:

    crop_is_valid = False

    st.error(
        "The bottom position must be greater "
        "than the top position."
    )


# =========================================================
# PREVIEW AND CROPPED IMAGE
# =========================================================
if crop_is_valid:

    selected_width = right - left
    selected_height = bottom - top


    st.write(
        f"**Selected crop size:** "
        f"{selected_width} × "
        f"{selected_height} pixels"
    )


    rectangle_preview = draw_crop_rectangle(
        original_image,
        left,
        top,
        right,
        bottom
    )


    cropped_image = original_image.crop(
        (
            left,
            top,
            right,
            bottom
        )
    )


    final_preview = resize_image(
        cropped_image.copy(),
        resize_enabled,
        target_width,
        target_height
    )


    preview_column_1, preview_column_2 = (
        st.columns(2)
    )


    with preview_column_1:

        st.subheader("Selected Area")

        st.image(
            rectangle_preview,
            use_container_width=True
        )

        st.caption(
            "The red rectangle shows the "
            "selected crop area."
        )


    with preview_column_2:

        st.subheader("Cropped Preview")

        st.image(
            final_preview,
            use_container_width=True
        )

        st.caption(
            f"Final output size: "
            f"{final_preview.width} × "
            f"{final_preview.height} pixels"
        )


# =========================================================
# SAVE OR REMOVE CROP
# =========================================================
save_column, remove_column = st.columns(2)


with save_column:

    save_crop_button = st.button(
        "💾 Save This Crop",
        type="primary",
        use_container_width=True,
        disabled=not crop_is_valid
    )


with remove_column:

    remove_crop_button = st.button(
        "🗑️ Remove Saved Crop",
        use_container_width=True,
        disabled=(
            selected_image_id
            not in st.session_state.saved_crops
        )
    )


if save_crop_button and crop_is_valid:

    final_cropped_image = resize_image(
        cropped_image.copy(),
        resize_enabled,
        target_width,
        target_height
    )


    output_extension = get_output_extension(
        selected_record["name"],
        output_format
    )


    used_names = {
        crop_information[
            "output_name"
        ].lower()
        for image_id, crop_information
        in st.session_state.saved_crops.items()
        if image_id != selected_image_id
    }


    output_name = create_output_name(
        selected_record["name"],
        output_extension,
        used_names
    )


    output_bytes = convert_image_to_bytes(
        final_cropped_image,
        output_extension,
        image_quality
    )


    st.session_state.saved_crops[
        selected_image_id
    ] = {
        "original_name":
            selected_record["name"],

        "output_name":
            output_name,

        "image_bytes":
            output_bytes,

        "width":
            final_cropped_image.width,

        "height":
            final_cropped_image.height
    }


    st.success(
        f"Saved successfully: {output_name}"
    )

    st.rerun()


if remove_crop_button:

    st.session_state.saved_crops.pop(
        selected_image_id,
        None
    )

    st.success(
        "The saved crop was removed."
    )

    st.rerun()


# =========================================================
# SAVED IMAGES AND ZIP DOWNLOAD
# =========================================================
st.divider()

st.subheader("Saved Cropped Images")


if not st.session_state.saved_crops:

    st.warning(
        "No cropped images have been saved yet."
    )

else:

    for image_record in image_records:

        saved_crop = (
            st.session_state.saved_crops.get(
                image_record["id"]
            )
        )

        if saved_crop:

            st.write(
                f"✅ **{saved_crop['output_name']}** "
                f"({saved_crop['width']} × "
                f"{saved_crop['height']} pixels)"
            )


    zip_file_bytes = create_zip_file(
        st.session_state.saved_crops
    )


    st.download_button(
        label=(
            f"📦 Download "
            f"{len(st.session_state.saved_crops)} "
            f"Cropped Images as ZIP"
        ),
        data=zip_file_bytes,
        file_name="cropped_images.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True
    )


    unsaved_count = (
        total_images - saved_count
    )


    if unsaved_count > 0:

        st.warning(
            f"{unsaved_count} uploaded image(s) "
            f"have not been saved. Only saved "
            f"images will be included in the ZIP."
        )

    else:

        st.success(
            "All uploaded images have been "
            "cropped and saved."
        )