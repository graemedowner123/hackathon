#!/usr/bin/env python3
"""
Test Runner for P2P Lending Platform
Executes all test suites and provides comprehensive reporting
"""

import sys
import os
import time
import subprocess
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_test_file(test_file, description):
    """Run a specific test file and return results"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the test file
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True, 
                              cwd=os.path.dirname(os.path.abspath(__file__)))
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        
        return {
            'name': description,
            'file': test_file,
            'success': success,
            'duration': duration,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"❌ Error running {test_file}: {e}")
        
        return {
            'name': description,
            'file': test_file,
            'success': False,
            'duration': duration,
            'return_code': -1,
            'error': str(e)
        }

def extract_test_stats(output):
    """Extract test statistics from output"""
    stats = {
        'tests_run': 0,
        'failures': 0,
        'errors': 0,
        'skipped': 0,
        'success_rate': 0
    }
    
    if not output:
        return stats
    
    lines = output.split('\n')
    
    for line in lines:
        if 'Tests Run:' in line:
            try:
                stats['tests_run'] = int(line.split('Tests Run:')[1].strip())
            except:
                pass
        elif 'Failures:' in line:
            try:
                stats['failures'] = int(line.split('Failures:')[1].strip())
            except:
                pass
        elif 'Errors:' in line:
            try:
                stats['errors'] = int(line.split('Errors:')[1].strip())
            except:
                pass
        elif 'Skipped:' in line:
            try:
                stats['skipped'] = int(line.split('Skipped:')[1].strip())
            except:
                pass
        elif 'Success Rate:' in line:
            try:
                rate_str = line.split('Success Rate:')[1].strip().replace('%', '')
                stats['success_rate'] = float(rate_str)
            except:
                pass
    
    return stats

def generate_test_report(results):
    """Generate comprehensive test report"""
    
    print(f"\n{'='*80}")
    print(f"📊 COMPREHENSIVE TEST REPORT")
    print(f"{'='*80}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    total_duration = sum(r['duration'] for r in results)
    successful_suites = sum(1 for r in results if r['success'])
    
    # Overall summary
    print(f"\n🎯 OVERALL SUMMARY")
    print(f"{'─'*40}")
    print(f"Test Suites Run: {len(results)}")
    print(f"Successful Suites: {successful_suites}")
    print(f"Failed Suites: {len(results) - successful_suites}")
    print(f"Total Duration: {total_duration:.2f} seconds")
    print(f"Overall Success Rate: {(successful_suites/len(results)*100):.1f}%")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS")
    print(f"{'─'*80}")
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"\n{status} {result['name']}")
        print(f"   File: {result['file']}")
        print(f"   Duration: {result['duration']:.2f}s")
        print(f"   Return Code: {result['return_code']}")
        
        # Extract test statistics
        stats = extract_test_stats(result.get('stdout', ''))
        if stats['tests_run'] > 0:
            print(f"   Tests: {stats['tests_run']} run, {stats['failures']} failed, {stats['errors']} errors, {stats['skipped']} skipped")
            print(f"   Success Rate: {stats['success_rate']:.1f}%")
            
            total_tests += stats['tests_run']
            total_failures += stats['failures']
            total_errors += stats['errors']
            total_skipped += stats['skipped']
        
        if not result['success'] and 'error' in result:
            print(f"   Error: {result['error']}")
    
    # Test statistics summary
    if total_tests > 0:
        print(f"\n📈 TEST STATISTICS")
        print(f"{'─'*40}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_tests - total_failures - total_errors}")
        print(f"Failed: {total_failures}")
        print(f"Errors: {total_errors}")
        print(f"Skipped: {total_skipped}")
        
        overall_success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        print(f"Overall Test Success Rate: {overall_success_rate:.1f}%")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print(f"{'─'*40}")
    
    if successful_suites == len(results):
        print("🎉 All test suites passed! Your system is working correctly.")
        print("✅ Ready for production deployment")
        print("✅ All core functionality verified")
        print("✅ Integration tests successful")
    else:
        failed_suites = [r for r in results if not r['success']]
        print(f"❌ {len(failed_suites)} test suite(s) failed:")
        for failed in failed_suites:
            print(f"   • {failed['name']}")
        
        print("\n🔧 Next Steps:")
        print("1. Review failed test output above")
        print("2. Fix identified issues")
        print("3. Re-run tests to verify fixes")
        print("4. Consider running individual test suites for debugging")
    
    return successful_suites == len(results)

def main():
    """Main test runner function"""
    
    print("🚀 P2P Lending Platform - Complete Test Suite Runner")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define test suites to run
    test_suites = [
        {
            'file': 'verify_fixes.py',
            'description': 'System Verification Tests (No AWS Required)'
        },
        {
            'file': 'unit_tests.py', 
            'description': 'Unit Tests (Core Functionality)'
        },
        {
            'file': 'integration_tests.py',
            'description': 'Integration Tests (End-to-End Workflows)'
        },
        {
            'file': 'test_suite.py',
            'description': 'Comprehensive Test Suite (Full System)'
        }
    ]
    
    # Check which test files exist
    available_tests = []
    for test in test_suites:
        if os.path.exists(test['file']):
            available_tests.append(test)
        else:
            print(f"⚠️  Test file not found: {test['file']}")
    
    if not available_tests:
        print("❌ No test files found!")
        return False
    
    print(f"\n📋 Running {len(available_tests)} test suites...")
    
    # Run all available tests
    results = []
    
    for test in available_tests:
        result = run_test_file(test['file'], test['description'])
        results.append(result)
        
        # Brief status update
        status = "✅" if result['success'] else "❌"
        print(f"\n{status} {test['description']}: {'PASSED' if result['success'] else 'FAILED'} ({result['duration']:.1f}s)")
    
    # Generate comprehensive report
    overall_success = generate_test_report(results)
    
    # Final status
    print(f"\n{'='*80}")
    if overall_success:
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("Your P2P lending platform is ready for production! 🚀")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the issues above and fix them before deployment.")
    print(f"{'='*80}")
    
    return overall_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
