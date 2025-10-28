# Template Layout Engine - Demo Guide

## 🎯 Quick Start

Welcome to the Template Layout Engine! This guide will help you get started in under 5 minutes.

### Access the Demo
**URL:** https://demo.nbne.uk/demo

---

## 📋 What You'll Need

1. **Sample CSV File** - `sample_memorial_orders.csv` (included)
2. **Web Browser** - Chrome, Firefox, Safari, or Edge
3. **5 Minutes** - That's all it takes!

---

## 🚀 Step-by-Step Tutorial

### Step 1: Open the Demo
Navigate to https://demo.nbne.uk/demo in your browser.

### Step 2: Choose Product Type
- Click the **Product Type** dropdown
- Select **"Text Products (Memorial, Business Cards, Labels)"**

### Step 3: Select a Template (Optional)
- Click one of the quick template buttons:
  - **Memorial Plaques** (recommended for sample CSV)
  - **Business Cards**
  - **Product Labels**

### Step 4: Upload the Sample CSV
1. Scroll to the **CSV Upload** section
2. Click **"Choose File"** and select `sample_memorial_orders.csv`
3. The system will automatically detect columns and map them:
   - **Name** → nameLine
   - **Date** → messageBlock
   - **Message** → additionalText
4. Review the mapping (adjust if needed)
5. Click **"📤 Upload & Generate"**

### Step 5: View Results
- The preview will show a 3x3 grid of memorial plaques
- **24 items** generated in under 1 second!
- Each plaque contains personalized data from your CSV

### Step 6: Download
- Click **"💾 Download SVG"** for editable vector file
- Click **"📄 Download PDF"** for print-ready output

---

## 🎨 Advanced Features

### Multiple Beds (Tabs)
Work on multiple products simultaneously:
1. Click the **"+"** button next to tabs
2. Name your new bed (e.g., "Business Cards")
3. Configure different dimensions
4. Switch between tabs - each saves its configuration

### Menu Bar Features

**📁 File Menu:**
- New Bed - Create additional workspace
- Open Template - Load saved configurations
- Save Template - Save current setup as JSON
- Export SVG/PDF - Download outputs

**✏️ Edit Menu:**
- Clear Preview - Reset preview area
- Reset to Defaults - Restore default settings
- Rename Current Bed - Change tab name

**👁️ View Menu:**
- Zoom In/Out - Adjust preview size
- Fit to Screen - Reset zoom level

**❓ Help Menu:**
- Quick Start Guide
- Keyboard Shortcuts
- About

### Custom Configurations
Adjust bed and part dimensions:
- **Bed Size:** Your print bed dimensions (mm)
- **Part Size:** Individual item dimensions (mm)
- **Tiling:** Columns, rows, and gaps

---

## 📊 Sample CSV Format

### Text Products (Memorial Plaques)
```csv
Name,Date,Message
John Smith,1950-2024,Forever in our hearts
Mary Johnson,1945-2023,Loved and remembered
```

### Photo Products
```csv
Name,Date,Photo
John Smith,1950-2024,/static/photos/john.jpg
Mary Johnson,1945-2023,/static/photos/mary.jpg
```

### Business Cards
```csv
Name,Title,Contact
John Smith,CEO,john@company.com
Jane Doe,Designer,jane@company.com
```

---

## 💡 Tips & Tricks

### Column Mapping
- The system auto-detects column names
- You can manually adjust mappings via dropdowns
- Use **"-- Skip --"** to ignore columns

### Graphics & Borders
- Upload graphics via **Graphics Library**
- Reference in CSV: `/static/graphics/border.svg`
- Leave blank for no graphic

### Keyboard Shortcuts
- **Ctrl+S** - Save Template
- **Ctrl+E** - Export SVG
- **Ctrl+P** - Export PDF
- **+/-** - Zoom In/Out

### Performance
- Processes 100+ items in seconds
- No limit on CSV size
- Real-time preview updates

---

## 🎯 Use Cases

### Memorial Products
- Memorial plaques
- Garden stakes
- Remembrance cards

### Business Products
- Business cards
- Name badges
- ID cards

### Retail Products
- Product labels
- Price tags
- Shelf labels

### Custom Applications
- Event badges
- Gift tags
- Promotional items

---

## 🔧 Technical Specifications

### Supported Formats
- **Input:** CSV, TXT (comma-separated)
- **Output:** SVG (editable), PDF (print-ready)

### Dimensions
- Units: Millimeters (mm)
- Precision: 0.1mm
- Max bed size: 1000mm x 1000mm

### Text Features
- Fonts: Times New Roman, Arial, Georgia
- Sizes: 6pt - 72pt
- Alignment: Left, Center, Right
- Multiline support

### Graphics Features
- Formats: SVG, PNG, JPG
- Clipping: Rounded corners, circles
- Positioning: Absolute, relative

---

## 📞 Support & Questions

For technical support or questions:
- **Email:** support@nbne.uk
- **Documentation:** https://demo.nbne.uk/docs
- **Video Tutorials:** https://demo.nbne.uk/tutorials

---

## 🚀 Next Steps

1. **Try the sample CSV** - See it in action
2. **Create your own CSV** - Use your data
3. **Experiment with templates** - Find what works
4. **Save your templates** - Reuse configurations
5. **Scale up** - Process bulk orders

---

## ✨ Key Benefits

- ⚡ **Fast:** Process 100s of items in seconds
- 🎨 **Flexible:** Template-driven, no coding required
- 📊 **Scalable:** Handles small batches to bulk orders
- 💾 **Production-Ready:** SVG and PDF export
- 🔄 **Reusable:** Save and share templates
- 🎯 **Accurate:** Precise mm-level positioning

---

**Ready to transform your workflow?** Start with the sample CSV and see the magic happen!

*Template Layout Engine v1.0 - Developed for NBNE Origin*
