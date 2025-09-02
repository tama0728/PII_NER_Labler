# KDPII NER Labeler

> **🇰🇷 한국어 버전**: [README_KR.md](./README_KR.md)를 참조하세요.

## 🎉 Latest Updates (v3.3.0)

**✨ Major New Features:**
- ✅ **Complete Export System**: All tasks export to single JSONL file with original structure compatibility
- ✅ **JSONL Format Standardization**: Upload and export unified to JSONL-only for data consistency  
- ✅ **Original Structure Preservation**: Export maintains exact original file format (start_offset, end_offset)
- ✅ **Client-Side Export**: Fast, reliable export without server dependencies
- ✅ **Korean Localization**: All user messages translated to Korean for better accessibility
- ✅ **Browser UX Enhancement**: Autocomplete disabled on input fields to prevent UI interference

**✅ Previously Resolved (v3.2.0):**
- ✅ **Core Annotation Fixed**: Label click → text drag highlighting now works properly
- ✅ **ID Conflict Resolved**: span_id and entity_id collision issues fixed
- ✅ **Statistics Accuracy**: Annotation count errors (+1 over-counting) corrected
- ✅ **Dynamic Label Persistence**: Task-specific labels now persist during task switching
- ✅ **Label Deselection**: Click selected label again to deselect
- ✅ **Navigation Enhancement**: Back button added with data loss warnings
- ✅ **Collaboration UX**: Improved member selection with existing member dropdown + new member addition

**🔄 Known Issues:**
- ⚠️ **ID Management**: Entity ID reuse after deletion (tracked for v3.4.0)

> **Note**: Export functionality now production-ready with full JSONL standardization and DB-ready structure.

---

🏷️ **Advanced Named Entity Recognition Annotation Tool** for KDPII Data Processing

A sophisticated NER annotation interface with advanced features including file upload processing, task-based annotation, color-consistent labeling, metadata preservation, and team collaboration support.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start integrated application
python3 app.py

# 3. Open browser
# Visit: http://localhost:8080
# Main NER Interface: http://localhost:8080/ner
# Team Collaboration: http://localhost:8080/collaborate
```

## ✨ Features

### Core NER Functionality
- ✅ **Interactive Text Annotation** - Click and drag to select text spans
- ✅ **File Upload Processing** - JSONL format support with automatic parsing and metadata preservation
- ✅ **Task-Based Management** - Individual tasks with collapsible sidebar navigation
- ✅ **Color-Consistent Labeling** - Fixed color assignment per label during upload
- ✅ **True Overlapping Annotations** - Advanced nested and overlapping entity support
- ✅ **Dynamic Label Management** - Task-specific labels with auto-generation from files

### KDPII Compliance Features
- ✅ **Identifier Type Classification** - Direct/Quasi/Default identifier categorization
- ✅ **Entity Relationship Linking** - Ctrl+click to link related entities  
- ✅ **Metadata Preservation** - Original file metadata displayed in readonly fields
- ✅ **User Authentication System** - Multi-user annotation workflow
- ✅ **Team Collaboration** - Workspace-based collaborative annotation

### Advanced UI Features
- ✅ **Metadata Display Panel** - Read-only metadata from original files
- ✅ **Task Sidebar** - Collapsible task list with file information
- ✅ **Filter System** - Hide/show annotations by label type
- ✅ **Annotation Highlighting** - Automatic highlighting with consistent colors
- ✅ **File Upload Modal** - Drag-and-drop interface with format support

### Data Processing & Integration
- ✅ **JSONL Parser** - Standardized entity extraction with complete metadata preservation
- ✅ **Export Functionality** - Complete annotation export maintaining original file structure
- ✅ **Original Structure Compatibility** - Perfect import/export roundtrip with start_offset/end_offset
- ✅ **Database Ready Format** - Export format optimized for database insertion
- ✅ **Team Workspaces** - Collaborative annotation with member management

## 📁 Project Structure

```
kdpii_labler/
├── README.md                    # This file
├── app.py                      # Main Flask application (integrated)
├── ner_extractor.py            # Core NER extraction engine
├── ner_web_interface.py        # Original standalone NER interface
├── requirements.txt            # Python dependencies
├── frontend/
│   ├── templates/
│   │   ├── workspace_ner_interface.html  # Main NER annotation interface
│   │   ├── collaborate.html    # Team collaboration page
│   │   └── dashboard.html      # User dashboard
│   └── static/                 # CSS, JavaScript, images
├── backend/
│   ├── config.py              # Application configuration
│   ├── database.py            # Database initialization
│   ├── models/                # Data models
│   ├── services/              # Business logic
│   ├── views.py               # Main application routes
│   ├── auth.py                # Authentication system
│   ├── api.py                 # REST API endpoints
│   └── collaboration_api.py   # Team collaboration API
├── docs/                       # Documentation
└── tests/                      # Test files
```

## 🎯 Use Cases

### 1. File-Based Batch Annotation
```bash
# Upload JSONL files with pre-existing annotations
# Files automatically parsed to extract entities and metadata
# Each text becomes a separate task with preserved labels and colors
curl -X POST http://localhost:8080/collab/workspaces/workspace_id/upload \
  -F "file=@annotations.jsonl"

# Export all tasks to JSONL with original structure
# GET export will include all annotations and modifications
curl -X GET http://localhost:8080/collab/workspaces/workspace_id/export/jsonl
```

### 2. Team Collaboration Workflow
```python
# Create workspace for team annotation
workspace_id = collab_service.create_workspace("Medical NER Project")

# Team members join workspace
collab_service.add_member_to_workspace(workspace_id, "annotator_1")

# Upload tasks and collaborate
POST /collab/workspaces/{workspace_id}/tasks/{task_id}/annotate
{
  "annotations": [...],
  "member_name": "annotator_1"
}
```

### 3. KDPII Privacy Classification
```json
// Example uploaded file with metadata preservation
{
  "text": "홍길동의 주민번호는 123456-1234567입니다.",
  "entities": [
    {
      "start_offset": 0,
      "end_offset": 3,
      "span_text": "홍길동",
      "entity_type": "PER",
      "identifier_type": "direct"
    }
  ],
  "document_id": "doc_001",
  "source": "medical_records",
  "date": "2024-01-15"
}
```

## 🔧 API Reference

### Main Application Routes
- **`/ner`** - Main NER annotation interface
- **`/collaborate`** - Team collaboration workspace
- **`/collab/workspaces`** - Workspace management API
- **`/api/ner/tasks`** - Task management endpoints
- **`/api/ner/tags`** - Label management endpoints

### Core Backend Services
- **`CollaborationService`** - Team workspace and task management
- **`NERExtractor`** - Core annotation engine with file processing
- **`UserService`** - Authentication and user management

### Key API Endpoints
- **`POST /collab/workspaces/{id}/upload`** - Upload JSONL files for annotation
- **`GET /collab/workspaces/{id}/export/jsonl`** - Export all tasks as JSONL with original structure
- **`GET/POST /api/ner/tasks`** - Task creation and retrieval
- **`POST /api/ner/tasks/{id}/annotations`** - Add annotations
- **`GET/POST/PUT/DELETE /api/ner/tags`** - Label CRUD operations

## 📊 Advanced Features Comparison

| Feature | Basic NER Tools | KDPII NER Labeler v3.3.0 | Status |
|---------|-----------------|---------------------------|--------|
| Basic NER Annotation | ✅ | ✅ | **Enhanced** |
| File Upload Processing | ❌ | ✅ | **JSONL Standardized** |
| Complete Export System | ❌ | ✅ | **Production Ready** |
| Original Structure Preservation | ❌ | ✅ | **Database Compatible** |
| Task-Based Management | ❌ | ✅ | **Unique** |
| Color-Consistent Labeling | ❌ | ✅ | **Innovative** |
| Metadata Preservation | ❌ | ✅ | **KDPII Specific** |
| Team Collaboration | ❌ | ✅ | **Professional** |
| Overlapping Annotations | ❌ | ✅ | **Advanced** |
| Entity Relationship Linking | ❌ | ✅ | **Unique** |
| Korean Localization | ❌ | ✅ | **Accessibility** |
| Workspace Management | ❌ | ✅ | **Enterprise** |

## 🧪 Testing

```bash
# Start the application
python3 app.py

# Test file upload with sample data
# Upload sample JSONL files via web interface at http://localhost:8080/ner
# Test complete export functionality

# Test collaboration features
# Create workspace at http://localhost:8080/collaborate

# Test API endpoints
curl -X GET http://localhost:8080/api/ner/config
curl -X POST http://localhost:8080/api/ner/tasks -d '{"text":"Test annotation"}'
```

## 📋 Requirements

- Python 3.8+
- Flask 2.3+
- Flask-SQLAlchemy
- Flask-Login
- Modern web browser (Chrome, Firefox, Safari)
- JavaScript enabled

## 🔧 Key Technical Features

### File Processing Engine
- **JSONL Parser** - Standardized JSONL file processing with complete metadata preservation
- **Metadata Extraction** - Preserves original file structure and metadata with perfect fidelity
- **Entity Auto-detection** - Automatic entity type extraction from files
- **Color Assignment** - Fixed color mapping per label during upload

### Task Management System
- **Individual Task Isolation** - Each text becomes independent annotation task
- **Label Scoping** - Task-specific labels with color consistency
- **Sidebar Navigation** - Collapsible task browser with file information
- **State Persistence** - Maintains task state and annotation progress

### Team Collaboration Framework
- **Workspace Management** - Multi-user collaborative annotation spaces
- **Member Role System** - Annotator identification and attribution
- **Real-time Updates** - Live collaboration with conflict resolution
- **Annotation Merging** - Multiple annotation strategy support

### Advanced UI Architecture
- **Responsive Design** - Adaptive interface for various screen sizes
- **Interactive Elements** - Drag-and-drop, modal dialogs, dynamic forms
- **Data Visualization** - Real-time metadata and annotation display
- **Performance Optimization** - Efficient DOM manipulation and rendering

## 🤝 Contributing

1. **Issue Reporting**: Use GitHub issues to report bugs or request features
2. **Feature Development**: Focus on KDPII compliance and privacy-focused features  
3. **Code Quality**: Follow existing code patterns and include appropriate tests
4. **Documentation**: Update README and docs for any new features
5. **Collaboration**: Contributions welcome for enhanced team collaboration features

## 📄 License

Open source project for KDPII data processing and privacy compliance.

## 🔄 Version History

- **v3.3.0**: Complete export system with JSONL standardization, Korean localization, original structure preservation
- **v3.2.0**: Core annotation fixes, ID conflict resolution, statistics accuracy, navigation enhancements
- **v3.1.0**: File upload processing, task management, color-consistent labeling, metadata preservation
- **v3.0.0**: Complete code integration and optimization with team collaboration
- **v2.0.0**: Advanced NER features with enterprise architecture
- **v1.0**: Basic NER annotation interface

---

**Made with ❤️ for KDPII Data Privacy**

*Advanced NER annotation tool with file processing, team collaboration, and metadata preservation*