import os
import svgwrite
import base64
try:
    from memorial_base import MemorialBase
except ImportError:
    MemorialBase = object
try:
    import pandas as pd
except ImportError:
    pd = None

class PhotoStakesProcessor(MemorialBase):
    # Add class-level defaults for any missing attributes
    px_per_mm = 3.78  # Fallback px/mm
    pt_to_mm = 0.3528 # Fallback pt to mm
    memorial_width_px = 480 * px_per_mm
    memorial_height_px = 75 * px_per_mm
    x_offset_px = 0
    y_offset_px = 0
    page_width_mm = 480
    page_height_mm = 290
    page_width_px = int(page_width_mm * px_per_mm)
    page_height_px = int(page_height_mm * px_per_mm)
    OUTPUT_DIR = 'SVG_OUTPUT'
    CATEGORY = 'PHOTO'
    date_str = 'YYYYMMDD'

    def __init__(self, graphics_path=None, output_dir=None):
        print('PhotoStakesProcessor.__init__ called')
        try:
            super().__init__(graphics_path, output_dir)
        except Exception as e:
            print(f"Warning: super().__init__ failed: {e}")
        self.CATEGORY = 'PHOTO'
        self.photo_width_mm = 50.5
        self.photo_height_mm = 68.8
        self.photo_clip_width_mm = 50.378
        self.photo_clip_height_mm = 68.901
        self.photo_border_stroke_mm = 3.65
        self.photo_outline_stroke_mm = 0.1
        self.photo_corner_radius_mm = 6
        self.photo_left_margin_mm = 7.7
        self.text_right_shift_mm = 30
        # Convert to pixels
        self.photo_width_px = int(self.photo_width_mm * self.px_per_mm)
        self.photo_height_px = int(self.photo_height_mm * self.px_per_mm)
        self.photo_clip_width_px = int(self.photo_clip_width_mm * self.px_per_mm)
        self.photo_clip_height_px = int(self.photo_clip_height_mm * self.px_per_mm)
        self.photo_border_stroke_px = int(self.photo_border_stroke_mm * self.px_per_mm)
        self.photo_outline_stroke_px = int(self.photo_outline_stroke_mm * self.px_per_mm)
        self.photo_corner_radius_px = int(self.photo_corner_radius_mm * self.px_per_mm)
        self.photo_left_margin_px = int(self.photo_left_margin_mm * self.px_per_mm)
        self.text_right_shift_px = int(self.text_right_shift_mm * self.px_per_mm)

    def wrap_text(self, text, width=30):
        # Simple word wrap
        if not text:
            return []
        words = text.split()
        lines = []
        current = ''
        for word in words:
            if len(current + ' ' + word) > width:
                lines.append(current)
                current = word
            else:
                current = (current + ' ' + word).strip()
        if current:
            lines.append(current)
        return lines

    def embed_image(self, path):
        try:
            with open(path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('ascii')
                return f'data:image/jpeg;base64,{encoded}'
        except Exception as e:
            print(f"embed_image failed: {e}")
            return None

    def add_photo_memorial(self, dwg, x, y, order):
        try:
            clip_x = x + self.photo_left_margin_px
            # Vertically center the image and borders in the red rounded rectangle
            clip_y = y + (self.memorial_height_px - self.photo_clip_height_px) / 2
            frame_x = x + self.photo_left_margin_px
            frame_y = y + (self.memorial_height_px - self.photo_height_px) / 2
            text_x = frame_x + self.photo_width_px + self.text_right_shift_px
            text_area_width = self.memorial_width_px - (text_x - x) - self.text_right_shift_px
            text_center_x = text_x + text_area_width / 2 - (self.photo_clip_width_px / 2)
            text_center_y = y + (28 * self.px_per_mm)
            dwg.add(dwg.rect(
                insert=(clip_x, clip_y),
                size=(self.photo_clip_width_px, self.photo_clip_height_px),
                rx=self.photo_corner_radius_px,
                ry=self.photo_corner_radius_px,
                fill='black'
            ))
            clip_rect = dwg.rect(
                insert=(clip_x, clip_y),
                size=(self.photo_clip_width_px, self.photo_clip_height_px),
                rx=self.photo_corner_radius_px,
                ry=self.photo_corner_radius_px,
                fill='none',
                stroke='none'
            )
            clip_path = dwg.defs.add(dwg.clipPath(id=f'clip_{x}_{y}'))
            clip_path.add(clip_rect)
            dwg.add(dwg.rect(
                insert=(text_center_x, text_center_y),
                size=(self.photo_clip_width_px, self.photo_clip_height_px),
                rx=self.photo_corner_radius_px,
                ry=self.photo_corner_radius_px,
                fill='none',
                stroke='blue',
                stroke_width=self.photo_outline_stroke_px
            ))
            dwg.add(dwg.rect(
                insert=(frame_x, frame_y),
                size=(self.photo_width_px, self.photo_height_px),
                rx=self.photo_corner_radius_px,
                ry=self.photo_corner_radius_px,
                fill='none',
                stroke='black',
                stroke_width=self.photo_border_stroke_px
            ))
            # Robustly get image_path for both dict and Series
            photo_path = order['image_path'] if isinstance(order, dict) else order.get('image_path', None)
            print(f"[add_photo_memorial] Extracted photo_path: {photo_path}")
            assert photo_path is not None, '[add_photo_memorial] ERROR: image_path is None!'
            if photo_path and isinstance(photo_path, str) and photo_path.strip():
                norm_path = os.path.normpath(photo_path.strip())
                print(f"[add_photo_memorial] Normalized: {norm_path}")
                print(f"[add_photo_memorial] Exists: {os.path.exists(norm_path)}")
                if os.path.exists(norm_path):
                    print(f"Found photo: {norm_path}")
                    photo_data = self.embed_image(norm_path)
                    if photo_data:
                        print(f"Successfully embedded photo")
                        photo = dwg.image(
                            href=photo_data,
                            insert=(frame_x, frame_y),
                            size=(self.photo_width_px, self.photo_height_px),
                            clip_path=f'url(#clip_{x}_{y})'
                        )
                        photo['xlink:href'] = photo_data
                        dwg.add(photo)
                        print(f"[add_photo_memorial] photo element added to SVG")
                    else:
                        print(f"Failed to embed photo")
                else:
                    print(f"Warning: Photo not found at {norm_path}")
            # Text area
            text_x = frame_x + self.photo_width_px + self.text_right_shift_px
            text_area_width = self.memorial_width_px - (text_x - x) - self.text_right_shift_px
            text_center_x = text_x + text_area_width / 2
            # Add text elements
            # Robustly get line_1 for both dict and Series
            line_1 = order['line_1'] if isinstance(order, dict) else order.get('line_1', None)
            print(f"[add_photo_memorial] line_1: {line_1}")
            assert line_1 is not None, '[add_photo_memorial] ERROR: line_1 is None!'
            if line_1 and isinstance(line_1, str) and line_1.strip():
                line1_y = y + (28 * self.px_per_mm)
                dwg.add(dwg.text(
                    str(line_1),
                    insert=(text_center_x, line1_y),
                    font_size=f"{17 * self.pt_to_mm}mm",
                    font_family="Georgia",
                    text_anchor="middle",
                    fill="black"
                ))
            line_2 = order['line_2'] if isinstance(order, dict) else order.get('line_2', None)
            print(f"[add_photo_memorial] line_2: {line_2}")
            assert line_2 is not None, '[add_photo_memorial] ERROR: line_2 is None!'
            if line_2 and isinstance(line_2, str) and line_2.strip():
                line2_y = y + (45 * self.px_per_mm)
                dwg.add(dwg.text(
                    str(line_2),
                    insert=(text_center_x, line2_y),
                    font_size=f"{25 * self.pt_to_mm}mm",
                    font_family="Georgia",
                    text_anchor="middle",
                    fill="black"
                ))
            line_3 = order['line_3'] if isinstance(order, dict) else order.get('line_3', None)
            print(f"[add_photo_memorial] line_3: {line_3}")
            assert line_3 is not None, '[add_photo_memorial] ERROR: line_3 is None!'
            if line_3 and isinstance(line_3, str) and line_3.strip():
                line3_y = y + (62 * self.px_per_mm)
                dwg.add(dwg.text(
                    str(line_3),
                    insert=(text_center_x, line3_y),
                    font_size=f"{13 * self.pt_to_mm}mm",
                    font_family="Georgia",
                    text_anchor="middle",
                    fill="black"
                ))
        except Exception as e:
            print(f"add_photo_memorial encountered an error: {e}")

    def create_memorial_svg(self, orders, batch_num):
        try:
            if isinstance(orders, pd.DataFrame):
                if not orders.empty:
                    first = orders.iloc[0]
                    print(f"Batch {batch_num} first order text fields: line_1={first.get('line_1', '')}, line_2={first.get('line_2', '')}, line_3={first.get('line_3', '')}")
            elif orders:
                first = orders[0]
                print(f"Batch {batch_num} first order text fields: line_1={first.get('line_1', '')}, line_2={first.get('line_2', '')}, line_3={first.get('line_3', '')}")
            filename = f"{self.CATEGORY}_{self.date_str}_{batch_num:03d}.svg"
            output_path = os.path.join(self.OUTPUT_DIR, filename)
            dwg = svgwrite.Drawing(
                filename=output_path,
                size=(f"{self.page_width_mm}mm", f"{self.page_height_mm}mm"),
                viewBox=f"0 0 {self.page_width_px} {self.page_height_px}"
            )
            for idx, order in enumerate(orders.itertuples(index=False)):
                order_dict = order._asdict()
                print(f"[create_memorial_svg] Processing order idx={idx}, type={type(order_dict)}")
                print(f"[create_memorial_svg] order contents: {order_dict}")
                if idx >= 3:
                    break
                row = 0
                col = idx
                x = self.x_offset_px + (col * self.memorial_width_px)
                y = self.y_offset_px + (row * self.memorial_height_px)
                dwg.add(dwg.rect(
                    insert=(x, y),
                    size=(self.memorial_width_px, self.memorial_height_px),
                    rx=6*self.px_per_mm,
                    ry=6*self.px_per_mm,
                    fill='none',
                    stroke='red',
                    stroke_width=0.1*self.px_per_mm
                ))
                self.add_photo_memorial(dwg, x, y, order_dict)
            ref_size_px = 0.1 * self.px_per_mm
            x_pos = self.page_width_px - ref_size_px
            y_pos = (289.8 - 0.011) * self.px_per_mm - ref_size_px
            dwg.add(dwg.rect(
                insert=(x_pos, y_pos),
                size=(ref_size_px, ref_size_px),
                fill='blue'
            ))
            dwg.save()
            return dwg
        except Exception as e:
            print(f"create_memorial_svg encountered an error: {e}")
            return None

    def process_orders(self, orders):
        print('[WINDSURF PATCH] PhotoStakesProcessor.process_orders called')
        try:
            if pd is None:
                print("pandas not available")
                return
            # --- WINDSURF PATCH: Robust normalization and filtering, rollback: remove this block ---
            if isinstance(orders, list):
                df = pd.DataFrame(orders)
            else:
                df = orders.copy()
            df.columns = [col.lower().strip() for col in df.columns]
            for col in ['type', 'colour', 'decorationtype', 'graphic', 'number-of-items', 'image_path']:
                if col not in df.columns:
                    df[col] = ''
            df['type'] = df['type'].astype(str).str.strip().str.lower()
            df['colour'] = df['colour'].astype(str).str.strip().str.lower()
            df['decorationtype'] = df['decorationtype'].astype(str).str.strip().str.lower()
            df['graphic'] = df['graphic'].astype(str).str.strip()
            df['image_path'] = df['image_path'].astype(str).str.strip()
            print(f"[DEBUG] Columns after normalization: {list(df.columns)}")
            print(df.head())
            allowed_colours = ['copper', 'gold', 'silver', 'stone', 'marble', 'gold']
            # Only include rows where 'graphic' is 'Photo' (set by pipeline), and all other criteria
            # Debug: print image_path values for all candidate rows
            print('[DEBUG] image_path values for all rows:')
            print(df[['order-id', 'image_path']])
            eligible = df[
                (df['type'] == 'regular stake') &
                (df['colour'].isin(allowed_colours)) &
                (
                    (df['graphic'].str.lower() == 'photo') |
                    (df['decorationtype'].str.lower() == 'photo')
                ) &
                (df['image_path'].notna()) & (df['image_path'].astype(str).str.strip() != '')
            ].copy()
            print(f"[DEBUG] Rows after filtering for Regular Stake, allowed colours, and graphic == 'Photo': {len(eligible)}")
            if not eligible.empty:
                print(eligible[['order-id', 'sku', 'colour', 'decorationtype', 'graphic']].head())
            else:
                print(eligible.head())
            if eligible.empty:
                print("No eligible photo stakes found for photo_stakes.py processor.")
                return
            # Expand rows by number-of-items
            expanded_rows = []
            for _, row in eligible.iterrows():
                try:
                    qty = int(row.get('number-of-items', 1))
                    qty = max(qty, 1)
                except Exception:
                    qty = 1
                for _ in range(qty):
                    expanded_rows.append(row.copy())
            df_expanded = pd.DataFrame(expanded_rows)
            batch_num = 1
            for start_idx in range(0, len(df_expanded), 3):
                batch_orders = df_expanded.iloc[start_idx:start_idx + 3]
                if not batch_orders.empty:
                    print(f"\n[DEBUG] Processing Photo batch {batch_num}...")
                    self.create_memorial_svg(batch_orders, batch_num)
                    batch_num += 1
            # --- END WINDSURF PATCH ---
        except Exception as e:
            print(f"process_orders encountered an error: {e}")