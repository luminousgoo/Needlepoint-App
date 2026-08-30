import io
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError
import streamlit as st
import numpy as np
# Try to import optional background remover
try:
    from rembg import remove
    rembg_available = True
except ImportError:
    rembg_available = False
    st.sidebar.warning("⚠️ Install 'rembg' to enable Background Removal: pip install rembg")

st.set_page_config(page_title="Vibrant Needlepoint Pattern Generator", layout="wide")

st.title("🪡 Vibrant Needlepoint Ornament Generator (K-Means)")
st.write("Upload your photo and get a high-vibrancy pattern chart designed for a 3.5\" circular ornament.")

# --- Sidebar: Advanced Settings ---
st.sidebar.header("Vibrancy & Cropping Settings")
num_colors = st.sidebar.slider("Number of Vibrant Thread Colors", min_value=6, max_value=32, value=18, step=1)
cell_size = st.sidebar.slider("Grid Zoom / Cell Pixel Size", min_value=12, max_value=30, value=18, step=2)

st.sidebar.markdown("---")
use_circular_crop = st.sidebar.checkbox("Crop to Circle (Ornament Ready)", value=True)
if rembg_available:
    use_bg_remover = st.sidebar.checkbox("Remove Background (Keeps foreground vibrant)", value=False)
else:
    use_bg_remover = False
    st.sidebar.info("Background Removal not available (rembg library missing).")

# --- Core Function: K-Means Color Reduction (More Vibrant than Median Cut) ---
def kmeans_color_reduction(image_array, n_colors):
    """
    Reduces colors using K-Means clustering instead of PIL's built-in quantize.
    This preserves vibrancy better by finding actual dominant colors in RGB space.
    Returns a Pillow image with the reduced palette.
    """
    # Reshape image data: 2D array of pixels (H*W, 3)
    pixels = image_array.reshape(-1, 3).astype(float)

    # Initialize centroids (seed points) randomly from the image pixels
    indices = np.random.choice(len(pixels), n_colors, replace=False)
    centroids = pixels[indices]

    # Run K-Means algorithm (max iterations 50 for speed)
    for _ in range(50):
        # 1. Assign each pixel to the closest centroid
        distances = np.sqrt(((pixels - centroids[:, np.newaxis])**2).sum(axis=2))
        cluster_labels = np.argmin(distances, axis=0)

        # 2. Update centroids to be the mean of their assigned pixels
        new_centroids = np.array([pixels[cluster_labels == i].mean(axis=0) for i in range(n_colors)])
        
        # Check for convergence (if centroids stop moving significantly)
        if np.all(centroids == new_centroids):
            break
        centroids = new_centroids

    # Replace pixel values with their assigned centroid color
    quantized_pixels = centroids[cluster_labels]
    quantized_image_array = quantized_pixels.reshape(image_array.shape).astype(np.uint8)
    
    return Image.fromarray(quantized_image_array, 'RGB')

# --- Main App Logic ---
uploaded_file = st.file_uploader("Choose an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
  try:
    original_image = Image.open(uploaded_file).convert("RGB")
  except UnidentifiedImageError:
    st.error("Error: Could not identify the image file. Please try a standard format.")
    st.stop()

  orig_w, orig_h = original_image.size
  aspect_ratio = orig_h / orig_w

  col1, col2 = st.columns([1, 1.5])
  with col1:
    st.subheader("Original Image")
    st.image(original_image, use_container_width=True)

  # --- Step 1: Apply Optional Background Removal ---
  working_image = original_image
  if use_bg_remover and rembg_available:
      with st.spinner("Removing background to isolate subjects..."):
          # rembg works best on the raw bytes
          uploaded_file.seek(0)
          input_bytes = uploaded_file.read()
          output_bytes = remove(input_bytes)
          working_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
          st.info("Background removed. The colors of your subjects will be prioritized.")

  # --- Step 2: Apply Optional Circular Crop ---
  crop_width = orig_w
  crop_height = orig_h
  
  if use_circular_crop:
      # Create a square crop to center the circle
      min_dim = min(orig_w, orig_h)
      left = (orig_w - min_dim) // 2
      top = (orig_h - min_dim) // 2
      right = left + min_dim
      bottom = top + min_dim
      working_image = working_image.crop((left, top, right, bottom))
      crop_width = min_dim
      crop_height = min_dim
      st.info("Cropped centrally to a square for circular ornament sizing.")

  # --- Step 3: Automated Recommendation Logic (Optimized for 3.5" Ornament) ---
  # For a high-def look on a 3.5" ornament (approx 14-count canvas), 90 stitches wide is the sweet spot.
  rec_width = 90
  rec_height = int(rec_width * (crop_height / crop_width))
  rec_colors = num_colors  # Sync with slider

  with col2:
    st.subheader("🛠️ Pattern Settings & Preview")
    st.write(f"**Target Output:** 3.5\" Circular Ornament")
    st.write(
        f"Based on your cropped image, we recommend a grid width of"
        f" **{rec_width} stitches** (height: **{rec_height} stitches**) using"
        f" **{rec_colors} vibrant colors**."
    )

  st.markdown("---")

  # Let user override recommendations
  grid_width = st.slider("Adjust Canvas Width (Stitches)", min_value=50, max_value=150, value=rec_width, step=5)
  grid_height = int(grid_width * (crop_height / crop_width))

  st.info(f"Current Selection: **{grid_width} x {grid_height} grid** for a total of **{grid_width * grid_height:,} stitches**.")

  if st.button("Generate Vibrant Pattern Canvas (K-Means)", type="primary"):
    with st.spinner("Processing image with high-vibrancy K-Means..."):
      # Convert to NumPy for K-Means
      img_array = np.array(working_image)
      
      # Handle Transparency (if background remover was used)
      if working_image.mode == 'RGBA':
          # Composite foreground onto a white background
          alpha = img_array[:, :, 3] / 255.0
          rgb = img_array[:, :, :3]
          white_background = np.ones_like(rgb) * 255
          comp_array = (rgb * alpha[..., np.newaxis] + white_background * (1 - alpha[..., np.newaxis])).astype(np.uint8)
          img_array = comp_array

      # Apply K-Means Color Reduction
      quantized_image = kmeans_color_reduction(img_array, num_colors)

      # Resize to target grid resolution (using NEAREST to keep pixels sharp)
      small_image = quantized_image.resize((grid_width, grid_height), Image.Resampling.NEAREST)
      
      # Extract final palette for legend
      paletted_pixels = small_image.getdata()
      unique_colors = sorted(list(set(paletted_pixels)))

      # Enlarge for preview
      preview_image = small_image.resize((grid_width * cell_size, grid_height * cell_size), Image.Resampling.NEAREST)

      # Add Grid Lines
      draw = ImageDraw.Draw(preview_image)
      for x in range(0, grid_width * cell_size, cell_size):
        draw.line([(x, 0), (x, grid_height * cell_size)], fill=(160, 160, 160))
      for y in range(0, grid_height * cell_size, cell_size):
        draw.line([(0, y), (grid_width * cell_size, y)], fill=(160, 160, 160))
      
      # Optional: Draw a circle overlay for the ornament guide
      if use_circular_crop:
          center_x = grid_width * cell_size // 2
          center_y = grid_height * cell_size // 2
          radius = min(grid_width, grid_height) * cell_size // 2
          draw.ellipse([(center_x - radius, center_y - radius), (center_x + radius, center_y + radius)], outline="black", width=2)

    st.success("Pattern generated successfully!")
    
    # Layout the pattern and the legend side-by-side
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Printable Pattern Canvas")
        if use_circular_crop:
             st.caption("Black circle is a guide for cutting out your stitched ornament.")
        st.image(preview_image, use_container_width=True)

        buf = io.BytesIO()
        preview_image.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="Download Pattern Chart (.png)",
            data=byte_im,
            file_name="vibrant_needlepoint_chart.png",
            mime="image/png",
        )

    with c2:
        st.subheader("Color Palette & Legend")
        st.caption(f"Mapping to the {num_colors} most vibrant colors.")
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

