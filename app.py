import io
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError
import streamlit as st
import numpy as np

try:
    from rembg import remove
    rembg_available = True
except ImportError:
    rembg_available = False

st.set_page_config(page_title="Vibrant Needlepoint Pattern Generator", layout="wide")

st.title("🪡 Vibrant Needlepoint Ornament Generator")
st.write("Upload your photo to get a high-vibrancy pattern chart designed for a 3.5\" circular ornament.")

num_colors = st.sidebar.slider("Number of Vibrant Thread Colors", min_value=6, max_value=32, value=18, step=1)
cell_size = st.sidebar.slider("Grid Zoom / Cell Pixel Size", min_value=12, max_value=30, value=18, step=2)
use_circular_crop = st.sidebar.checkbox("Crop to Circle (Ornament Ready)", value=True)

def kmeans_color_reduction(image_array, n_colors):
    pixels = image_array.reshape(-1, 3).astype(float)
    indices = np.random.choice(len(pixels), n_colors, replace=False)
    centroids = pixels[indices]
    for _ in range(50):
        distances = np.sqrt(((pixels - centroids[:, np.newaxis])**2).sum(axis=2))
        cluster_labels = np.argmin(distances, axis=0)
        new_centroids = np.array([pixels[cluster_labels == i].mean(axis=0) for i in range(n_colors)])
        if np.all(centroids == new_centroids):
            break
        centroids = new_centroids
    quantized_pixels = centroids[cluster_labels]
    quantized_image_array = quantized_pixels.reshape(image_array.shape).astype(np.uint8)
    return Image.fromarray(quantized_image_array, 'RGB')

uploaded_file = st.file_uploader("Choose an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    try:
        original_image = Image.open(uploaded_file).convert("RGB")
        orig_w, orig_h = original_image.size
        aspect_ratio = orig_h / orig_w

        col1, col2 = st.columns([1, 1.5])
        with col1:
            st.subheader("Original Image")
            st.image(original_image, use_container_width=True)

        working_image = original_image
        crop_width = orig_w
        crop_height = orig_h
        
        if use_circular_crop:
            min_dim = min(orig_w, orig_h)
            left = (orig_w - min_dim) // 2
            top = (orig_h - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim
            working_image = working_image.crop((left, top, right, bottom))
            crop_width = min_dim
            crop_height = min_dim

        rec_width = 90
        rec_height = int(rec_width * (crop_height / crop_width))

        with col2:
            st.subheader("🛠️ Settings & Preview")
            st.write(f"Recommended grid width: **{rec_width} stitches** (height: **{rec_height} stitches**) using **{num_colors} vibrant colors**.")

        st.markdown("---")
        grid_width = st.slider("Adjust Canvas Width (Stitches)", min_value=50, max_value=150, value=rec_width, step=5)
        grid_height = int(grid_width * (crop_height / crop_width))

        if st.button("Generate Vibrant Pattern Canvas", type="primary"):
            with st.spinner("Processing image..."):
                img_array = np.array(working_image)
                quantized_image = kmeans_color_reduction(img_array, num_colors)
                small_image = quantized_image.resize((grid_width, grid_height), Image.Resampling.NEAREST)
                unique_colors = sorted(list(set(small_image.getdata())))
                preview_image = small_image.resize((grid_width * cell_size, grid_height * cell_size), Image.Resampling.NEAREST)

                draw = ImageDraw.Draw(preview_image)
                for x in range(0, grid_width * cell_size, cell_size):
                    draw.line([(x, 0), (x, grid_height * cell_size)], fill=(160, 160, 160))
                for y in range(0, grid_height * cell_size, cell_size):
                    draw.line([(0, y), (grid_width * cell_size, y)], fill=(160, 160, 160))
                
                if use_circular_crop:
                    center_x = grid_width * cell_size // 2
                    center_y = grid_height * cell_size // 2
                    radius = min(grid_width, grid_height) * cell_size // 2
                    draw.ellipse([(center_x - radius, center_y - radius), (center_x + radius, center_y + radius)], outline="black", width=2)

            st.success("Pattern generated successfully!")
            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("Printable Pattern Canvas")
                st.image(preview_image, use_container_width=True)
                buf = io.BytesIO()
                preview_image.save(buf, format="PNG")
                st.download_button(label="Download Pattern Chart (.png)", data=buf.getvalue(), file_name="vibrant_needlepoint_chart.png", mime="image/png")

            with c2:
                st.subheader("Color Palette & Legend")
                for i, color in enumerate(unique_colors):
                    swatch = Image.new("RGB", (30, 30), color)
                    sw = io.BytesIO()
                    swatch.save(sw, format="PNG")
                    col_a, col_b = st.columns([1, 5])
                    with col_a:
                        st.image(sw, width=30)
                    with col_b:
                        st.write(f"**Color #{i+1}** — RGB: `{color}`")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
