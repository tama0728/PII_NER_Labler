#!/usr/bin/env python3
"""
KDPII NER Labeler Test Runner
============================

Comprehensive test runner for the KDPII NER Labeler system.
Executes all test suites with proper configuration and reporting.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --e2e              # Run only end-to-end tests
    python run_tests.py --performance      # Run only performance tests
    python run_tests.py --quick            # Run quick tests only
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --verbose          # Verbose output
    python run_tests.py --help             # Show help

Features:
- Organized test execution by category
- Coverage reporting
- Performance benchmarking
- Parallel test execution
- Custom reporting formats
"""

import sys
import os
import argparse
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Main test runner class for KDPII NER Labeler."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent  # Go up to project root
        self.test_suite_dir = Path(__file__).parent.parent  # test-suite directory
        self.tests_dir = self.test_suite_dir / 'tests'
        self.config_dir = self.test_suite_dir / 'config'
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def setup_environment(self):
        """Setup test environment and validate dependencies."""
        print("🔧 Setting up test environment...")
        
        # Add project root to Python path
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
        
        # Check if pytest is available
        try:
            import pytest
            print(f"✅ pytest {pytest.__version__} available")
        except ImportError:
            print("❌ pytest not available. Install with: pip install pytest")
            return False
        
        # Check if tests directory exists
        if not self.tests_dir.exists():
            print(f"❌ Tests directory not found: {self.tests_dir}")
            return False
        
        print(f"✅ Tests directory found: {self.tests_dir}")
        
        # Validate test files
        test_files = list(self.tests_dir.glob('test_*.py'))
        print(f"✅ Found {len(test_files)} test files")
        
        return True
    
    def run_test_suite(self, test_pattern=None, markers=None, extra_args=None):
        """Run specific test suite with given parameters."""
        cmd = ['python3', '-m', 'pytest', '-c', str(self.config_dir / 'pytest.ini')]
        
        # Add test path
        if test_pattern:
            cmd.append(str(self.tests_dir / test_pattern))
        else:
            cmd.append(str(self.tests_dir))
        
        # Add markers
        if markers:
            if isinstance(markers, str):
                markers = [markers]
            for marker in markers:
                cmd.extend(['-m', marker])
        
        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        # Default arguments for better output
        default_args = [
            '-v',  # Verbose
            '--tb=short',  # Short traceback format
            '--color=yes',  # Colored output
            '--durations=10',  # Show slowest 10 tests
        ]
        cmd.extend(default_args)
        
        print(f"🏃 Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }
    
    def run_unit_tests(self):
        """Run unit tests only."""
        print("\n📋 Running Unit Tests...")
        print("=" * 50)
        
        unit_tests = [
            'unit/test_ner_core.py',
            'unit/test_database.py'
        ]
        
        results = {}
        for test_file in unit_tests:
            if (self.tests_dir / test_file).exists():
                print(f"\n🧪 Running {test_file}...")
                result = self.run_test_suite(test_file)
                results[test_file] = result
                
                if result['success']:
                    print(f"✅ {test_file} passed")
                else:
                    print(f"❌ {test_file} failed")
                    print(f"Error: {result['stderr'][:200]}...")
            else:
                print(f"⚠️  {test_file} not found, skipping")
        
        return results
    
    def run_integration_tests(self):
        """Run integration tests."""
        print("\n🔗 Running Integration Tests...")
        print("=" * 50)
        
        integration_tests = [
            'integration/test_flask_api.py',
            'integration/test_backend_services.py',
            'integration/test_integration.py',
            'integration/test_overlapping_annotations.py'
        ]
        
        results = {}
        for test_file in integration_tests:
            if (self.tests_dir / test_file).exists():
                print(f"\n🧪 Running {test_file}...")
                result = self.run_test_suite(test_file)
                results[test_file] = result
                
                if result['success']:
                    print(f"✅ {test_file} passed")
                else:
                    print(f"❌ {test_file} failed")
                    print(f"Error: {result['stderr'][:200]}...")
            else:
                print(f"⚠️  {test_file} not found, skipping")
        
        return results
    
    def run_frontend_tests(self):
        """Run frontend tests."""
        print("\n🎨 Running Frontend Tests...")
        print("=" * 50)
        
        frontend_test = 'frontend/test_frontend.py'
        
        if (self.tests_dir / frontend_test).exists():
            print(f"\n🧪 Running {frontend_test}...")
            result = self.run_test_suite(frontend_test)
            
            if result['success']:
                print(f"✅ {frontend_test} passed")
            else:
                print(f"❌ {frontend_test} failed")
                print(f"Error: {result['stderr'][:200]}...")
            
            return {frontend_test: result}
        else:
            print(f"⚠️  {frontend_test} not found, skipping")
            return {}
    
    def run_e2e_tests(self):
        """Run end-to-end tests."""
        print("\n🌍 Running End-to-End Tests...")
        print("=" * 50)
        
        e2e_test = 'e2e/test_end_to_end.py'
        
        if (self.tests_dir / e2e_test).exists():
            print(f"\n🧪 Running {e2e_test}...")
            # E2E tests might take longer, add timeout
            extra_args = ['--timeout=600']
            result = self.run_test_suite(e2e_test, extra_args=extra_args)
            
            if result['success']:
                print(f"✅ {e2e_test} passed")
            else:
                print(f"❌ {e2e_test} failed")
                print(f"Error: {result['stderr'][:200]}...")
            
            return {e2e_test: result}
        else:
            print(f"⚠️  {e2e_test} not found, skipping")
            return {}
    
    def run_performance_tests(self):
        """Run performance tests."""
        print("\n⚡ Running Performance Tests...")
        print("=" * 50)
        
        # Run tests marked as performance
        result = self.run_test_suite(markers=['performance'])
        
        if result['success']:
            print("✅ Performance tests passed")
        else:
            print("❌ Performance tests failed")
            print(f"Error: {result['stderr'][:200]}...")
        
        return {'performance': result}
    
    def run_with_coverage(self):
        """Run tests with coverage reporting."""
        print("\n📊 Running Tests with Coverage...")
        print("=" * 50)
        
        coverage_args = [
            '--cov=.',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-report=xml',
            '--cov-branch'
        ]
        
        result = self.run_test_suite(extra_args=coverage_args)
        
        if result['success']:
            print("✅ Coverage tests completed")
            print("📁 Coverage report generated in 'htmlcov/' directory")
        else:
            print("❌ Coverage tests failed")
            print(f"Error: {result['stderr'][:200]}...")
        
        return {'coverage': result}
    
    def run_quick_tests(self):
        """Run only quick tests (excluding slow and e2e)."""
        print("\n⚡ Running Quick Tests...")
        print("=" * 50)
        
        # Run tests but exclude slow and e2e markers
        quick_args = ['-m', 'not slow and not e2e']
        result = self.run_test_suite(extra_args=quick_args)
        
        if result['success']:
            print("✅ Quick tests passed")
        else:
            print("❌ Quick tests failed")
            print(f"Error: {result['stderr'][:200]}...")
        
        return {'quick': result}
    
    def run_all_tests(self):
        """Run all test suites."""
        print("\n🚀 Running All Tests...")
        print("=" * 50)
        
        all_results = {}
        
        # Run each test category
        all_results.update(self.run_unit_tests())
        all_results.update(self.run_integration_tests())
        all_results.update(self.run_frontend_tests())
        all_results.update(self.run_e2e_tests())
        
        return all_results
    
    def generate_report(self, results):
        """Generate comprehensive test report."""
        print("\n📋 Test Execution Report")
        print("=" * 50)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Summary:")
        print(f"   Total Test Suites: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            print(f"   ⏱️  Duration: {duration:.2f} seconds")
        
        print(f"\n📄 Detailed Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {status} {test_name}")
            if not result['success'] and result['stderr']:
                # Show first line of error
                error_line = result['stderr'].split('\n')[0]
                print(f"      └─ {error_line[:80]}...")
        
        # Save detailed report to file
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'duration': duration if self.start_time and self.end_time else None
            },
            'results': {
                name: {
                    'success': result['success'],
                    'returncode': result['returncode'],
                    'stderr': result['stderr'][:500] if result['stderr'] else None
                }
                for name, result in results.items()
            }
        }
        
        report_file = self.project_root / 'test_report.json'
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📁 Detailed report saved to: {report_file}")
        
        return passed_tests == total_tests


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description='KDPII NER Labeler Test Runner')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--frontend', action='store_true', help='Run only frontend tests')
    parser.add_argument('--e2e', action='store_true', help='Run only end-to-end tests')
    parser.add_argument('--performance', action='store_true', help='Run only performance tests')
    parser.add_argument('--quick', action='store_true', help='Run only quick tests')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage reporting')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("🧪 KDPII NER Labeler Test Suite")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    runner = TestRunner()
    
    # Setup environment
    if not runner.setup_environment():
        print("❌ Environment setup failed. Exiting.")
        sys.exit(1)
    
    runner.start_time = time.time()
    
    try:
        # Determine which tests to run
        if args.unit:
            results = runner.run_unit_tests()
        elif args.integration:
            results = runner.run_integration_tests()
        elif args.frontend:
            results = runner.run_frontend_tests()
        elif args.e2e:
            results = runner.run_e2e_tests()
        elif args.performance:
            results = runner.run_performance_tests()
        elif args.quick:
            results = runner.run_quick_tests()
        elif args.coverage:
            results = runner.run_with_coverage()
        else:
            # Run all tests by default
            results = runner.run_all_tests()
        
        runner.end_time = time.time()
        
        # Generate report
        success = runner.generate_report(results)
        
        if success:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()