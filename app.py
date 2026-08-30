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

  rec_width = 120
  rec_height = int(rec_width * aspect_ratio)
  rec_colors = 36

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
  st.subheader("Select Ornament Shape & Mesh Density")

  ornament_shape = st.selectbox("Ornament Shape", ["Circle", "Square", "Arch"])
  mesh_count = st.selectbox(
      "Canvas Mesh Count (Holes Per Inch)", [10, 12, 13, 14, 18, 24], index=3
  )

  st.markdown("---")
  st.subheader("Fine-Tune Pattern Prompts")

  grid_width = st.slider(
      "Target Canvas Width (Stitches)",
      min_value=40,
      max_value=300,
      value=rec_width,
      step=5,
  )
  num_colors = st.slider(
      "Number of Thread Colors",
      min_value=16,
      max_value=64,
      value=rec_colors,
      step=2,
  )
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

  working_image = original_image
  if ornament_shape in ["Circle", "Square"]:
    min_dim = min(orig_w, orig_h)
    left = (orig_w - min_dim) // 2
    top = (orig_h - min_dim) // 2
    working_image = working_image.crop((left, top, left + min_dim, top + min_dim))
    crop_w, crop_h = min_dim, min_dim
  elif ornament_shape == "Arch":
    crop_w = min(orig_w, int(orig_h / 1.2))
    crop_h = int(crop_w * 1.2)
    left = (orig_w - crop_w) // 2
    top = (orig_h - crop_h) // 2
    working_image = working_image.crop((left, top, left + crop_w, top + crop_h))

  shape_aspect = crop_h / crop_w
  grid_height = int(grid_width * shape_aspect)

  width_inches = grid_width / mesh_count
  height_inches = grid_height / mesh_count

  st.info(
      f"Current Selection ({ornament_shape}, {mesh_count} Mesh):"
      f" **{grid_width} x {grid_height} grid** ({grid_width * grid_height:,}"
      f" total stitches) | Approx. Size: **{width_inches:.1f}\" x"
      f" {height_inches:.1f}\"** with **{num_colors}** colors."
  )

  if st.button("Generate Ornament Pattern Canvas", type="primary"):
    with st.spinner("Processing image and mapping colors..."):
      enhancer = ImageEnhance.Color(working_image)
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

      max_px_w = grid_width * cell_size
      max_px_h = grid_height * cell_size

      # Thicker outline width set to 6 for high visibility
      if ornament_shape == "Circle":
        center_x = max_px_w // 2
        center_y = max_px_h // 2
        radius = min(max_px_w, max_px_h) // 2
        draw.ellipse(
            [
                (center_x - radius, center_y - radius),
                (center_x + radius, center_y + radius),
            ],
            outline="black",
            width=6,
        )
      elif ornament_shape == "Square":
        draw.rectangle(
            [(0, 0), (max_px_w - 1, max_px_h - 1)], outline="black", width=6
        )
      elif ornament_shape == "Arch":
        radius = max_px_w // 2
        draw.arc(
            [(0, 0), (max_px_w, radius * 2)],
            start=180,
            end=360,
            fill="black",
            width=6,
        )
        draw.line([(0, radius), (0, max_px_h)], fill="black", width=6)
        draw.line([(max_px_w, radius), (max_px_w, max_px_h)], fill="black", width=6)
        draw.line(
            [(0, max_px_h - 1), (max_px_w, max_px_h - 1)], fill="black", width=6
        )

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
