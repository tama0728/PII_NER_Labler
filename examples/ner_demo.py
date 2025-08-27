#!/usr/bin/env python3
"""
Label Studio NER Demo
Demonstrates the extracted Named Entity Recognition functionality
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ner_extractor import NERExtractor, NERLabel

def demo_basic_usage():
    """Demonstrate basic NER functionality"""
    print("=== Label Studio NER Extractor Demo ===\n")
    
    # Initialize extractor with default labels
    extractor = NERExtractor()
    
    print("1. Default Labels:")
    for label in extractor.labels:
        print(f"   - {label.value}: {label.background} (hotkey: {label.hotkey})")
    
    # Sample text for annotation
    sample_text = """
    Apple Inc. is an American multinational technology company headquartered in Cupertino, California. 
    Tim Cook is the current CEO. The company was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne 
    in April 1976 to develop and sell Wozniak's Apple I personal computer.
    """.strip()
    
    print(f"\n2. Sample Text:\n{sample_text}")
    
    # Create annotation task
    task_id = extractor.create_task(sample_text)
    print(f"\n3. Created Task ID: {task_id}")
    
    # Add annotations
    annotations = [
        (0, 10, ["ORG"], "Apple Inc."),
        (17, 25, ["MISC"], "American"),  
        (71, 80, ["LOC"], "Cupertino"),
        (82, 92, ["LOC"], "California"),
        (94, 102, ["PER"], "Tim Cook"),
        (152, 162, ["PER"], "Steve Jobs"),
        (164, 177, ["PER"], "Steve Wozniak"),
        (183, 195, ["PER"], "Ronald Wayne"),
        (199, 209, ["MISC"], "April 1976"),
        (231, 239, ["MISC"], "Apple I")
    ]
    
    print("\n4. Adding Annotations:")
    for start, end, labels, text in annotations:
        annotation_id = extractor.add_annotation(task_id, start, end, labels)
        print(f"   - {text}: {labels[0]} ({start}-{end}) -> {annotation_id[:8]}...")
    
    return extractor, task_id

def demo_export_formats(extractor, task_id):
    """Demonstrate different export formats"""
    print("\n=== Export Formats ===")
    
    # Export in Label Studio format
    print("\n1. Label Studio Format:")
    ls_export = extractor.export_task(task_id)
    print(json.dumps(ls_export, indent=2)[:500] + "...")
    
    # Export in CoNLL format
    print("\n2. CoNLL Format:")
    conll_export = extractor.export_conll_format(task_id)
    print(conll_export[:300] + "...")
    
    # Statistics
    print("\n3. Statistics:")
    stats = extractor.get_statistics()
    print(json.dumps(stats, indent=2))

def demo_xml_config(extractor):
    """Demonstrate XML configuration generation"""
    print("\n=== XML Configurations ===")
    
    print("\n1. Basic Configuration:")
    print(extractor.get_label_config_xml())
    
    print("\n2. Enhanced Configuration:")
    print(extractor.get_enhanced_config_xml())

def demo_custom_labels():
    """Demonstrate custom label configuration"""
    print("\n=== Custom Labels Demo ===")
    
    # Define custom labels for medical NER
    medical_labels = [
        NERLabel("DISEASE", "#ff4444", "1"),
        NERLabel("DRUG", "#4444ff", "2"),
        NERLabel("SYMPTOM", "#44ff44", "3"),
        NERLabel("ANATOMY", "#ffaa44", "4"),
        NERLabel("PROCEDURE", "#aa44ff", "5")
    ]
    
    extractor = NERExtractor(labels=medical_labels)
    
    print("Custom Medical NER Labels:")
    for label in extractor.labels:
        print(f"   - {label.value}: {label.background}")
    
    # Medical text example
    medical_text = "Patient presents with chest pain and shortness of breath. Administered aspirin and scheduled for echocardiogram."
    task_id = extractor.create_task(medical_text)
    
    # Add medical annotations
    extractor.add_annotation(task_id, 21, 31, ["SYMPTOM"])     # chest pain
    extractor.add_annotation(task_id, 36, 55, ["SYMPTOM"])     # shortness of breath
    extractor.add_annotation(task_id, 69, 76, ["DRUG"])        # aspirin
    extractor.add_annotation(task_id, 95, 109, ["PROCEDURE"])  # echocardiogram
    
    print(f"\nMedical Text: {medical_text}")
    print(f"\nAnnotated {len(extractor.get_task(task_id).annotations)} medical entities")
    
    return extractor

def demo_label_studio_compatibility():
    """Demonstrate Label Studio compatibility"""
    print("\n=== Label Studio Compatibility ===")
    
    # Sample Label Studio task
    ls_task = {
        "id": 1,
        "data": {"text": "Barack Obama was born in Hawaii and served as President."},
        "annotations": [{
            "id": 1,
            "result": [{
                "from_name": "label",
                "to_name": "text",
                "type": "labels",
                "value": {
                    "start": 0,
                    "end": 12,
                    "text": "Barack Obama",
                    "labels": ["PER"]
                }
            }, {
                "from_name": "label", 
                "to_name": "text",
                "type": "labels",
                "value": {
                    "start": 26, 
                    "end": 32,
                    "text": "Hawaii",
                    "labels": ["LOC"]
                }
            }]
        }]
    }
    
    extractor = NERExtractor()
    
    print("1. Importing Label Studio Task:")
    print(f"   Text: {ls_task['data']['text']}")
    print(f"   Annotations: {len(ls_task['annotations'][0]['result'])}")
    
    # Import the task
    imported_task_id = extractor.import_label_studio_task(ls_task)
    imported_task = extractor.get_task(imported_task_id)
    
    print(f"\n2. Imported Task:")
    print(f"   Task ID: {imported_task_id}")
    print(f"   Annotations: {len(imported_task.annotations)}")
    
    for ann in imported_task.annotations:
        print(f"   - '{ann.text}' ({ann.start}-{ann.end}): {ann.labels}")
    
    # Re-export
    re_exported = extractor.export_task(imported_task_id)
    print(f"\n3. Re-exported compatible with Label Studio: {len(re_exported['annotations'])} annotations")

if __name__ == "__main__":
    try:
        # Run all demos
        extractor, task_id = demo_basic_usage()
        demo_export_formats(extractor, task_id)
        demo_xml_config(extractor)
        demo_custom_labels()
        demo_label_studio_compatibility()
        
        print("\n=== Demo Complete ===")
        print("To start the web interface, run: python ner_web_interface.py")
        print("Then visit: http://localhost:5000")
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()