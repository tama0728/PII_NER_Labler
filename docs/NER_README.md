# Label Studio NER Extractor

A standalone Named Entity Recognition (NER) annotation interface extracted from Label Studio, providing all the essential functionality for NER tasks without the full Label Studio installation.

## Features

### Core NER Functionality
- **Text Annotation**: Interactive text selection and entity labeling
- **Multiple Entity Types**: Support for Person (PER), Organization (ORG), Location (LOC), and Miscellaneous (MISC)
- **Visual Interface**: Color-coded labels with Label Studio-inspired design
- **Keyboard Shortcuts**: Quick label selection with hotkeys (1, 2, 3, 4)

### Export Formats
- **Label Studio Format**: Compatible with Label Studio import/export
- **CoNLL Format**: Industry-standard token-level NER format
- **JSON Format**: Structured annotation data with timestamps

### Advanced Features
- **Word-level Granularity**: Ensures annotations align with word boundaries
- **Overlapping Spans**: Support for nested or overlapping entity annotations
- **Confidence Ratings**: Per-region confidence assessment (High/Medium/Low)
- **Label Filtering**: Search and filter labels for large label sets
- **Statistics Dashboard**: Real-time annotation statistics and label distribution

## Installation

```bash
# Install dependencies
pip install -r requirements_ner.txt

# Run the web interface
python ner_web_interface.py
```

Visit `http://localhost:5000` to access the annotation interface.

## Usage

### Basic Usage

```python
from ner_extractor import NERExtractor

# Initialize extractor
extractor = NERExtractor()

# Create annotation task
task_id = extractor.create_task("John Smith works at Microsoft in Seattle.")

# Add annotations
extractor.add_annotation(task_id, 0, 10, ["PER"])    # John Smith
extractor.add_annotation(task_id, 20, 29, ["ORG"])   # Microsoft  
extractor.add_annotation(task_id, 33, 40, ["LOC"])   # Seattle

# Export in different formats
label_studio_format = extractor.export_task(task_id)
conll_format = extractor.export_conll_format(task_id)
```

### Web Interface Usage

1. **Load Text**: Enter or paste text in the input area and click "Load Text"
2. **Select Label**: Click on a label type (PER, ORG, LOC, MISC) to select it
3. **Annotate**: Select text spans in the content area to create annotations
4. **Export**: Click "Export" to download annotations in JSON or CoNLL format

### Custom Labels

```python
from ner_extractor import NERExtractor, NERLabel

# Define custom labels
custom_labels = [
    NERLabel("PERSON", "red", "1"),
    NERLabel("COMPANY", "blue", "2"), 
    NERLabel("PRODUCT", "green", "3"),
    NERLabel("DATE", "orange", "4")
]

extractor = NERExtractor(labels=custom_labels)
```

## XML Configuration

The extractor generates Label Studio-compatible XML configurations:

### Basic Configuration
```xml
<View>
  <Labels name="label" toName="text">
    <Label value="PER" background="red" hotkey="1"/>
    <Label value="ORG" background="darkorange" hotkey="2"/>
    <Label value="LOC" background="orange" hotkey="3"/>
    <Label value="MISC" background="green" hotkey="4"/>
  </Labels>
  <Text name="text" value="$text"/>
</View>
```

### Enhanced Configuration
```xml
<View>
  <Filter name="filter" toName="label" hotkey="shift+f" minlength="1" />
  <Labels name="label" toName="text" showInline="false">
    <Label value="PER" background="red" hotkey="1"/>
    <Label value="ORG" background="darkorange" hotkey="2"/>
    <Label value="LOC" background="orange" hotkey="3"/>
    <Label value="MISC" background="green" hotkey="4"/>
  </Labels>
  <Text name="text" value="$text" granularity="word"/>
  <Choices name="confidence" toName="text" perRegion="true">
    <Choice value="High" />
    <Choice value="Medium" />
    <Choice value="Low" />
  </Choices>
</View>
```

## API Endpoints

### Task Management
- `POST /api/tasks` - Create new annotation task
- `GET /api/tasks/<task_id>` - Get task details
- `GET /api/tasks/<task_id>/export` - Export in Label Studio format
- `GET /api/tasks/<task_id>/conll` - Export in CoNLL format

### Annotations
- `POST /api/tasks/<task_id>/annotations` - Add annotation

### Configuration & Statistics
- `GET /api/config` - Get XML configurations and label definitions
- `GET /api/statistics` - Get annotation statistics

## Output Formats

### Label Studio Format
```json
{
  "id": 123456789,
  "data": {"text": "John Smith works at Microsoft."},
  "annotations": [{
    "id": 987654321,
    "created_at": "2024-01-01T12:00:00",
    "result": [{
      "from_name": "label",
      "to_name": "text", 
      "type": "labels",
      "value": {
        "start": 0,
        "end": 10,
        "text": "John Smith",
        "labels": ["PER"]
      }
    }]
  }]
}
```

### CoNLL Format
```
John    B-PER
Smith   I-PER
works   O
at      O
Microsoft   B-ORG
.       O
```

## Architecture

### Core Components
- **NERExtractor**: Main annotation engine with task management
- **NERLabel**: Label definition with styling and hotkeys
- **NERAnnotation**: Individual text span annotation
- **NERTask**: Complete annotation task with metadata

### Web Interface
- **Flask Backend**: RESTful API for task management
- **HTML/CSS/JS Frontend**: Interactive annotation interface
- **Label Studio Styling**: Consistent visual design

## Integration

### With Label Studio
```python
# Import from Label Studio
ls_task = {...}  # Label Studio task JSON
task_id = extractor.import_label_studio_task(ls_task)

# Export to Label Studio
exported = extractor.export_task(task_id)
```

### With spaCy
```python
import spacy
from ner_extractor import NERExtractor

nlp = spacy.load("en_core_web_sm")
extractor = NERExtractor()

# Convert spaCy entities to annotations
def spacy_to_annotations(text):
    doc = nlp(text)
    task_id = extractor.create_task(text)
    
    for ent in doc.ents:
        extractor.add_annotation(task_id, ent.start_char, ent.end_char, [ent.label_])
    
    return task_id
```

## Comparison with Label Studio

### Included Features ✅
- Interactive text annotation interface
- Multiple entity type support
- Export to Label Studio and CoNLL formats
- Keyboard shortcuts and hotkeys
- Color-coded labels
- Word-level granularity
- Overlapping span support
- Statistics and analytics

### Not Included ❌
- Machine learning model integration
- Multi-user collaboration
- Project management
- Advanced data import/export
- Database integration
- User authentication
- Advanced configuration UI

## License

This extraction is based on the open-source Label Studio project. Please refer to Label Studio's license terms for usage guidelines.

## Contributing

This is a standalone extraction of Label Studio's NER functionality. For the full Label Studio experience, visit [https://labelstud.io/](https://labelstud.io/).