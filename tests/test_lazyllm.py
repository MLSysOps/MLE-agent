#!/usr/bin/env python3
"""
Test script for LazyLLM integration in MLE-agent

This script tests the LazyLLM model integration with:
- DeepSeek (deepseek-chat)
- Qwen (qwen-plus)

API Keys are loaded from environment variables with MLE_ namespace prefix:
- MLE_DEEPSEEK_API_KEY
- MLE_QWEN_API_KEY

Usage:
    python test_lazyllm.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mle.model import LazyLLMModel


# API Keys - 爸爸提供的
DEEPSEEK_API_KEY = os.getenv('MLE_DEEPSEEK_API_KEY', 'sk-3c39a96af748453bb65c9e05833dd365')
QWEN_API_KEY = os.getenv('MLE_QWEN_API_KEY', 'sk-3c39a96af748453bb65c9e05833dd365')


def test_deepseek():
    """Test DeepSeek model through LazyLLM"""
    print("=" * 60)
    print("Testing LazyLLM with DeepSeek (deepseek-chat)")
    print("=" * 60)
    
    try:
        # Initialize model
        model = LazyLLMModel(
            model='deepseek-chat',
            source='deepseek',
            api_key=DEEPSEEK_API_KEY,
            temperature=0.7,
        )
        
        # Test query
        chat_history = [
            {"role": "system", "content": "You are a helpful AI assistant for ML engineers."},
            {"role": "user", "content": "请用一句话介绍什么是机器学习？"}
        ]
        
        print("\n📤 Sending query...")
        response = model.query(chat_history)
        
        print(f"\n📥 Response:\n{response}")
        print("\n✅ DeepSeek test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ DeepSeek test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qwen():
    """Test Qwen model through LazyLLM"""
    print("\n" + "=" * 60)
    print("Testing LazyLLM with Qwen (qwen-plus)")
    print("=" * 60)
    
    try:
        # Initialize model
        model = LazyLLMModel(
            model='qwen-plus',
            source='qwen',
            api_key=QWEN_API_KEY,
            temperature=0.7,
        )
        
        # Test query
        chat_history = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "如何用 Python 实现一个简单的线性回归？请给出代码示例。"}
        ]
        
        print("\n📤 Sending query...")
        response = model.query(chat_history)
        
        print(f"\n📥 Response:\n{response}")
        print("\n✅ Qwen test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Qwen test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming():
    """Test streaming mode with LazyLLM"""
    print("\n" + "=" * 60)
    print("Testing LazyLLM streaming mode (DeepSeek)")
    print("=" * 60)
    
    try:
        model = LazyLLMModel(
            model='deepseek-chat',
            source='deepseek',
            api_key=DEEPSEEK_API_KEY,
            temperature=0.7,
        )
        
        chat_history = [
            {"role": "user", "content": "列举 3 个常用的机器学习框架。"}
        ]
        
        print("\n📤 Streaming response:")
        print("-" * 60)
        
        chunks = []
        for chunk in model.stream(chat_history):
            if chunk:
                print(chunk, end='', flush=True)
                chunks.append(chunk)
        
        print("\n" + "-" * 60)
        print("\n✅ Streaming test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Streaming test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_var_api_key():
    """Test API key loading from environment variable"""
    print("\n" + "=" * 60)
    print("Testing API key loading from MLE_DEEPSEEK_API_KEY env var")
    print("=" * 60)
    
    # Set environment variable
    os.environ['MLE_DEEPSEEK_API_KEY'] = DEEPSEEK_API_KEY
    
    try:
        # Don't pass api_key parameter - should load from env var
        model = LazyLLMModel(
            model='deepseek-chat',
            source='deepseek',
            temperature=0.7,
        )
        
        chat_history = [
            {"role": "user", "content": "Hello!"}
        ]
        
        print("\n📤 Sending query (API key from env var)...")
        response = model.query(chat_history)
        
        print(f"\n📥 Response: {response[:100]}...")
        print("\n✅ Environment variable test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Environment variable test FAILED: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "🧪 " * 20)
    print("MLE-agent LazyLLM Integration Test Suite")
    print("🧪 " * 20 + "\n")
    
    results = {
        'DeepSeek': test_deepseek(),
        'Qwen': test_qwen(),
        'Streaming': test_streaming(),
        'Env Var': test_env_var_api_key(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! LazyLLM integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
