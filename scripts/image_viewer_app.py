import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import sys
from collections import Counter
import random

# Base directories - same as in create_masked_images.py
BASE_DIR = "data"
TRUE_POSITIVE_DIR = os.path.join(BASE_DIR, "true_positive_images")
OUTPUT_DIR = os.path.join(BASE_DIR, "true_positive_masked_images")
CROP_DIR = os.path.join(BASE_DIR, "cropped_images_for_classification")
QUEUE_FILE = os.path.join(BASE_DIR, "classification_queue.json")

class FlagImageViewer(tk.Tk):
    """GUI application for viewing flag images with bounding boxes."""
    
    def __init__(self):
        super().__init__()
        
        # Configure the main window
        self.title("Flag Image Viewer")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Initialize variables
        self.current_index = 0
        self.images = []
        self.min_boxes = tk.IntVar(value=2)
        self.max_boxes = tk.IntVar(value=100)  # Set a high default that will be adjusted
        self.show_masked = tk.BooleanVar(value=True)
        self.current_image_tk = None
        self.max_boxes_in_data = 0  # Track the actual maximum in the data
        
        # New variables for classification queue browsing
        self.view_mode = tk.StringVar(value="bbox")  # "bbox" or "classification"
        self.min_confidence = tk.DoubleVar(value=0.3)
        self.max_samples = tk.IntVar(value=100)
        self.classification_queue = []
        self.filter_by_town = tk.StringVar(value="All")
        self.town_list = ["All"]
        self.distance_filter = tk.StringVar(value="All")
        self.distance_options = ["All", "Distant flags", "Normal sized", "Small detections"]
        
        # Scan data to find the maximum number of boxes
        self.scan_max_boxes()
        
        # Create the UI
        self.create_ui()
        
        # Load images on startup
        self.load_images()
    
    def scan_max_boxes(self):
        """Scan all JSON files to find the maximum number of bounding boxes in any image."""
        try:
            # Get list of towns
            towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) 
                    if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]
            
            self.town_list.extend(towns)
            
            max_boxes = 0
            
            # Process each town
            for town in towns:
                town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
                bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
                
                try:
                    with open(bbox_file, 'r') as f:
                        bbox_data = json.load(f)
                    
                    # Find the maximum number of boxes in any image
                    for image_name, detections in bbox_data.items():
                        box_count = len(detections)
                        max_boxes = max(max_boxes, box_count)
                    
                except Exception as e:
                    print(f"Error scanning {town}: {e}")
            
            self.max_boxes_in_data = max_boxes
            # Set the max_boxes variable to the found maximum
            self.max_boxes.set(max_boxes)
            
            print(f"Maximum number of bounding boxes found in data: {max_boxes}")
            
        except Exception as e:
            print(f"Error scanning for maximum boxes: {e}")
            # Set a reasonable default if scanning fails
            self.max_boxes_in_data = 20
            self.max_boxes.set(20)
    
    def create_ui(self):
        """Create the user interface."""
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel
        control_panel = ttk.Frame(main_frame)
        control_panel.pack(fill=tk.X, pady=(0, 10))
        
        # View mode selection
        mode_frame = ttk.LabelFrame(control_panel, text="View Mode")
        mode_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        bbox_radio = ttk.Radiobutton(mode_frame, text="Original Images", 
                                   variable=self.view_mode, value="bbox",
                                   command=self.switch_view_mode)
        bbox_radio.pack(side=tk.LEFT, padx=5)
        
        class_radio = ttk.Radiobutton(mode_frame, text="Classification Images", 
                                    variable=self.view_mode, value="classification",
                                    command=self.switch_view_mode)
        class_radio.pack(side=tk.LEFT, padx=5)
        
        # Filter frame - will contain different controls based on mode
        self.filter_frame = ttk.LabelFrame(control_panel, text="Filters")
        self.filter_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Create both sets of filters but only show the relevant one
        self.create_bbox_filters()
        self.create_classification_filters()
        
        # Image count label
        self.count_label = ttk.Label(control_panel, text="Images: 0")
        self.count_label.pack(side=tk.RIGHT)
        
        # Image display area
        self.image_frame = ttk.Frame(main_frame, borderwidth=2, relief="groove")
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Image canvas with scrollbars
        self.canvas_frame = ttk.Frame(self.image_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(self.image_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Image info panel
        info_frame = ttk.LabelFrame(main_frame, text="Image Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(info_frame, height=6, wrap=tk.WORD)
        self.info_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Navigation panel
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X)
        
        prev_button = ttk.Button(nav_frame, text="Previous", command=self.prev_image)
        prev_button.pack(side=tk.LEFT, padx=(0, 5))
        
        next_button = ttk.Button(nav_frame, text="Next", command=self.next_image)
        next_button.pack(side=tk.LEFT)
        
        random_button = ttk.Button(nav_frame, text="Random Image", command=self.random_image)
        random_button.pack(side=tk.LEFT, padx=5)
        
        # Keyboard bindings
        self.bind("<Left>", lambda e: self.prev_image())
        self.bind("<Right>", lambda e: self.next_image())
        self.bind("<space>", lambda e: self.toggle_masked())
        self.bind("r", lambda e: self.random_image())
        
        # Mouse wheel for zooming
        self.canvas.bind("<MouseWheel>", self.zoom)  # Windows
        self.canvas.bind("<Button-4>", self.zoom)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom)    # Linux scroll down
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set initial status
        self.status_var.set(f"Ready - Maximum boxes in data: {self.max_boxes_in_data}")
        
        # Initialize the correct filters
        self.switch_view_mode()
    
    def create_bbox_filters(self):
        """Create filters for the original bounding box mode."""
        self.bbox_filter_frame = ttk.Frame(self.filter_frame)
        
        # Min boxes filter
        ttk.Label(self.bbox_filter_frame, text="Min Boxes:").pack(side=tk.LEFT, padx=(0, 5))
        min_boxes_spinbox = ttk.Spinbox(self.bbox_filter_frame, from_=1, to=self.max_boxes_in_data, width=5, 
                                        textvariable=self.min_boxes)
        min_boxes_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Max boxes filter
        ttk.Label(self.bbox_filter_frame, text="Max Boxes:").pack(side=tk.LEFT, padx=(0, 5))
        max_boxes_spinbox = ttk.Spinbox(self.bbox_filter_frame, from_=1, to=self.max_boxes_in_data, width=5, 
                                        textvariable=self.max_boxes)
        max_boxes_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Filter button
        filter_button = ttk.Button(self.bbox_filter_frame, text="Apply Filter", command=self.load_images)
        filter_button.pack(side=tk.LEFT, padx=(0, 20))
        
        # Toggle masked/original
        masked_check = ttk.Checkbutton(self.bbox_filter_frame, text="Show Masked Images", 
                                      variable=self.show_masked, command=self.update_image)
        masked_check.pack(side=tk.LEFT, padx=(0, 20))
    
    def create_classification_filters(self):
        """Create filters for the classification queue mode."""
        self.classification_filter_frame = ttk.Frame(self.filter_frame)
        
        # Min confidence filter
        ttk.Label(self.classification_filter_frame, text="Min Confidence:").pack(side=tk.LEFT, padx=(0, 5))
        min_conf_spinbox = ttk.Spinbox(self.classification_filter_frame, from_=0.1, to=1.0, increment=0.1, width=5, 
                                      textvariable=self.min_confidence)
        min_conf_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Town filter
        ttk.Label(self.classification_filter_frame, text="Town:").pack(side=tk.LEFT, padx=(0, 5))
        town_combo = ttk.Combobox(self.classification_filter_frame, textvariable=self.filter_by_town, 
                                 values=self.town_list, width=20)
        town_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Distance hint filter
        ttk.Label(self.classification_filter_frame, text="Distance:").pack(side=tk.LEFT, padx=(0, 5))
        distance_combo = ttk.Combobox(self.classification_filter_frame, textvariable=self.distance_filter, 
                                    values=self.distance_options, width=15)
        distance_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Max samples
        ttk.Label(self.classification_filter_frame, text="Max Samples:").pack(side=tk.LEFT, padx=(0, 5))
        max_samples_spinbox = ttk.Spinbox(self.classification_filter_frame, from_=10, to=1000, increment=10, width=5, 
                                         textvariable=self.max_samples)
        max_samples_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        
        # Filter button
        filter_button = ttk.Button(self.classification_filter_frame, text="Apply Filter", 
                                 command=self.load_classification_images)
        filter_button.pack(side=tk.LEFT, padx=(0, 20))
    
    def switch_view_mode(self):
        """Switch between viewing original images and classification queue images."""
        mode = self.view_mode.get()
        
        # Clear existing children from filter frame
        for widget in self.filter_frame.winfo_children():
            widget.pack_forget()
        
        # Show the appropriate filters
        if mode == "bbox":
            self.bbox_filter_frame.pack(fill=tk.X, expand=True)
            self.load_images()
        else:  # classification mode
            self.classification_filter_frame.pack(fill=tk.X, expand=True)
            self.load_classification_images()
    
    def load_images(self):
        """Load images with bounding boxes in the specified range."""
        min_boxes = self.min_boxes.get()
        max_boxes = self.max_boxes.get()
        
        # Validate input
        if min_boxes > max_boxes:
            messagebox.showwarning("Invalid Range", "Minimum boxes cannot be greater than maximum boxes.")
            self.min_boxes.set(max_boxes)
            min_boxes = max_boxes
        
        self.status_var.set(f"Finding images with {min_boxes} to {max_boxes} bounding boxes...")
        self.update()  # Update the UI
        
        # Find images with bounding boxes in the specified range
        self.images = self.find_images_with_box_range(min_boxes, max_boxes)
        
        # Update count label
        self.count_label.config(text=f"Images: {len(self.images)}")
        
        if not self.images:
            messagebox.showinfo("No Images", f"No images found with {min_boxes} to {max_boxes} bounding boxes.")
            self.status_var.set("No images found")
            return
        
        # Reset to first image
        self.current_index = 0
        self.update_image()
        
        self.status_var.set(f"Loaded {len(self.images)} images with {min_boxes} to {max_boxes} bounding boxes")
    
    def load_classification_images(self):
        """Load images from the classification queue."""
        try:
            if not os.path.exists(QUEUE_FILE):
                messagebox.showinfo("Queue File Missing", 
                                   f"The classification queue file {QUEUE_FILE} was not found. "
                                   "Please run the prepare_images_for_classification.py script first.")
                self.status_var.set("Classification queue file not found")
                return
            
            self.status_var.set("Loading classification queue...")
            self.update()  # Update the UI
            
            # Load the queue
            with open(QUEUE_FILE, 'r') as f:
                queue_data = json.load(f)
            
            # Extract the list of images
            if isinstance(queue_data, dict) and 'images' in queue_data:
                full_queue = queue_data['images']
            else:
                full_queue = queue_data
            
            # Apply filters
            min_conf = self.min_confidence.get()
            town_filter = self.filter_by_town.get()
            distance_filter = self.distance_filter.get()
            max_samples = self.max_samples.get()
            
            filtered_queue = []
            for item in full_queue:
                # Apply confidence filter
                if item['confidence'] < min_conf:
                    continue
                
                # Apply town filter
                if town_filter != "All" and item['town'] != town_filter:
                    continue
                
                # Apply distance filter
                if distance_filter != "All":
                    hint = item.get('distance_hint', '').lower()
                    if distance_filter == "Distant flags" and "distant" not in hint:
                        continue
                    elif distance_filter == "Normal sized" and "normal" not in hint:
                        continue
                    elif distance_filter == "Small detections" and "small" not in hint:
                        continue
                
                # Check if the image file exists
                if item.get('is_cropped', False):
                    image_path = item.get('cropped_image')
                else:
                    image_path = item.get('original_image')
                
                if not os.path.exists(image_path):
                    continue
                
                filtered_queue.append(item)
            
            # Limit the number of samples
            if len(filtered_queue) > max_samples:
                filtered_queue = filtered_queue[:max_samples]
            
            self.classification_queue = filtered_queue
            self.images = self.classification_queue  # Use the same variable for consistency in update_image
            
            # Update count label
            self.count_label.config(text=f"Images: {len(self.images)}")
            
            if not self.images:
                messagebox.showinfo("No Images", "No images match the current filters.")
                self.status_var.set("No matching images found")
                return
            
            # Reset to first image
            self.current_index = 0
            self.update_image()
            
            self.status_var.set(f"Loaded {len(self.images)} images from classification queue")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading classification queue: {e}")
            self.status_var.set(f"Error: {e}")
    
    def find_images_with_box_range(self, min_boxes=2, max_boxes=None):
        """Find all images with bounding boxes in the specified range and return them as a list."""
        # If max_boxes is None, use the maximum found in the data
        if max_boxes is None:
            max_boxes = self.max_boxes_in_data
        
        # Get list of towns
        towns = [d for d in os.listdir(TRUE_POSITIVE_DIR) 
                if os.path.isdir(os.path.join(TRUE_POSITIVE_DIR, d))]
        
        filtered_images = []
        
        # Process each town
        for town in towns:
            town_dir = os.path.join(TRUE_POSITIVE_DIR, town)
            bbox_file = os.path.join(town_dir, f"true_positive_bboxes_hf_{town}.json")
            
            try:
                with open(bbox_file, 'r') as f:
                    bbox_data = json.load(f)
                
                # Find images with bounding boxes in the specified range
                for image_name, detections in bbox_data.items():
                    box_count = len(detections)
                    if min_boxes <= box_count <= max_boxes:
                        image_path = os.path.join(town_dir, image_name)
                        if os.path.exists(image_path):
                            # Calculate masked image path
                            town_output_dir = os.path.join(OUTPUT_DIR, town)
                            masked_path = os.path.join(town_output_dir, f"masked_{image_name}")
                            
                            # Check if masked image exists, create if not
                            if not os.path.exists(masked_path):
                                os.makedirs(town_output_dir, exist_ok=True)
                                self.create_masked_image(image_path, detections, masked_path)
                            
                            filtered_images.append({
                                'town': town,
                                'image_name': image_name,
                                'path': image_path,
                                'masked_path': masked_path,
                                'box_count': box_count,
                                'detections': detections
                            })
                
            except Exception as e:
                print(f"Error scanning {town}: {e}")
        
        # Sort by box count (descending)
        filtered_images.sort(key=lambda x: x['box_count'], reverse=True)
        
        return filtered_images
    
    def create_masked_image(self, image_path, detections, output_path):
        """Create a masked image with bounding boxes and confidence scores."""
        try:
            # Import the necessary function from create_masked_images.py
            from create_masked_images import create_masked_image
            create_masked_image(image_path, detections, output_path)
        except Exception as e:
            print(f"Error creating masked image: {e}")
    
    def update_image(self):
        """Update the displayed image."""
        if not self.images or self.current_index >= len(self.images):
            return
        
        # Get current image info
        image_info = self.images[self.current_index]
        
        # Determine which image to show based on mode
        if self.view_mode.get() == "bbox":
            # Original/masked image mode
            if self.show_masked.get():
                image_path = image_info['masked_path']
            else:
                image_path = image_info['path']
        else:
            # Classification queue mode
            if image_info.get('is_cropped', False):
                image_path = image_info.get('cropped_image')
            else:
                image_path = image_info.get('original_image')
        
        try:
            # Load and display the image
            image = Image.open(image_path)
            
            # Resize image to fit canvas while maintaining aspect ratio
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:  # Ensure canvas has been drawn
                # Calculate scale factor
                img_width, img_height = image.size
                width_ratio = canvas_width / img_width
                height_ratio = canvas_height / img_height
                scale_factor = min(width_ratio, height_ratio) * 0.9  # 90% of available space
                
                # Resize image
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                # Fix for PIL.Image.LANCZOS deprecation
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image_tk = ImageTk.PhotoImage(image)
            
            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image_tk)
            
            # Configure canvas scrolling
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            
            # Update info text
            if self.view_mode.get() == "bbox":
                self.update_bbox_info_text(image_info)
            else:
                self.update_classification_info_text(image_info)
            
            # Update status
            self.status_var.set(f"Image {self.current_index + 1} of {len(self.images)}")
            
        except Exception as e:
            self.status_var.set(f"Error loading image: {e}")
            print(f"Error loading image: {e}")
    
    def update_bbox_info_text(self, image_info):
        """Update the information text panel for bbox mode."""
        self.info_text.delete(1.0, tk.END)
        
        # Basic info
        info = f"Town: {image_info['town']}\n"
        info += f"Image: {image_info['image_name']}\n"
        info += f"Bounding Boxes: {image_info['box_count']}\n\n"
        
        # Detailed detection info
        info += "Detections:\n"
        for i, detection in enumerate(image_info['detections']):
            box = detection['box']
            confidence = detection['confidence']
            info += f"  Box {i+1}: Confidence: {confidence:.2f}, Coords: {box}\n"
        
        self.info_text.insert(tk.END, info)
    
    def update_classification_info_text(self, image_info):
        """Update the information text panel for classification mode."""
        self.info_text.delete(1.0, tk.END)
        
        # Basic info
        info = f"Town: {image_info['town']}\n"
        
        # Check if it's a cropped image
        if image_info.get('is_cropped', False):
            original_filename = os.path.basename(image_info.get('original_image', ''))
            info += f"Original Image: {original_filename}\n"
            info += f"Cropped Image: {image_info.get('filename', '')}\n"
        else:
            info += f"Image: {image_info.get('filename', '')}\n"
            info += f"Mode: Single box image (uncropped)\n"
        
        # Box info
        info += f"Box Index: {image_info.get('box_index', 0)}\n"
        info += f"Confidence: {image_info.get('confidence', 0):.2f}\n"
        
        # Distance hint and size info
        if 'distance_hint' in image_info:
            info += f"Distance Hint: {image_info['distance_hint']}\n"
        
        if 'relative_size' in image_info:
            info += f"Relative Size: {image_info['relative_size']*100:.2f}% of image area\n"
        
        if 'position_factor' in image_info:
            info += f"Position Factor: {image_info['position_factor']:.2f} (higher = more towards top)\n"
        
        # Box coordinates
        if 'box' in image_info:
            box = image_info['box']
            info += f"Box Coordinates: {box}\n"
        
        self.info_text.insert(tk.END, info)
    
    def next_image(self):
        """Show the next image."""
        if not self.images:
            return
        
        self.current_index = (self.current_index + 1) % len(self.images)
        self.update_image()
    
    def prev_image(self):
        """Show the previous image."""
        if not self.images:
            return
        
        self.current_index = (self.current_index - 1) % len(self.images)
        self.update_image()
    
    def random_image(self):
        """Show a random image from the current set."""
        if not self.images:
            return
        
        self.current_index = random.randint(0, len(self.images) - 1)
        self.update_image()
    
    def toggle_masked(self):
        """Toggle between masked and original images."""
        if self.view_mode.get() == "bbox":
            self.show_masked.set(not self.show_masked.get())
            self.update_image()
    
    def zoom(self, event):
        """Handle zoom with mouse wheel."""
        if not self.current_image_tk:
            return
        
        # Determine zoom direction
        if event.num == 4 or event.delta > 0:  # Zoom in
            factor = 1.1
        else:  # Zoom out
            factor = 0.9
        
        # Apply zoom
        self.canvas.scale("all", event.x, event.y, factor, factor)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

if __name__ == "__main__":
    app = FlagImageViewer()
    app.mainloop() 