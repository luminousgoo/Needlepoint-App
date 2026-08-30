import io
from PIL import Image, ImageDraw, ImageEnhance, UnidentifiedImageError
import streamlit as st

st.set_page_config(
    page_title="DIY Needlepoint Pattern Generator", layout="centered"
)

st.title("🪡 High-Detail Needlepoint Ornament Generator")
st.write(
    "Upload any photo to automatically generate a high-vibrancy, detailed"
    " ornament pattern chart."
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

  rec_width = 100
  rec_height = int(rec_width * aspect_ratio)
  rec_colors = 24

  col1, col2 = st.columns(2)
  with col1:
    st.subheader("Original Image")
    st.image(original_image, use_container_width=True)

  with col2:
    st.subheader("✨ High-Detail Settings")
    st.write(
        f"Optimized for ornament mockup quality: **{rec_width} stitches** wide"
        f" (height: **{rec_height} stitches**) using **{rec_colors} colors** for"
        " maximum clarity."
    )

  st.markdown("---")
  st.subheader("Adjust Pattern Prompts")

  grid_width = st.slider(
      "Target Canvas Width (Stitches)",
      min_value=50,
      max_value=150,
      value=rec_width,
      step=5,
  )
  num_colors = st.slider(
      "Number of Thread Colors",
      min_value=8,
      max_value=32,
      value=rec_colors,
      step=1,
  )
  color_boost = st.slider(
      "Color Vibrancy Boost",
      min_value=1.0,
      max_value=2.5,
      value=1.5,
      step=0.1,
  )
  contrast_boost = st.slider(
      "Detail Contrast Boost",
      min_value=1.0,
      max_value=2.0,
      value=1.2,
      step=0.1,
  )
  cell_size = st.slider(
      "Grid Zoom / Cell Pixel Size", min_value=10, max_value=30, value=18, step=2
  )

  grid_height = int(grid_width * aspect_ratio)

  st.info(
      f"Current Selection: **{grid_width} x {grid_height} grid** ("
      f"{grid_width * grid_height:,} total stitches) with **{num_colors}**"
      f" colors."
  )

  if st.button("Generate High-Detail Pattern Canvas", type="primary"):
    with st.spinner("Processing image, enhancing detail and vibrancy..."):
      enhancer_color = ImageEnhance.Color(original_image)
      vibrant_image = enhancer_color.enhance(color_boost)

      enhancer_contrast = ImageEnhance.Contrast(vibrant_image)
      detailed_image = enhancer_contrast.enhance(contrast_boost)

      small_image = detailed_image.resize(
          (grid_width, grid_height), Image.Resampling.LANCZOS
      )
      quantized_image = small_image.quantize(
          colors=num_colors, method=Image.MEDIANCUT
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
    st.success("High-detail canvas generated successfully!")
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
        label="Download High-Detail Pattern Canvas (.png)",
        data=byte_im,
        file_name="high_detail_needlepoint_canvas.png",
        mime="image/png",
    )
