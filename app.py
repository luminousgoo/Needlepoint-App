import io
from PIL import Image, ImageDraw, ImageOps
import streamlit as st

st.set_page_config(
    page_title="DIY Needlepoint Pattern Generator", layout="centered"
)

st.title("🪡 DIY Needlepoint Ornament Generator")
st.write(
    "Upload any photo to automatically calculate the optimal canvas size and"
    " color count, or customize them below!"
)

uploaded_file = st.file_uploader(
    "Choose an image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
  original_image = Image.open(uploaded_file).convert("RGB")
  orig_w, orig_h = original_image.size
  aspect_ratio = orig_h / orig_w

  # Automated recommendation logic for an ornament (target ~60 stitches wide for high detail balance)
  rec_width = 60
  rec_height = int(rec_width * aspect_ratio)
  rec_colors = 14  # Ideal sweet spot for photographic detail vs stitchability

  col1, col2 = st.columns(2)
  with col1:
    st.subheader("Original Image")
    st.image(original_image, use_container_width=True)

  with col2:
    st.subheader("✨ Recommended Settings")
    st.write(
        f"Based on your image's aspect ratio, we recommend a canvas width of"
        f" **{rec_width} stitches** (height: **{rec_height} stitches**) using"
        f" **{rec_colors} colors** to best capture the details."
    )

  st.markdown("---")
  st.subheader("Adjust Pattern Prompts")

  # Interactive prompt inputs for user preferences
  grid_width = st.slider(
      "Target Canvas Width (Stitches)",
      min_value=30,
      max_value=120,
      value=rec_width,
      step=5,
  )
  num_colors = st.slider(
      "Number of Thread Colors",
      min_value=4,
      max_value=24,
      value=rec_colors,
      step=1,
  )
  cell_size = st.slider(
      "Grid Zoom / Cell Pixel Size", min_value=10, max_value=30, value=20, step=2
  )

  grid_height = int(grid_width * aspect_ratio)

  st.info(
      f"Current Selection: **{grid_width} x {grid_height} grid** ("
      f"{grid_width * grid_height:,} total stitches) with **{num_colors}**"
      " colors."
  )

  if st.button("Generate Final Pattern Canvas", type="primary"):
    with st.spinner("Processing image and generating canvas..."):
      small_image = original_image.resize(
          (grid_width, grid_height), Image.Resampling.NEAREST
      )
      quantized_image = small_image.quantize(
          colors=num_colors, method=Image.Quantize.MEDIANCUT
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

    st.success("Canvas generated successfully!")
    st.subheader("Printable Pattern Canvas")
    st.image(preview_image, use_container_width=True)

    st.subheader("Color Palette & Legend")
    for i, color in enumerate(unique_colors):
      swatch = Image.new("RGB", (30, 30), color)
      col_a, col_b = st.columns([1, 5])
      with col_a:
        st.image(swatch, width=30)
      with col_b:
        st.write(
            f"**Color #{i+1}** — RGB: `{color}` (Hex:"
            f" `#{color[0]:02x}{color[1]:02x}{color[2]:02x}`)"
        )

    buf = io.BytesIO()
    preview_image.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="Download Pattern Canvas (.png)",
        data=byte_im,
        file_name="needlepoint_canvas.png",
        mime="image/png",
    )
