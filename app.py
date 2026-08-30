from PIL import Image

def adjust_mesh_density(image_path, mesh_count, physical_width_inches):
    """
    Adjusts an image's pixel grid to match a specific needlepoint mesh density.
    
    Parameters:
    - image_path (str): Path to the input design image.
    - mesh_count (int): Holes per inch corresponding to mesh type.
      * 10 or 12: Large holes for rugs/beginners
      * 13 or 14: Medium versatility for pillows
      * 18: Fine gauge for detailed portraits
      * 24: Congress cloth for miniature work
    - physical_width_inches (float): Desired physical width of the stitched piece.
    """
    img = Image.open(image_path)
    
    # Calculate grid dimensions based on mesh count and physical size
    target_width = int(mesh_count * physical_width_inches)
    aspect_ratio = img.height / img.width
    target_height = int(target_width * aspect_ratio)
    
    # Resize using NEAREST neighbor to maintain distinct grid blocks for stitching
    mesh_grid = img.resize((target_width, target_height), Image.Resampling.NEAREST)
    return mesh_grid

# Example usage for an 8-inch wide detailed portrait using 18 Mesh
# charted_image = adjust_mesh_density("design.jpg", mesh_count=18, physical_width_inches=8.0)
# charted_image.save("needlepoint_chart.png")
