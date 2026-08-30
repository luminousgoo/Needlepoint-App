import io
from PIL import Image, ImageDraw, ImageOps
import streamlit as st

st.set_page_config(
    page_title="DIY Needlepoint Pattern Generator", layout="centered"
)

st.title("🪡 DIY Needlepoint Ornament Generator")
st.write(
    "Upload any photo, choose your grid size and color count, and instantly generate a printable pattern chart!"
)

# Sidebar controls for customization
st.sidebar.header("Pattern Settings")
grid_width = st.sidebar.slider(
    "Stitch Width (Grid Size)", min_value=30, max_value=120, value=60, step=5
)
num_colors = st.sidebar.slider(
    "Max Colors (Palette Size)", min_value=4, max_value=24, value=12, step=1
)
cell_size = st.sidebar.slider(
    "Zoom / Cell Pixel Size", min_value=10, max_value=30, value=20, step=2
)

uploaded_file = st.file_uploader(
    "Choose an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
  # Load original image
  original_image = Image.open(uploaded_file).convert("RGB")

  col1, col2 = st.columns(2)
  with col1:
    st.subheader("Original Image")
    st.image(original_image, use_container_width=True)

  # Maintain aspect ratio for height calculation based on chosen width
  orig_w, orig_h = original_image.size
  aspect_ratio = orig_h / orig_w
  grid_height = int(grid_width * aspect_ratio)

  with col2:
    st.subheader("Grid Preview Info")
    st.write(f"**Grid Dimensions:** {grid_width} x {grid_height} stitches")
    st.write(f"**Total Stitches:** {grid_width * grid_height:,}")
    st.write(f"**Color Palette:** Up to {num_colors} colors")

  if st.button("Generate Pattern Chart", type="primary"):
    with st.spinner("Processing image and mapping colors..."):
      # Step 1: Shrink image down to target stitch grid size (Nearest neighbor preserves sharp pixels)
      small_image = original_image.resize(
          (grid_width, grid_height), Image.Resampling.NEAREST
      )

      # Step 2: Color-flatten / Quantize to reduce colors
      quantized_image = small_image.quantize(
          colors=num_colors, method=Image.Quantize.MEDIANCUT
      ).convert("RGB")

      # Extract unique palette colors present in the final image
      paletted_pixels = quantized_image.getdata()
      unique_colors = sorted(list(set(paletted_pixels)))

      # Step 3: Blow the image back up using Nearest Neighbor so individual stitches look like squares
      preview_image = quantized_image.resize(
          (grid_width * cell_size, grid_height * cell_size),
          Image.Resampling.NEAREST,
      )

      # Step 4: Draw grid lines over the enlarged image for readability
      draw = ImageDraw.Draw(preview_image)
      for x in range(0, grid_width * cell_size, cell_size):
        draw.line([(x, 0), (x, grid_height * cell_size)], fill=(200, 200, 200))
      for y in range(0, grid_height * cell_size, cell_size):
        draw.line([(0, y), (grid_width * cell_size, y)], fill=(200, 200, 200))

    st.success("Pattern generated successfully!")
    st.subheader("Printable Pattern Grid")
    st.image(preview_image, use_container_width=True)

    # Step 5: Build a Color Legend Checklist
    st.subheader("Color Palette & Legend")
    st.write(
        "Match these RGB swatches to your yarn or floss collection (e.g., DMC"
        " threads):"
    )

    # Display swatches and details in columns or table
    for i, color in enumerate(unique_colors):
      # Create a small color swatch block image
      swatch = Image.new("RGB", (30, 30), color)
      col_a, col_b = st.columns([1, 5])
      with col_a:
        st.image(swatch, width=30)
      with col_b:
        st.write(
            f"**Color #{i+1}** — RGB: `{color}` (Hex:"
            f" `#{color[0]:02x}{color[1]:02x}{color[2]:02x}`)"
        )

    # Provide a download button for the pattern image
    buf = io.BytesIO()
    preview_image.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="Download Pattern Image (.png)",
        data=byte_im,
        file_name="needlepoint_pattern.png",
        mime="image/png",
    )
