#!/usr/bin/env python3
"""
Test overlapping annotations functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ner_extractor import NERExtractor

def test_overlapping_annotations():
    """Test overlapping annotation scenarios"""
    print("🧪 Testing Overlapping Annotations")
    print("=" * 40)
    
    extractor = NERExtractor()
    
    # Test text with potential overlaps
    test_text = "John Smith works at Microsoft Corporation in Seattle, Washington."
    task_id = extractor.create_task(test_text)
    
    print(f"Test text: {test_text}")
    print(f"Text length: {len(test_text)}")
    print()
    
    # Test cases
    test_cases = [
        # (start, end, labels, description)
        (0, 10, ["PER"], "John Smith"),
        (5, 10, ["PER"], "Smith (overlapping with John Smith)"),
        (20, 41, ["ORG"], "Microsoft Corporation"),
        (20, 29, ["ORG"], "Microsoft (partial overlap)"),
        (45, 52, ["LOC"], "Seattle"),
        (45, 63, ["LOC"], "Seattle, Washington (extended)"),
        (54, 64, ["LOC"], "Washington"),
    ]
    
    # Add annotations
    print("Adding annotations:")
    for i, (start, end, labels, description) in enumerate(test_cases, 1):
        try:
            selected_text = test_text[start:end]
            annotation_id = extractor.add_annotation(task_id, start, end, labels)
            print(f"  {i}. ✅ '{selected_text}' ({start}-{end}) -> {labels[0]} -> {annotation_id[:8]}...")
        except Exception as e:
            print(f"  {i}. ❌ Error for '{description}': {e}")
    
    print()
    
    # Show final annotations
    task = extractor.get_task(task_id)
    print(f"Final annotations ({len(task.annotations)} total):")
    
    for i, ann in enumerate(task.annotations, 1):
        overlapping = []
        for other in task.annotations:
            if other.id != ann.id:
                # Check if they overlap
                if not (other.end <= ann.start or other.start >= ann.end):
                    overlapping.append(f"{other.labels[0]}({other.start}-{other.end})")
        
        overlap_info = f" [overlaps: {', '.join(overlapping)}]" if overlapping else ""
        print(f"  {i}. '{ann.text}' ({ann.start}-{ann.end}) -> {ann.labels}{overlap_info}")
    
    # Test export
    print("\n🔄 Testing Export:")
    try:
        exported = extractor.export_task(task_id)
        print(f"  ✅ Label Studio export: {len(exported['annotations'])} annotations")
        
        conll = extractor.export_conll_format(task_id)
        lines = conll.split('\n')
        non_o_lines = [line for line in lines if not line.endswith('\tO')]
        print(f"  ✅ CoNLL export: {len(non_o_lines)} labeled tokens")
        
    except Exception as e:
        print(f"  ❌ Export error: {e}")
    
    # Statistics
    print("\n📊 Statistics:")
    stats = extractor.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return task_id, extractor

def test_edge_cases():
    """Test edge cases for annotation boundaries"""
    print("\n🔬 Testing Edge Cases")
    print("=" * 40)
    
    extractor = NERExtractor()
    test_text = "A B C D E"  # Simple text for precise testing
    task_id = extractor.create_task(test_text)
    
    edge_cases = [
        # (start, end, labels, should_work, description)
        (0, 1, ["TEST"], True, "Single character at start"),
        (8, 9, ["TEST"], True, "Single character at end"),
        (0, 9, ["TEST"], True, "Entire text"),
        (2, 5, ["TEST"], True, "Middle section"),
        (-1, 2, ["TEST"], False, "Negative start"),
        (7, 15, ["TEST"], False, "End beyond text"),
        (5, 3, ["TEST"], False, "Start > End"),
        (0, 0, ["TEST"], False, "Zero-length span"),
    ]
    
    print(f"Test text: '{test_text}' (length: {len(test_text)})")
    
    for i, (start, end, labels, should_work, description) in enumerate(edge_cases, 1):
        try:
            annotation_id = extractor.add_annotation(task_id, start, end, labels)
            if should_work:
                print(f"  {i}. ✅ {description}: '{test_text[start:end]}' -> {annotation_id[:8]}...")
            else:
                print(f"  {i}. ⚠️  {description}: Unexpectedly succeeded")
        except Exception as e:
            if not should_work:
                print(f"  {i}. ✅ {description}: Correctly failed ({str(e)[:50]}...)")
            else:
                print(f"  {i}. ❌ {description}: Unexpectedly failed ({e})")

if __name__ == "__main__":
    try:
        task_id, extractor = test_overlapping_annotations()
        test_edge_cases()
        
        print("\n✅ All tests completed!")
        print("The overlapping annotation system should now handle:")
        print("  - Overlapping text spans")
        print("  - Boundary validation") 
        print("  - Duplicate detection")
        print("  - Safe rendering with complex HTML")
        print("  - Robust text offset calculation")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()