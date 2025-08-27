# KDPII NER Labeler

🏷️ **Advanced Named Entity Recognition Annotation Tool** for KDPII Data Processing

A sophisticated NER annotation interface with advanced features including overlapping annotations, entity relationship linking, JSON editing, and identifier type classification for data privacy compliance.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements_ner.txt

# 2. Start web interface
python3 ner_web_interface.py

# 3. Open browser
# Visit: http://localhost:8080
```

## ✨ Features

### Core NER Functionality
- ✅ **Interactive Text Annotation** - Click and drag to select text spans
- ✅ **Multiple Entity Types** - Person, Organization, Location, Miscellaneous
- ✅ **True Overlapping Annotations** - Advanced nested and overlapping entity support
- ✅ **Dynamic Label Management** - Add, edit, delete labels with custom hotkeys
- ✅ **Real-time Statistics** - Live label distribution and completion tracking

### KDPII Compliance Features
- ✅ **Identifier Type Classification** - Direct/Quasi/Default identifier categorization
- ✅ **Entity Relationship Linking** - Ctrl+click to link related entities
- ✅ **JSON Annotation Editing** - Direct JSON manipulation with validation
- ✅ **User Authentication System** - Multi-user annotation workflow
- ✅ **Completion Progress Tracking** - Annotation completeness monitoring

### Advanced UI Features
- ✅ **Editable JSON Details Panel** - Real-time JSON editing with validation feedback
- ✅ **Visual Entity Linking** - Ctrl+click interface for entity relationships  
- ✅ **Filter System** - Hide/show annotations by label type
- ✅ **Annotation Context Menu** - Right-click deletion with overlap handling
- ✅ **Label Distribution Chart** - Real-time statistics visualization

### Export & Integration
- ✅ **Label Studio Compatible** - Full import/export compatibility
- ✅ **CoNLL Format** - Industry standard NER format
- ✅ **JSON Export** - Structured annotation data with relationships
- ✅ **Python API** - Programmatic access to all functions

## 📁 Project Structure

```
kdpii_labler/
├── README.md                    # This file
├── ner_extractor.py            # Core NER extraction engine
├── ner_web_interface.py        # Flask web application
├── requirements_ner.txt        # Python dependencies
├── templates/
│   └── ner_interface.html      # Web interface template
├── docs/                       # Documentation
│   ├── NER_README.md          # Detailed documentation
│   └── NER_EXTRACTION_SUMMARY.md  # Korean summary
├── examples/                   # Example scripts
│   └── ner_demo.py            # Usage demonstration
├── tests/                      # Test files
│   └── test_overlapping_annotations.py  # Overlap testing
└── static/                     # Static web assets (auto-created)
```

## 🎯 Use Cases

### 1. KDPII Data Privacy Annotation
```python
from ner_extractor import NERExtractor

# Annotate sensitive data with identifier types
extractor = NERExtractor()
task_id = extractor.create_task("홍길동의 주민번호는 123456-1234567입니다.")

# Add annotation with privacy classification
extractor.add_annotation(task_id, 0, 3, ["PER"], 
                        identifier_type="direct")  # Direct identifier
```

### 2. Entity Relationship Mapping
```python
# Link related entities using entity_id
annotation1 = extractor.add_annotation(task_id, 0, 10, ["PER"])  # "John Smith"
annotation2 = extractor.add_annotation(task_id, 25, 27, ["PER"]) # "He"

# Link them as the same entity
extractor.link_entities(task_id, annotation1['span_id'], annotation2['span_id'])
```

### 3. Advanced JSON Annotation Editing
```javascript
// Direct JSON editing with validation
{
  "text": "홍길동",
  "labels": ["PER"],
  "start": 0,
  "end": 3,
  "identifier_type": "direct",
  "entity_id": "person_001",
  "relationships": [{"entity_id": "person_001", "type": "same_entity"}]
}
```

## 🔧 API Reference

### Core Classes
- **`NERExtractor`** - Main annotation engine
- **`NERLabel`** - Entity label definition  
- **`NERAnnotation`** - Individual text annotation
- **`NERTask`** - Complete annotation task

### Key Methods
- **`create_task(text)`** - Create new annotation task
- **`add_annotation(task_id, start, end, labels)`** - Add entity annotation
- **`export_task(task_id)`** - Export in Label Studio format
- **`export_conll_format(task_id)`** - Export in CoNLL format

## 📊 Advanced Features Comparison

| Feature | Basic NER Tools | KDPII NER Labeler | Status |
|---------|-----------------|-------------------|--------|
| Basic NER Annotation | ✅ | ✅ | **Enhanced** |
| Overlapping Annotations | ❌ | ✅ | **Advanced** |
| Entity Relationship Linking | ❌ | ✅ | **Unique** |
| JSON Direct Editing | ❌ | ✅ | **Innovative** |
| Identifier Type Classification | ❌ | ✅ | **KDPII Specific** |
| Real-time Validation | ❌ | ✅ | **Professional** |
| Dynamic Label Management | ❌ | ✅ | **Flexible** |
| Multi-user Support | ❌ | ✅ | **Enterprise** |

## 🧪 Testing

```bash
# Run functionality tests
python3 tests/test_overlapping_annotations.py

# Run demo examples  
python3 examples/ner_demo.py
```

## 📋 Requirements

- Python 3.7+
- Flask 2.3+
- Modern web browser

## 🔧 Key Technical Features

### JSON Editing System
- **Real-time Validation** - Live JSON syntax checking with visual feedback
- **Bi-directional Sync** - JSON ↔ UI synchronization with debouncing
- **Error Handling** - Comprehensive error messages and recovery

### Entity Relationship System  
- **Ctrl+Click Linking** - Intuitive entity connection interface
- **Visual Feedback** - Real-time highlighting and connection status
- **Entity ID Management** - Automatic entity grouping and ID assignment

### Overlapping Annotation Engine
- **True Nesting** - Support for complex overlapping entity structures
- **Render Optimization** - Efficient DOM rendering for nested annotations
- **Conflict Resolution** - Intelligent handling of annotation boundaries

## 🤝 Contributing

1. Specialized for KDPII data privacy annotation workflows
2. Report issues or suggest improvements via GitHub issues
3. Contributions welcome for enhanced privacy compliance features

## 📄 License

Open source project for KDPII data processing and privacy compliance.

---

**Made with ❤️ for KDPII Data Privacy**

*Advanced NER annotation for sensitive data processing and privacy compliance*