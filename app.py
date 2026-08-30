import io
from PIL import Image, ImageDraw, ImageEnhance, UnidentifiedImageError
import streamlit as st

st.set_page_config(
    page_title="Ornament Needlepoint Pattern Generator", layout="centered"
)

st.title("🪡 Ornament-Grade Needlepoint Generator")
st.write(
    "Upload your photo to generate a soft, photo-realistic needlepoint pattern"
    " chart matching professional ornament mockups."
)

uploaded_file = st.file_uploader(
    "Choose an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
  try:
    original_image = Image.open(uploaded_file).convert("RGB")
  except UnidentifiedImageError:
    st.error("Error: Could not read image file. Please try another image.")
    st.stop()

  orig_w, orig_h = original_image.size
  aspect_ratio = orig_h / orig_w

  rec_width = 220
  rec_height = int(rec_width * aspect_ratio)
  rec_colors = 44

  col1, col2 = st.columns(2)
  with col1:
    st.subheader("Original Image")
    st.image(original_image, use_container_width=True)

  with col2:
    st.subheader("✨ Ornament Settings")
    st.write(
        f"Optimized for smooth gradients: **{rec_width} stitches** wide"
        f" (height: **{rec_height} stitches**) using **{rec_colors} harmonious"
        " colors**."
    )

  st.markdown("---")
  st.subheader("Fine-Tune Pattern Prompts")

  grid_width = st.slider(
      "Target Canvas Width (Stitches)",
      min_value=120,
      max_value=300,
      value=rec_width,
      step=10,
  )
  num_colors = st.slider(
      "Number of Thread Colors",
      min_value=24,
      max_value=64,
      value=rec_colors,
      step=2,
  )
  # Limited, subtle saturation adjustments
  color_balance = st.slider(
      "Natural Color Balance (Saturation)",
      min_value=0.8,
      max_value=1.5,
      value=1.1,
      step=0.05,
  )
  cell_size = st.slider(
      "Grid Zoom / Cell Pixel Size", min_value=20, max_value=60, value=36, step=4
  )

  grid_height = int(grid_width * aspect_ratio)

  # Calculate approximate physical size based on standard 14-count canvas mesh
  mesh_count = 14
  width_inches = grid_width / mesh_count
  height_inches = grid_height / mesh_count

  st.info(
      f"Current Selection: **{grid_width} x {grid_height} grid** ("
      f"{grid_width * grid_height:,} total stitches) | Approx. Canvas Size (14-count):"
      f" **{width_inches:.1f}\" x {height_inches:.1f}\"** with **{num_colors}**"
      " colors."
  )

  if st.button("Generate Ornament Pattern Canvas", type="primary"):
    with st.spinner("Processing image and mapping colors..."):
      enhancer = ImageEnhance.Color(original_image)
      balanced_image = enhancer.enhance(color_balance)

      small_image = balanced_image.resize(
          (grid_width, grid_height), Image.Resampling.LANCZOS
      )

      quantized_image = small_image.quantize(
          colors=num_colors, method=Image.Quantize.MAXCOVERAGE
      ).convert("RGB")

      paletted_pixels = quantized_image.getdata()
      unique_colors = sorted(list(set(paletted_pixels)))

      preview_image = quantized_image.resize(
          (grid_width * cell_size, grid_height * cell_size),
          Image.Resampling.NEAREST,
      )

      draw = ImageDraw.Draw(preview_image)
      for x in range(0, grid_width * cell_size, cell_size):
        draw.line([(x, 0), (x, grid_height * cell_size)], fill=(200, 200, 200))
      for y in range(0, grid_height * cell_size, cell_size):
        draw.line([(0, y), (grid_width * cell_size, y)], fill=(200, 200, 200))

      st.session_state['preview_image'] = preview_image
      st.session_state['unique_colors'] = unique_colors
      st.session_state['generated'] = True

  if st.session_state.get('generated', False):
    st.success("Ornament pattern canvas generated successfully!")
    st.subheader("Printable Pattern Canvas")
    st.image(st.session_state['preview_image'], use_container_width=True)

    st.subheader("Color Palette & Legend")
    for i, color in enumerate(st.session_state['unique_colors']):
      swatch = Image.new("RGB", (30, 30), color)
      sw_buf = io.BytesIO()
      swatch.save(sw_buf, format="PNG")

      col_a, col_b = st.columns([1, 5])
      with col_a:
        st.image(sw_buf.getvalue(), width=30)
      with col_b:
        st.write(
            f"**Color #{i+1}** — RGB: `{color}` (Hex:"
            f" `#{color[0]:02x}{color[1]:02x}{color[2]:02x}`)"
        )

    buf = io.BytesIO()
    st.session_state['preview_image'].save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="Download Ornament Pattern Canvas (.png)",
        data=byte_im,
        file_name="ornament_needlepoint_canvas.png",
        mime="image/png",
    )
